from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "brand" / "Icon.png"
ASSET_DIR = ROOT / "assets" / "generated"
OUTPUT = ASSET_DIR / "icon.ico"
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
PNG_SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Icon source not found: {SOURCE}")
    image = Image.open(SOURCE).convert("RGBA")
    ASSET_DIR.mkdir(exist_ok=True)
    resized_images = []
    for size in PNG_SIZES:
        resized = image.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(ASSET_DIR / f"window_icon_{size}.png")
        resized_images.append(resized)
    image.save(OUTPUT, format="ICO", sizes=SIZES)
    print(f"Generated {OUTPUT} from {SOURCE} ({image.width}x{image.height})")
    print(f"Generated runtime PNG icons in {ASSET_DIR}")


if __name__ == "__main__":
    main()
