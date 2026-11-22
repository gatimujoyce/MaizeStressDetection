"""Counts how many really different photos each Bangladesh class has, and makes a contact sheet to eyeball duplicates.

Prints per class: files, unique file contents (md5), unique 256-bit dHash values, and the duplicate clusters
(photos with exactly the same hash). Writes bd_duplicates_sheet.jpg: one row per cluster (up to 4 per class,
up to 6 photos per row) so the clusters can be checked by eye. Reads only; changes nothing.

  python scripts/check_bd_duplicates.py --bd "<...>\\RAW_Image"
"""
import argparse
import hashlib
import os
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageOps

FOLDERS = ["Common_Rust", "Gray_Leaf_Spot", "Healthy_Leaf", "Corn_Leaf_Blight"]
EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def dhash(img, side=16):
    g = np.asarray(img.convert("L").resize((side + 1, side), Image.LANCZOS), dtype=np.int16)
    return (g[:, 1:] > g[:, :-1]).flatten().tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bd", required=True)
    ap.add_argument("--sheet", default="bd_duplicates_sheet.jpg")
    args = ap.parse_args()

    rows = []
    for folder in FOLDERS:
        files = sorted((f for f in os.listdir(os.path.join(args.bd, folder)) if f.lower().endswith(EXTS)),
                       key=lambda f: int("".join(c for c in f if c.isdigit()) or 0))
        md5s, hashes, sizes = set(), defaultdict(list), defaultdict(int)
        for f in files:
            p = os.path.join(args.bd, folder, f)
            with open(p, "rb") as fh:
                md5s.add(hashlib.md5(fh.read()).hexdigest())
            with Image.open(p) as im:
                sizes[im.size] += 1
                im = ImageOps.exif_transpose(im).convert("RGB")
                hashes[dhash(im)].append(f)
        clusters = sorted((v for v in hashes.values() if len(v) > 1), key=len, reverse=True)
        print(f"\n{folder}: {len(files)} files | {len(md5s)} unique file contents | {len(hashes)} unique hashes | "
              f"{len(clusters)} duplicate clusters")
        print("   image sizes:", dict(sorted(sizes.items(), key=lambda kv: -kv[1])[:4]))
        for c in clusters[:8]:
            print(f"   {len(c):>3} photos: {', '.join(c[:12])}{' ...' if len(c) > 12 else ''}")
        for c in clusters[:4]:
            rows.append((folder, [os.path.join(args.bd, folder, f) for f in c[:6]], c[:6]))

    if rows:
        tw, th, label = 220, 165, 18
        sheet = Image.new("RGB", (tw * 6, (th + label) * len(rows)), "white")
        d = ImageDraw.Draw(sheet)
        for r, (folder, paths, names) in enumerate(rows):
            for k, (p, n) in enumerate(zip(paths, names)):
                with Image.open(p) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    im.thumbnail((tw, th))
                    x, y = k * tw, r * (th + label)
                    sheet.paste(im, (x, y + label))
                    d.text((x + 3, y + 3), f"{folder[:12]} {n}", fill="black")
        sheet.save(args.sheet, quality=85)
        print(f"\nContact sheet: {os.path.abspath(args.sheet)}")


if __name__ == "__main__":
    main()
