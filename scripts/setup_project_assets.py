#!/usr/bin/env python3
"""Prepare independent project assets; clean only this run's owned download cache."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone

EFFECTS = ("fire", "sparkle", "impact", "lightning", "hearts", "steam")
FILES = ("README.md", "manifest.json", "preview.jpg") + tuple(
    f"{effect}/{effect}-alpha-2s.mov" for effect in EFFECTS
)
DEFAULT_SUBDIR = "Footage/Effects/rium-ramen-point-effects"
MANAGER = "rium-shorts-skill-ramen/setup_project_assets.py"
RECEIPT = ".rium-assets-setup.json"
MAX_BYTES = 128 * 1024 * 1024
DOWNLOAD_URL = (
    "https://github.com/contentriumkorea/rium-shorts-skill-ramen/"
    "releases/latest/download/rium-ramen-point-effects.zip"
)


class SetupError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reject_links(path):
    """Inspect unresolved paths too: resolve() alone hides junctions."""
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise SetupError("Symlink paths are not allowed.")
        if part.exists():
            info = part.lstat()
            if getattr(info, "st_file_attributes", 0) & 0x400:
                raise SetupError("Reparse point/junction paths are not allowed.")


def verify_payload(payload):
    if set(payload) != set(FILES) or sum(map(len, payload.values())) > MAX_BYTES:
        raise SetupError("Unexpected asset files or size.")
    manifest = json.loads(payload["manifest.json"])
    entries = manifest.get("effects", [])
    if len(entries) != 6 or {e.get("effect_id") for e in entries} != set(EFFECTS):
        raise SetupError("Expected the six bundled MOV effects.")
    for entry in entries:
        rel = f'{entry["effect_id"]}/{entry["effect_id"]}-alpha-2s.mov'
        if entry.get("alpha_video") != rel or set(entry.get("files", {})) != {rel}:
            raise SetupError("Unexpected manifest asset paths.")
        info = entry["files"][rel]
        if digest(payload[rel]) != info["sha256"] or len(payload[rel]) != info["bytes"]:
            raise SetupError("Asset checksum mismatch.")
    return manifest


def read_bundled(source):
    source = source.absolute()
    reject_links(source)
    payload = {}
    total = 0
    for rel in FILES:
        path = source / rel
        reject_links(path)
        if not path.is_file():
            raise SetupError("Bundled assets are missing or too large.")
        total += path.stat().st_size
        if total > MAX_BYTES:
            raise SetupError("Bundled assets are missing or too large.")
        payload[rel] = path.read_bytes()
    verify_payload(payload)
    return payload


def download_payload(expected_sha256):
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise SetupError("A verified SHA-256 is required with --download.")
    cache = Path(tempfile.mkdtemp(prefix="rium-assets-"))
    reject_links(cache)
    archive = cache / "download.zip"
    try:
        request = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "Rium-assets-setup"})
        with urllib.request.urlopen(request, timeout=30) as response, archive.open("xb") as output:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise SetupError("Download exceeds the size limit.")
                output.write(chunk)
        if digest(archive.read_bytes()) != expected_sha256:
            raise SetupError("Downloaded ZIP checksum mismatch.")
        with zipfile.ZipFile(archive) as bundle:
            infos = bundle.infolist()
            expected = {"rium-ramen-point-effects/" + rel for rel in FILES}
            names = [entry.filename for entry in infos]
            if len(names) != len(expected) or set(names) != expected:
                raise SetupError("ZIP must contain exactly the nine expected files.")
            if sum(entry.file_size for entry in infos) > MAX_BYTES:
                raise SetupError("Uncompressed ZIP exceeds the size limit.")
            for entry in infos:
                mode = entry.external_attr >> 16
                if entry.is_dir() or (stat.S_IFMT(mode) and not stat.S_ISREG(mode)):
                    raise SetupError("ZIP links and non-regular entries are not allowed.")
            # No extractall(): exact validated members are read into bounded memory.
            payload = {rel: bundle.read("rium-ramen-point-effects/" + rel) for rel in FILES}
        verify_payload(payload)
        return payload, (cache, archive, expected_sha256)
    except Exception as error:
        # Preserve failed-run evidence; never sweep temp or Downloads folders.
        raise SetupError(f"Download/setup failed; this run's cache was retained at {cache}. ({type(error).__name__})") from None


def remove_owned_download(owned):
    cache, archive, expected_hash = owned
    reject_links(cache)
    reject_links(archive)
    if archive.parent != cache or archive.name != "download.zip" or not cache.name.startswith("rium-assets-"):
        raise SetupError("Unexpected cache ownership.")
    if set(cache.iterdir()) != {archive} or not archive.is_file():
        raise SetupError("Cache contains unexpected files; cleanup withheld.")
    if archive.stat().st_nlink != 1 or digest(archive.read_bytes()) != expected_hash:
        raise SetupError("Cache changed or is shared; cleanup withheld.")
    archive.unlink()  # Only the ZIP created by download_payload() in this execution.
    cache.rmdir()    # Only if empty; never recursive deletion.


def write_receipt(path, data):
    reject_links(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")
    os.replace(temporary, path)


def prepare_project(project, payload, *, source=None, subdir=DEFAULT_SUBDIR, owned_download=None):
    project = Path(project).absolute()
    reject_links(project)
    if not project.is_dir():
        raise SetupError("The project root must already exist.")
    relative = Path(subdir)
    if relative.is_absolute() or relative.drive or not relative.parts or any(p in {"..", "."} for p in relative.parts):
        raise SetupError("Asset subdirectory must be a non-empty project-relative path.")
    target = project / relative
    reject_links(target)
    if target.resolve() == project.resolve() or not target.resolve().is_relative_to(project.resolve()):
        raise SetupError("Assets must remain inside their project.")
    if source is not None:
        source = Path(source).absolute()
        reject_links(source)
        if target.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(target.resolve()):
            raise SetupError("Destination must be independent of the installed source library.")
    if owned_download and (target.resolve().is_relative_to(owned_download[0].resolve()) or owned_download[0].resolve().is_relative_to(target.resolve())):
        raise SetupError("The download cache cannot be used as a project asset directory.")
    manifest = verify_payload(payload)
    hashes = {rel: digest(data) for rel, data in payload.items()}
    reused = []
    # Preflight every file before changing any existing project.
    for rel in FILES:
        path = target / rel
        reject_links(path)
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise SetupError(f"Existing parent is not a directory; no changes performed: {rel}")
            if parent == project:
                break
        if path.exists():
            if path.stat().st_nlink != 1:
                raise SetupError(f"Existing asset uses shared hard links; preserved without changes: {rel}")
            if not path.is_file() or digest(path.read_bytes()) != hashes[rel]:
                raise SetupError(f"Existing asset differs; no overwrite performed: {rel}")
            reused.append(rel)
    receipt_path = target / RECEIPT
    reject_links(receipt_path)
    prior = None
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        if prior.get("managed_by") != MANAGER or prior.get("asset_subdirectory") != relative.as_posix():
            raise SetupError("Existing receipt is not owned by this setup.")
    target.mkdir(parents=True, exist_ok=True)
    reject_links(target)
    lock = target / ".rium-assets-setup.lock"
    token = uuid.uuid4().hex
    try:
        with lock.open("x", encoding="ascii") as output:
            output.write(token)
    except FileExistsError:
        raise SetupError("Another setup or a retained lock exists; nothing was replaced.") from None
    created = []
    try:
        for rel in FILES:
            path = target / rel
            reject_links(path)
            if path.exists():
                if not path.is_file() or path.stat().st_nlink != 1 or digest(path.read_bytes()) != hashes[rel]:
                    raise SetupError("Destination changed during setup; stopped without overwriting it.")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            reject_links(path.parent)
            # Exclusive creation cannot overwrite another editor's newly created file.
            with path.open("xb") as output:
                output.write(payload[rel])
            created.append(rel)
        for rel in FILES:
            reject_links(target / rel)
            if digest((target / rel).read_bytes()) != hashes[rel]:
                raise SetupError("Final project asset verification failed.")
        receipt = {
            "managed_by": MANAGER, "schema_version": 1,
            "asset_subdirectory": relative.as_posix(), "library_version": manifest.get("version"),
            "files": hashes, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "storage": "independent project files; no shared links created",
            "native_editor_connection": (prior or {}).get("native_editor_connection", "not_verified"),
            "download_cleanup": "pending" if owned_download else "not_needed: bundled source used",
            "cleanup_scope": "only this execution's own downloaded ZIP; project assets and installed library are preserved",
        }
        write_receipt(receipt_path, receipt)
        if owned_download:
            try:
                remove_owned_download(owned_download)
                receipt["download_cleanup"] = "removed: this execution's managed ZIP and empty cache"
            except SetupError:
                receipt["download_cleanup"] = "withheld: cache ownership or contents changed"
                write_receipt(receipt_path, receipt)
                raise
            write_receipt(receipt_path, receipt)
        return {"status": "assets_ready", "asset_directory": str(target), "receipt": str(receipt_path), "created": len(created), "reused": len(reused), "native_editor_connection": "not_verified_by_this_helper", "download_cleanup": receipt["download_cleanup"]}
    finally:
        if lock.is_file() and not lock.is_symlink() and lock.read_text(encoding="ascii") == token:
            lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Existing project root")
    parser.add_argument("--asset-subdir", default=DEFAULT_SUBDIR, help="Project-relative asset directory")
    parser.add_argument("--download", action="store_true", help="Fetch the official asset ZIP into a disposable cache instead of using bundled assets")
    parser.add_argument("--sha256", help="Verified official asset ZIP SHA-256; required with --download")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent / "assets" / "point-effects"
    owned = None
    try:
        project = Path(args.project).absolute()
        reject_links(project)
        if project.resolve().is_relative_to(Path(__file__).resolve().parent.parent):
            raise SetupError("Use a working project outside the installed skill folder.")
        if args.download:
            payload, owned = download_payload((args.sha256 or "").lower())
        else:
            if args.sha256:
                raise SetupError("--sha256 is only used with --download.")
            payload = read_bundled(source)
        result = prepare_project(args.project, payload, source=source, subdir=args.asset_subdir, owned_download=owned)
        print(json.dumps(result, ensure_ascii=False))
    except (SetupError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"status": "incomplete", "error": str(error), "cache_retained": str(owned[0]) if owned and owned[0].exists() else None}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
