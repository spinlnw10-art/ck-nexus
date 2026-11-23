#!/usr/bin/env python3
"""Fail-closed validation and evidence binding for verified OTel image provenance.

Cosign performs cryptographic signature and certificate verification. This helper
checks verified JSON payloads, binds them to one image digest and source candidate,
and emits non-authoritative evidence. It never makes a gate decision.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SLSA_PREFIX = "https://slsa.dev/provenance/"
SLSA_STATUSES = {"VERIFIED", "NOT_PUBLISHED", "VERIFICATION_ERROR"}


class EvidenceError(ValueError):
    """Raised when verified evidence cannot be safely bound to its subject."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate JSON object key")
        result[key] = value
    return result


def load_json(
    path: Path,
    *,
    allowed_root: Path,
    max_bytes: int = 20 * 1024 * 1024,
) -> tuple[Any, bytes]:
    root = allowed_root.resolve(strict=True)
    try:
        info = path.lstat()
    except OSError as exc:
        raise EvidenceError("evidence input cannot be accessed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise EvidenceError("evidence input must be a regular non-symlink file")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EvidenceError("evidence input must remain inside the allowed root") from exc
    if info.st_size == 0 or info.st_size > max_bytes:
        raise EvidenceError("evidence input size is outside the permitted range")
    raw = resolved.read_bytes()
    if len(raw) != info.st_size:
        raise EvidenceError("evidence changed while being read")
    try:
        return json.loads(raw, object_pairs_hook=_unique_object), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("evidence input must be valid UTF-8 JSON") from exc


def _as_entries(document: Any) -> list[dict[str, Any]]:
    entries = document if isinstance(document, list) else [document]
    if not entries or any(not isinstance(item, dict) for item in entries):
        raise EvidenceError("Cosign output must contain JSON objects")
    return entries


def extract_verified_digest(document: Any) -> str:
    """Extract one unambiguous digest from successful cosign verify JSON."""
    found: set[str] = set()
    for entry in _as_entries(document):
        critical = entry.get("critical", entry.get("Critical"))
        if not isinstance(critical, dict):
            continue
        image = critical.get("image", critical.get("Image"))
        if not isinstance(image, dict):
            continue
        digest = image.get("docker-manifest-digest", image.get("Docker-manifest-digest"))
        if isinstance(digest, str) and DIGEST_RE.fullmatch(digest):
            found.add(digest)
    if len(found) != 1:
        raise EvidenceError("Cosign signature output must bind exactly one image digest")
    return next(iter(found))


def _decode_statement(entry: dict[str, Any]) -> dict[str, Any]:
    payload = entry.get("payload")
    if not isinstance(payload, str):
        raise EvidenceError("Cosign attestation entry is missing its payload")
    try:
        decoded = base64.b64decode(payload, validate=True)
        statement = json.loads(decoded, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeDecodeError) as exc:
        raise EvidenceError("Cosign attestation payload is not valid base64 JSON") from exc
    if not isinstance(statement, dict):
        raise EvidenceError("attestation statement must be a JSON object")
    return statement


def _subject_matches_digest(subject: dict[str, Any], expected_digest: str) -> bool:
    digests = subject.get("digest")
    return (
        isinstance(digests, dict)
        and digests.get("sha256") == expected_digest.removeprefix("sha256:")
    )


def verify_slsa_subject(document: Any, expected_digest: str) -> dict[str, Any]:
    """Require a verified SLSA provenance statement whose subject has the image digest."""
    if not DIGEST_RE.fullmatch(expected_digest):
        raise EvidenceError("expected image digest is invalid")
    matched: list[dict[str, Any]] = []
    for entry in _as_entries(document):
        statement = _decode_statement(entry)
        predicate_type = statement.get("predicateType")
        subjects = statement.get("subject")
        if not isinstance(predicate_type, str) or not predicate_type.startswith(SLSA_PREFIX):
            continue
        if not isinstance(subjects, list):
            continue
        for subject in subjects:
            if not isinstance(subject, dict):
                continue
            if _subject_matches_digest(subject, expected_digest):
                matched.append({
                    "predicate_type": predicate_type,
                    "subject_name": subject.get("name", ""),
                })
    if not matched:
        raise EvidenceError("no verified SLSA provenance subject matches the image digest")
    return {
        "matched_attestations": len(matched),
        "predicate_types": sorted({item["predicate_type"] for item in matched}),
        "subject_names": sorted({str(item["subject_name"]) for item in matched}),
    }


def build_report(
    signature_path: Path,
    provenance_path: Path | None,
    *,
    image: str,
    release_tag: str,
    candidate_sha: str,
    slsa_status: str,
    allowed_root: Path,
) -> dict[str, Any]:
    if not COMMIT_RE.fullmatch(candidate_sha):
        raise EvidenceError("candidate SHA must be 40 lowercase hexadecimal characters")
    if not re.fullmatch(r"v\d+\.\d+\.\d+", release_tag):
        raise EvidenceError("release tag must be a stable vX.Y.Z tag")
    if not image.startswith("ghcr.io/open-telemetry/opentelemetry-collector-releases/"):
        raise EvidenceError("image must come from the official OpenTelemetry GHCR namespace")
    if slsa_status not in SLSA_STATUSES:
        raise EvidenceError("SLSA status is invalid")

    signature_doc, signature_raw = load_json(signature_path, allowed_root=allowed_root)
    digest = extract_verified_digest(signature_doc)
    provenance_hash = None
    provenance_summary = {
        "matched_attestations": 0,
        "predicate_types": [],
        "subject_names": [],
    }
    if slsa_status == "VERIFIED":
        if provenance_path is None:
            raise EvidenceError("verified SLSA status requires provenance evidence")
        provenance_doc, provenance_raw = load_json(
            provenance_path, allowed_root=allowed_root
        )
        provenance_summary = verify_slsa_subject(provenance_doc, digest)
        provenance_hash = hashlib.sha256(provenance_raw).hexdigest()
    elif provenance_path is not None:
        raise EvidenceError("unverified SLSA status must not include provenance evidence")

    return {
        "schema": "ck-nexus.q14.otel-image-provenance-evidence.v1",
        "candidate_sha": candidate_sha,
        "release_tag": release_tag,
        "image": image,
        "image_digest": digest,
        "signature_verification": "COSIGN_VERIFIED_BY_WORKFLOW",
        "signature_evidence_sha256": hashlib.sha256(signature_raw).hexdigest(),
        "slsa_provenance_status": slsa_status,
        "provenance_evidence_sha256": provenance_hash,
        **provenance_summary,
        "image_layers_pulled": False,
        "container_started": False,
        "network_accessed": True,
        "production_promotion_eligible": False,
        "gate_decision_made": False,
        "approval_granted": False,
        "authority": "CK-NEXUS_CORE_ONLY",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signature-input", type=Path, required=True)
    parser.add_argument("--provenance-input", type=Path)
    parser.add_argument("--slsa-status", choices=sorted(SLSA_STATUSES), required=True)
    parser.add_argument("--image")
    parser.add_argument("--release-tag")
    parser.add_argument("--candidate-sha")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--extract-digest", action="store_true")
    args = parser.parse_args()
    try:
        allowed_root = Path.cwd().resolve(strict=True)
        signature_doc, _ = load_json(
            args.signature_input, allowed_root=allowed_root
        )
        if args.extract_digest:
            print(extract_verified_digest(signature_doc))
            return
        if not all((args.image, args.release_tag, args.candidate_sha, args.output)):
            parser.error("report mode requires image, release tag, candidate SHA, and output")
        report = build_report(
            args.signature_input,
            args.provenance_input,
            image=args.image,
            release_tag=args.release_tag,
            candidate_sha=args.candidate_sha,
            slsa_status=args.slsa_status,
            allowed_root=allowed_root,
        )
        if args.output.is_symlink():
            raise EvidenceError("output must not be a symlink")
        output_parent = args.output.parent.resolve(strict=False)
        try:
            output_parent.relative_to(allowed_root)
        except ValueError as exc:
            raise EvidenceError("output must remain inside the allowed root") from exc
        output_parent.mkdir(parents=True, exist_ok=True)
        output_path = output_parent / args.output.name
        rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
        with output_path.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    except (EvidenceError, OSError) as exc:
        parser.error(str(exc))
    print("Q14_IMAGE_PROVENANCE_EVIDENCE_RECORDED")


if __name__ == "__main__":
    main()
