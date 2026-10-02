"""Genererer packaging/avm70.ico (samme motiv som web-favicon'et: blå
firkant med tre niveau-søjler). Køres kun når ikonet skal ændres."""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=48, fill=(37, 99, 235, 255))
u = SIZE / 16  # favicon'ets 16x16-gitter
for x, y0, y1 in [(3, 6, 10), (7, 3, 13), (11, 5, 11)]:
    d.rectangle([x * u, y0 * u, (x + 2) * u, y1 * u], fill=(255, 255, 255, 255))
out = Path(__file__).with_name("avm70.ico")
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(out)
