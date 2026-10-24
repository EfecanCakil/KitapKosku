"""Uygulama simgesini (icon.png ve icon.ico) çizer. Kullanım: python tools/make_icon.py"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
S = 1024


def draw() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # zemin: sıcak kahve tonlarında yuvarlak kare
    bg = Image.new("RGBA", (S, S))
    g = ImageDraw.Draw(bg)
    for y in range(S):
        t = y / S
        g.line([(0, y), (S, y)], fill=(int(70 - 25 * t), int(48 - 18 * t), int(32 - 12 * t), 255))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([40, 40, S - 40, S - 40], radius=220, fill=255)
    img.paste(bg, (0, 0), mask)

    # açık kitap
    cx, top, bot = S // 2, 300, 790
    page_l = [(cx, top + 40), (cx - 330, top - 10), (cx - 330, bot - 50), (cx, bot)]
    page_r = [(cx, top + 40), (cx + 330, top - 10), (cx + 330, bot - 50), (cx, bot)]
    d.polygon([(x, y + 26) for x, y in page_l], fill=(120, 60, 30, 255))
    d.polygon([(x, y + 26) for x, y in page_r], fill=(120, 60, 30, 255))
    d.polygon(page_l, fill=(236, 220, 190, 255))
    d.polygon(page_r, fill=(248, 238, 214, 255))
    # satırlar
    for i in range(7):
        y = top + 70 + i * 52
        d.line([(cx - 280, y - 12 + i * 2), (cx - 50, y + 30)], fill=(178, 150, 112, 255), width=12)
        d.line([(cx + 50, y + 30), (cx + 280, y - 12 + i * 2)], fill=(190, 165, 128, 255), width=12)
    # ayraç kurdelesi
    d.polygon([(cx + 150, top - 2), (cx + 205, top - 6), (cx + 205, top + 250), (cx + 178, top + 220), (cx + 150, top + 252)],
              fill=(201, 92, 48, 255))
    return img


if __name__ == "__main__":
    im = draw()
    im.save(ROOT / "icon.png")
    im.save(ROOT / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon.png ve icon.ico yazıldı")
