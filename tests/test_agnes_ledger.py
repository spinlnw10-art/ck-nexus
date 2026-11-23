import pytest

from creator_app.agnes_ledger import AppendOnlyLedger


def test_read_all_is_read_only_for_missing_ledger(tmp_path):
    path = tmp_path / "missing.jsonl"
    ledger = AppendOnlyLedger(path)
    assert ledger.read_all() == []
    assert path.exists() is False


def test_read_all_returns_only_verified_records(tmp_path):
    ledger = AppendOnlyLedger(tmp_path / "ledger.jsonl")
    appended = ledger.append("test_event", {"value": "synthetic"})
    records = ledger.read_all()
    assert records == [appended]
    assert records[0]["event_type"] == "test_event"


def test_read_all_fails_closed_after_tampering(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = AppendOnlyLedger(path)
    ledger.append("test_event", {"value": "synthetic"})
    path.write_text(path.read_text() + '{"tampered":true}\n')
    with pytest.raises(RuntimeError, match="integrity check failed"):
        ledger.read_all()


def _append_worker(path, worker_id, count):
    ledger = AppendOnlyLedger(path)
    for index in range(count):
        ledger.append("parallel_test", {"worker": worker_id, "index": index})
    return count


def test_parallel_threads_preserve_hash_chain(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "parallel.jsonl"
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda worker: _append_worker(path, worker, 12), range(8)))
    ledger = AppendOnlyLedger(path)
    assert sum(results) == 96
    assert ledger.verify().valid is True
    assert ledger.verify().entries == 96
    assert len(ledger.read_all()) == 96


def test_parallel_processes_preserve_hash_chain_when_file_locks_exist(tmp_path):
    from concurrent.futures import ProcessPoolExecutor

    ledger = AppendOnlyLedger(tmp_path / "parallel-process.jsonl")
    if ledger.locking_mode != "fcntl+thread":
        pytest.skip("OS file locks are unavailable on this platform")
    path = str(ledger.path)
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(_append_worker, [path] * 4, range(4), [8] * 4))
    assert sum(results) == 32
    assert ledger.verify().valid is True
    assert ledger.verify().entries == 32
