#!/usr/bin/env python3
"""Create the first catalog entries from MapleSU's existing theme defaults and artwork."""
import io
import json
from pathlib import Path
import secrets
import tempfile
import zipfile

from PIL import Image, ImageDraw
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from theme_market import ROOT, KEY, add, check


def package(document: dict, assets: dict[str, bytes], target: Path) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("theme.json", json.dumps(document, ensure_ascii=False).encode())
        for name, data in assets.items():
            archive.writestr(name, data)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(output.getvalue()) + padder.finalize()
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv)).encryptor()
    target.write_bytes(iv + cipher.update(padded) + cipher.finalize())


def main() -> None:
    art = ROOT.parent / "manager/src/main/res/drawable-nodpi/art_default.jpg"
    with tempfile.TemporaryDirectory(prefix="maplesu-themes-") as temporary:
        work = Path(temporary)
        for comic in (False, True):
            name = "MapleSU Comic" if comic else "MapleSU Default"
            document = dict(meta_name=name, meta_author="MapleSU", meta_version="1", meta_type="phone",
                meta_description="MapleSU 原有动漫卡面，首页排版与设计语言由用户选择。" if comic else "MapleSU 默认配色，保留原有首页排版与设计语言。",
                homeLayoutStyle="kernelsu", nightModeFollowSys=True, useSystemDynamicColor=True,
                isBackgroundEnabled=False, isMusicEnabled=False, isSoundEffectEnabled=False,
                isGridWorkingCardBackgroundEnabled=comic, gridWorkingCardBackgroundOpacity=1.0,
                gridWorkingCardBackgroundDim=0.35, isGridWorkingCardCheckHidden=comic,
                isAdvancedTitleStyleEnabled=False, navIconCustomEnabled=False, navIcons={})
            assets = {"grid_working_card_background.jpg": art.read_bytes()} if comic else {}
            fpt = work / "theme.fpt"
            package(document, assets, fpt)
            if comic:
                with Image.open(art) as original:
                    cover = original.convert("RGB")
                    cover.thumbnail((720, 720))
            else:
                cover = Image.new("RGB", (720, 480), "#dffae4")
                draw = ImageDraw.Draw(cover)
                draw.ellipse((275, 145, 445, 315), outline="#36d167", width=10)
                draw.line((320, 229, 348, 257, 403, 198), fill="#36d167", width=12)
            preview = work / "preview.jpg"
            cover.save(preview, quality=92)
            add(ROOT, "maplesu.comic" if comic else "maplesu.default", fpt, preview,
                "manager/src/main/res/drawable-nodpi/art_default.jpg (existing MapleSU artwork)" if comic else "MapleSU default theme settings; generated checkmark preview",
                "Existing MapleSU asset terms; original source retained" if comic else "GPL-3.0")
    print(json.dumps(dict(themes=len(check(ROOT)), valid=True)))


if __name__ == "__main__":
    main()
