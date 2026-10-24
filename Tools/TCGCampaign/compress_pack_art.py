"""Make the TCG campaign's shop pack art light (995 MB -> about 230 MB), per era.

The campaign ships 3 images per shop pack (326 packs): a 900x800 shop banner (Images/Shop) and a
pack cover in two sizes (Images/CardPack/HighEnd_HD and SD). They were lossless PNGs.

- Banners have no transparency: saved as JPEG. The client loads <name>.jpg when <name>.png is
  missing (YgoMasterClient/AssetHelper.cs), so the .png is removed.
- Covers have see-through edges, so they stay PNG:
  early eras (levels 1-39: DM, GX, 5D's) re-saved losslessly, later eras (levels 40-75: Zexal,
  Arc-V, VRAINS) as 256-colour PNG.
- Banners: early eras JPEG q90 at full size, later eras JPEG q80 at 75% size.
A pack's era comes from the level in its Shop.json name ("55-Core: Crossed Souls" is level 55).

Usage: python -I compress_pack_art.py <source Images folder> <Data folder with Shop.json> <output Images folder>
The source is never changed. Check the output in the game before replacing the installed Images.
"""
import json
import os
import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

from PIL import Image

LATE_LEVEL = 40


def pack_levels(data):
    text = open(os.path.join(data, "Shop.json"), encoding="utf-8-sig").read()
    text = re.sub(r"(?m)^\s*//[^\n]*", "", text)
    shop = json.JSONDecoder(strict=False).decode(re.sub(r",(\s*[}\]])", r"\1", text))
    levels = {}
    for pack in shop["PackShop"].values():
        m = re.match(r"(\d\d)-", pack.get("nameTextId", ""))
        if pack.get("packImage"):
            levels[pack["packImage"]] = int(m.group(1)) if m else 0
    return levels


def convert(job):
    kind, src, dst, late = job
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with Image.open(src) as im:
        im.load()
        if kind == "banner":
            rgb = im.convert("RGB")
            if late:
                rgb = rgb.resize((rgb.width * 3 // 4, rgb.height * 3 // 4), Image.LANCZOS)
            rgb.save(dst, "JPEG", quality=80 if late else 90, optimize=True, progressive=True)
        elif late:
            quantized = im.quantize(colors=256, method=Image.FASTOCTREE, dither=Image.FLOYDSTEINBERG) if im.mode == "RGBA" \
                else im.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
            quantized.save(dst, "PNG", optimize=True)
        else:
            im.save(dst, "PNG", optimize=True, compress_level=9)
            if os.path.getsize(dst) >= os.path.getsize(src):
                shutil.copy2(src, dst)  # never make a file bigger
    return os.path.getsize(src), os.path.getsize(dst)


def main():
    source, data, out = sys.argv[1:4]
    if os.path.abspath(source) == os.path.abspath(out):
        raise SystemExit("Write to a separate output folder.")
    levels = pack_levels(data)
    jobs = []
    for dirpath, _, files in os.walk(source):
        for name in files:
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, source)
            stem, ext = os.path.splitext(name)
            late = levels.get(stem, 0) >= LATE_LEVEL
            if ext.lower() == ".png" and rel.startswith("Shop"):
                jobs.append(("banner", src, os.path.join(out, os.path.splitext(rel)[0] + ".jpg"), late))
            elif ext.lower() == ".png" and rel.startswith("CardPack"):
                jobs.append(("cover", src, os.path.join(out, rel), late))
            else:
                dst = os.path.join(out, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
    before = after = 0
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as pool:
        for b, a in pool.map(convert, jobs, chunksize=8):
            before += b
            after += a
    print("%d pack images: %.0f MB -> %.0f MB" % (len(jobs), before / 1e6, after / 1e6))


if __name__ == "__main__":
    main()
