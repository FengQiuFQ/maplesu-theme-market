#!/usr/bin/env python3
"""Build, validate and stage a FinaSU-compatible static MapleSU theme catalog."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import urllib.parse
import zipfile

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parents[1]
KEY = hashlib.sha256(b"FolkPatchThemeSecretKey2025").digest()
PRIMARY = "https://fengqiufq.github.io/maplesu-theme-market/"
BACKUP = "https://raw.githubusercontent.com/FengQiuFQ/maplesu-theme-market/main/"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def inspect(path: Path) -> dict:
    if not 32 <= path.stat().st_size <= 256 * 1024 * 1024:
        raise ValueError("FPT package must be between 32 bytes and 256 MiB")
    data = path.read_bytes()
    decryptor = Cipher(algorithms.AES(KEY), modes.CBC(data[:16])).decryptor()
    padded = decryptor.update(data[16:]) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    archive = unpadder.update(padded) + unpadder.finalize()
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        entries = package.infolist()
        if not 1 <= len(entries) <= 128 or len({item.filename for item in entries}) != len(entries):
            raise ValueError("Invalid FPT entry count or duplicate resource names")
        if sum(item.file_size for item in entries) > 1024 * 1024 * 1024:
            raise ValueError("FPT resources exceed 1 GiB")
        for item in entries:
            if item.is_dir() or not item.file_size or item.filename in (".", "..", "original.json", "applied.json") or any(
                token in item.filename for token in ("/", "\\", "\0")
            ):
                raise ValueError(f"Invalid FPT resource: {item.filename!r}")
        if package.getinfo("theme.json").file_size > 1024 * 1024:
            raise ValueError("theme.json exceeds 1 MiB")
        document = json.loads(package.read("theme.json"))
        if not isinstance(document, dict):
            raise ValueError("theme.json must be an object")
        bad = package.testzip()
        if bad:
            raise ValueError(f"Corrupt FPT resource: {bad}")
        return document


def static_path(root: Path, value: str) -> Path:
    url = urllib.parse.urlsplit(value)
    if url.scheme or url.netloc or url.query or url.fragment or "\\" in value:
        raise ValueError(f"Expected a relative static path: {value}")
    path = (root / urllib.parse.unquote(url.path)).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError(f"Path leaves catalog: {value}")
    return path


def add(root: Path, identity: str, package: Path, preview: Path, origin: str, license_name: str) -> None:
    document = inspect(package)
    version = str(document.get("meta_version", "1"))
    if not all(re.fullmatch(r"[A-Za-z0-9._-]{1,80}", part) for part in (identity, version)):
        raise ValueError("ID and version must use letters, digits, dots, underscores or hyphens")
    if preview.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise ValueError("Preview must be PNG, JPEG or WebP")
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    # A version identifies immutable bytes, including when a later version is current.
    previous = root / "packages" / identity / version
    if previous.is_dir() and any(p.stem != digest for p in previous.glob("*.fpt")):
        raise ValueError("Theme version already exists with different bytes; increment meta_version")
    # Content hashes retain older releases and prevent mutable version paths.
    relative = f"packages/{identity}/{version}/{digest}.fpt"
    target = static_path(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package, target)
    cover = f"previews/{identity}/{hashlib.sha256(preview.read_bytes()).hexdigest()}{preview.suffix.lower()}"
    cover_path = static_path(root, cover)
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(preview, cover_path)
    entry = dict(id=identity, name=document.get("meta_name", identity), author=document.get("meta_author", ""),
                 version=version, description=document.get("meta_description", ""), type=document.get("meta_type", "phone"),
                 source="official", preview_url=cover, download_url=relative, download_sha256=digest,
                 download_size=package.stat().st_size)
    entries = json.loads((root / "index.json").read_text(encoding="utf-8")) if (root / "index.json").is_file() else []
    entries = [item for item in entries if str(item["id"]) != identity] + [entry]
    write_json(root / "index.json", sorted(entries, key=lambda item: str(item["id"])))
    write_json(root / f"provenance/{identity}/{digest}.json", dict(id=identity, version=version, sha256=digest,
        origin=origin, license=license_name, package=relative))


def check(root: Path) -> list:
    entries = json.loads((root / "index.json").read_text(encoding="utf-8"))
    if not isinstance(entries, list) or len({str(item["id"]) for item in entries}) != len(entries):
        raise ValueError("Catalog must be an array with unique IDs")
    for item in entries:
        package = static_path(root, item["download_url"])
        document = inspect(package)
        if hashlib.sha256(package.read_bytes()).hexdigest() != item["download_sha256"]:
            raise ValueError(f"Package digest mismatch: {item['id']}")
        if package.stat().st_size != item["download_size"] or str(document.get("meta_version", "1")) != item["version"]:
            raise ValueError(f"Package metadata mismatch: {item['id']}")
        if not static_path(root, item["preview_url"]).is_file():
            raise ValueError(f"Missing preview: {item['id']}")
    return entries


def stage(root: Path, destination: Path, primary: str, backup: str) -> None:
    entries = check(root)
    for base in (primary, backup):
        parsed = urllib.parse.urlsplit(base)
        if parsed.scheme != "https" or not parsed.netloc or not base.endswith("/") or parsed.username or parsed.fragment or parsed.query:
            raise ValueError("Mirror bases must be HTTPS directory URLs")
    if destination.exists():
        raise ValueError("Staging destination must be a new directory")
    destination.mkdir(parents=True)
    for item in entries:
        for field in ("download_url", "preview_url"):
            relative = item[field]
            target = static_path(destination, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(static_path(root, relative), target)
            item[field] = urllib.parse.urljoin(primary, relative)
            if field == "download_url":
                item["download_mirrors"] = [urllib.parse.urljoin(backup, relative)]
    write_json(destination / "index.json", entries)
    write_json(destination / "catalog.json", dict(schema_version=1, catalog_id="maplesu-themes",
        format="finasu-fpt-array", published=False, primary=primary, backup=backup,
        index_sha256=hashlib.sha256((destination / "index.json").read_bytes()).hexdigest(), themes=len(entries)))
    (destination / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    add_command = commands.add_parser("add")
    add_command.add_argument("--id", required=True)
    add_command.add_argument("--package", type=Path, required=True)
    add_command.add_argument("--preview", type=Path, required=True)
    add_command.add_argument("--origin", required=True)
    add_command.add_argument("--license", required=True)
    commands.add_parser("check")
    publish = commands.add_parser("stage")
    publish.add_argument("--out", type=Path, required=True)
    publish.add_argument("--primary", default=PRIMARY)
    publish.add_argument("--backup", default=BACKUP)
    args = parser.parse_args()
    if args.command == "add":
        add(args.root, args.id, args.package, args.preview, args.origin, args.license)
    elif args.command == "stage":
        stage(args.root, args.out, args.primary, args.backup)
    else:
        print(json.dumps(dict(themes=len(check(args.root)), valid=True)))


if __name__ == "__main__":
    main()
