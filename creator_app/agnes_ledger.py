from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock, RLock
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is thread-safe only.
    fcntl = None


_THREAD_LOCKS: dict[str, RLock] = {}
_THREAD_LOCKS_GUARD = Lock()


def _thread_lock_for(path: Path) -> RLock:
    key = str(path.resolve())
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, RLock())


@dataclass(frozen=True, slots=True)
class LedgerVerification:
    valid: bool
    entries: int
    last_hash: str | None
    error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "entries": self.entries,
            "last_hash": self.last_hash,
            "error": self.error,
        }


class AppendOnlyLedger:
    """Hash-chained JSONL ledger with thread/process serialization and no delete API."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @property
    def locking_mode(self) -> str:
        return "fcntl+thread" if fcntl is not None else "thread_only"

    @staticmethod
    def _digest(record_without_hash: dict[str, Any]) -> str:
        payload = json.dumps(
            record_without_hash, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @contextmanager
    def _locked_file(self, *, exclusive: bool, create: bool) -> Iterator[Any | None]:
        if not create and not self.path.exists():
            yield None
            return
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        local_lock = _thread_lock_for(self.path)
        local_lock.acquire()
        handle = None
        try:
            handle = self.path.open("a+" if create else "r", encoding="utf-8")
            if fcntl is not None:
                operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
                fcntl.flock(handle.fileno(), operation)
            if create:
                with suppress(OSError):
                    os.chmod(self.path, 0o600)
            yield handle
        finally:
            if handle is not None:
                if fcntl is not None:
                    with suppress(OSError):
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()
            local_lock.release()

    def _verify_handle(self, handle: Any) -> LedgerVerification:
        previous_hash: str | None = None
        count = 0
        try:
            handle.seek(0)
            for count, line in enumerate(handle, start=1):
                record = json.loads(line)
                if not isinstance(record, dict):
                    return LedgerVerification(
                        False, count - 1, previous_hash, "record schema invalid"
                    )
                if record.get("sequence") != count:
                    return LedgerVerification(False, count - 1, previous_hash, "sequence mismatch")
                if record.get("previous_hash") != previous_hash:
                    return LedgerVerification(
                        False, count - 1, previous_hash, "hash chain mismatch"
                    )
                if not isinstance(record.get("payload"), dict) or not isinstance(
                    record.get("event_type"), str
                ):
                    return LedgerVerification(
                        False, count - 1, previous_hash, "record schema invalid"
                    )
                claimed = str(record.get("hash") or "")
                base = {key: value for key, value in record.items() if key != "hash"}
                if not claimed or claimed != self._digest(base):
                    return LedgerVerification(
                        False, count - 1, previous_hash, "record digest mismatch"
                    )
                previous_hash = claimed
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            return LedgerVerification(False, max(count - 1, 0), previous_hash, type(exc).__name__)
        return LedgerVerification(True, count, previous_hash)

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(event_type, str) or not event_type.strip() or len(event_type) > 128:
            raise ValueError("event_type must be non-empty text of at most 128 characters")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        with self._locked_file(exclusive=True, create=True) as handle:
            state = self._verify_handle(handle)
            if not state.valid:
                raise RuntimeError(f"append-only ledger integrity check failed: {state.error}")
            base = {
                "sequence": state.entries + 1,
                "at": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "payload": payload,
                "previous_hash": state.last_hash,
            }
            try:
                record = {**base, "hash": self._digest(base)}
                line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            except (TypeError, ValueError) as exc:
                raise ValueError("ledger payload must contain JSON-compatible values") from exc
            handle.seek(0, os.SEEK_END)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
            return record

    def read_all(self) -> list[dict[str, Any]]:
        """Read verified ledger records without creating or modifying the ledger."""
        with self._locked_file(exclusive=False, create=False) as handle:
            if handle is None:
                return []
            state = self._verify_handle(handle)
            if not state.valid:
                raise RuntimeError(f"append-only ledger integrity check failed: {state.error}")
            try:
                handle.seek(0)
                return [json.loads(line) for line in handle if line.strip()]
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError("append-only ledger read failed") from exc

    def verify(self) -> LedgerVerification:
        with self._locked_file(exclusive=False, create=False) as handle:
            if handle is None:
                return LedgerVerification(True, 0, None)
            return self._verify_handle(handle)
