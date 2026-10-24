"""Seçilen kısa İngilizce klasiklerin Türkçesini önceden hazırlar ve uygulamaya gömer: books/ceviri/<kitap>.json.gz

Kullanım: python tools/pretranslate.py [en-5200 en-43 ...]   (kimlik verilmezse PRESET listesi)
Kaldığı bölümden devam eder; bilgisayarı yormamak için düşük öncelikle ve 4 iş parçacığıyla çalışır.
"""
import ctypes
import gzip
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import mt  # noqa: E402

BOOKS = ROOT / "books"
OUT = BOOKS / "ceviri"
# Kısa, çok okunan, farklı türlerden klasikler (kısadan uzuna)
PRESET = ["en-1952", "en-41", "en-68283", "en-50133", "en-5200", "en-389", "en-43", "en-11", "en-46", "en-35", "en-215",
          "en-600", "en-19942", "en-696", "en-219", "en-2500", "en-209", "en-244", "en-2097", "en-159", "en-64317", "en-5230"]


def save(book_id: str, data: dict):
    tmp = OUT / f"{book_id}.tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    tmp.replace(OUT / f"{book_id}.json.gz")


def main():
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL
    except Exception:  # noqa: BLE001
        pass
    ids = sys.argv[1:] or PRESET
    OUT.mkdir(exist_ok=True)
    tr = mt.Translator(threads=4)
    summary_path = OUT / "_ozet.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    for book_id in ids:
        with gzip.open(BOOKS / f"{book_id}.json.gz", "rt", encoding="utf-8") as fh:
            book = json.load(fh)
        path = OUT / f"{book_id}.json.gz"
        data = json.load(gzip.open(path, "rt", encoding="utf-8")) if path.exists() else {"ch": {}}
        t0, words = time.time(), 0
        for i, ch in enumerate(book["chapters"]):
            e = data["ch"].get(str(i))
            if e and e.get("t") and len(e["p"]) == len(ch["p"]) and None not in e["p"]:
                continue
            marks = [p[:3] if p.startswith(("§§ ", "§_ ")) else "" for p in ch["p"]]
            out = tr.paragraphs([p[len(m):] for p, m in zip(ch["p"], marks)])
            e = {"t": ch["t"] if ch["t"] == "Önsöz" else tr.title(ch["t"]), "p": [m + t for m, t in zip(marks, out)]}
            if ch.get("g"):
                e["g"] = tr.title(ch["g"])
            data["ch"][str(i)] = e
            words += sum(len(p.split()) for p in ch["p"])
            save(book_id, data)
            print(f"{book_id} {i + 1}/{len(book['chapters'])} ({words / max(1, time.time() - t0):.0f} kelime/sn)", flush=True)
        summary[book_id] = 1.0
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        print(f"✓ {book_id} {book['title']} bitti", flush=True)


if __name__ == "__main__":
    main()
