"""Render the published FAA sectional rectangle into a flash-sized AVIF."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
from pathlib import Path
from time import sleep
from urllib.request import urlopen

from PIL import Image

# Public Web Mercator tile coordinates (zoom, west, north, columns, rows).
REGION = (9, 113, 209, 5, 4)
ROOT = "https://tiles.arcgis.com/tiles/ssFJjBXIUyZDrSYZ/arcgis/rest/services/VFR_Sectional/MapServer/tile"
LIMIT = 520 * 1024


def get_tile(cell):
    x, y = cell
    for attempt in range(3):
        try:
            with urlopen(f"{ROOT}/11/{y}/{x}", timeout=30) as response:
                image = Image.open(BytesIO(response.read())).convert("RGB")
            if image.size != (256, 256):
                raise ValueError("Unexpected FAA tile dimensions")
            return x, y, image
        except OSError:
            if attempt == 2:
                raise
            sleep(2 ** attempt)


def main():
    zoom, west, north, cols, rows = REGION
    factor = 2 ** (11 - zoom)
    left, top = west * factor, north * factor
    mosaic = Image.new("RGB", (cols * factor * 256, rows * factor * 256))
    cells = [(x, y) for y in range(top, top + rows * factor)
             for x in range(left, left + cols * factor)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for x, y, image in pool.map(get_tile, cells):
            mosaic.paste(image, ((x - left) * 256, (y - top) * 256))
    # Keep the complete rectangle. Reduce dimensions only if the byte budget
    # cannot support legible detail at the minimum quality.
    for width in (3200, 2880, 2560, 2240):
        image = mosaic.resize((width, width * rows // cols), Image.Resampling.LANCZOS)
        low, high, best = 28, 65, None
        while low <= high:
            quality = (low + high) // 2
            buf = BytesIO()
            image.save(buf, format="AVIF", quality=quality, speed=5, max_threads=4)
            if buf.tell() <= LIMIT:
                best = buf.getvalue()
                low = quality + 1
            else:
                high = quality - 1
        if best:
            break
    else:
        raise ValueError("No complete chart fit the flash budget")
    name = "-".join(map(str, REGION))
    out = Path("dist"); out.mkdir(exist_ok=True)
    (out / f"{name}.avif").write_bytes(best)
    meta = {"bytes":len(best), "sha256":hashlib.sha256(best).hexdigest(),
            "width":image.width, "height":image.height}
    (out / f"{name}.json").write_text(json.dumps(meta)+"\n", encoding="utf-8")
    print(name, meta)


if __name__ == "__main__":
    main()
