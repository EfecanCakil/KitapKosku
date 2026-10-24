"""Kütüphaneyi kurar: telifsiz kitapları indirir, temizler, bölümlere ayırır ve books/ klasörüne sıkıştırılmış olarak yazar.

Kullanım: python tools/build_library.py [--only en-345,omer-seyfettin-tarihi] [--offline]
İndirilen ham dosyalar tools/_cache altında tutulur; ikinci çalıştırmada internete çıkılmaz.
Uygulama yalnızca books/ klasörünü kullanır, okurken internet gerekmez.
"""
import argparse
import gzip
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402

BOOKS = ROOT / "books"
CACHE = Path(__file__).resolve().parent / "_cache"
ORIGINALS = ROOT / "originals"
UA = {"User-Agent": "KitapKosku/1.0 (offline e-book reader; library builder)"}
OFFLINE = False


# ---------- indirme ----------
def _text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").replace("\r\r\n", "\n").replace("\r\n", "\n")


def fetch(url: str, cache_name: str) -> str:
    path = CACHE / cache_name
    if path.exists():
        return _text(path.read_bytes())
    if OFFLINE:
        raise RuntimeError(f"önbellekte yok: {cache_name}")
    last = None
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            time.sleep(1.0 if "wikisource" in url else 0.3)
            return _text(data)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 + 10 * i if "429" in str(e) else 2 + 3 * i)
    raise RuntimeError(f"{url}: {last}")


def ws_api(cache_name: str, **kw) -> dict:
    kw.update(format="json", formatversion="2")
    return json.loads(fetch("https://tr.wikisource.org/w/api.php?" + urllib.parse.urlencode(kw), cache_name))


def slug(s: str) -> str:
    s = s.translate(str.maketrans("ıİşŞğĞçÇöÖüÜâÂîÎûÛ", "iissggccoouuaaiiuu"))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------- Gutenberg ----------
_NUM = (r"(?:[IVXLC]+\b|\d+\b|(?:[A-Z]+-)?(?:[A-Z]*(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|TEEN|TY)|"
        r"[A-Z]*(?:FIRST|SECOND|THIRD)|[A-Z]{3,}TH|THE|LAST)\b)")
# Yalnızca numaralı başlıklar: "CHAPTER XI", "Letter 3", "PART ONE", "Book the First", "THE SECOND BOOK"
STRONG = re.compile(rf"^(?:(?:CHAPTER|CHAP\.|STAVE|LETTER|ADVENTURE|CANTO|BOOK|PART|VOLUME)\s+{_NUM}|THE\s+[A-Z]+\s+BOOK\b).*$", re.I)
GROUP = re.compile(rf"^(?:(?:BOOK|PART|VOLUME)\s+{_NUM}|THE\s+[A-Z]+\s+BOOK\b)", re.I)
BARE = re.compile(r"^([IVXLC]{1,8}|\d{1,3})\.?( — [^—]{2,80})?$")
TITLED = re.compile(r"^([IVXLC]{1,8}|\d{1,3})(\.\s+[^;,!?\[\]]{2,60}|\s+[A-Z][^a-z;,!?\[\]]{2,60})$")
UPPER = re.compile(r"^[^a-z\[\]]{3,70}$")
SENTENCE_END = re.compile(r"[.!?:;,]$")


def gutenberg_paragraphs(raw: str) -> tuple[dict, list[str]]:
    raw = raw.replace("﻿", "")
    meta = {}
    for key in ("Title", "Author", "Language", "Translator"):
        m = re.search(rf"^{key}:\s*(.+(?:\n {{2,}}.+)*)", raw, re.M)
        if m:
            meta[key.lower()] = re.sub(r"\s+", " ", m.group(1)).strip()
    s = re.search(r"^\*\*\* ?START OF.*$", raw, re.M)
    e = re.search(r"^\*\*\* ?END OF.*$", raw, re.M)
    body = raw[s.end() if s else 0: e.start() if e else len(raw)]
    # Bazı baskılarda bölüm başlığı yalnızca resim altı yazısında kalır: "[Illustration: … Chapter I.]"
    body = re.sub(r"\[Illustration:?[^\]]*?\bChapter ([IVXLC]+)\.?\s*\]", r"\n\nCHAPTER \1.\n\n", body, flags=re.I)
    body = re.sub(r"\[(Illustration|Frontispiece)[^\]]*\]", "", body, flags=re.I)
    paras = []
    for block in re.split(r"\n\s*\n", body):
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        # "CHAPTER I." + "Down the Rabbit-Hole" aynı blokta → tek başlık
        if 2 <= len(lines) <= 3 and sum(map(len, lines)) < 140 and \
                (STRONG.match(lines[0]) or BARE.match(lines[0]) or TITLED.match(lines[0])):
            lines = [" — ".join(lines)]
        poem = len(lines) > 1 and max(map(len, lines)) < 55
        p = "\n".join(lines) if poem else " ".join(lines)
        p = re.sub(r"(?<![A-Za-z0-9])_(.+?)_(?![A-Za-z0-9])", r"\1", p, flags=re.S)
        p = re.sub(r"[ \t]{2,}", " ", p).strip()
        p = re.sub(r"(?<=\S)--(?=\S)|(?<=\s)--(?=\s)|^--|--$", "—", p)
        if p and not re.fullmatch(r"[\s*.·_\-=\]\[]+", p):
            paras.append(p)
    return meta, paras


def _title_like(p: str) -> bool:
    rest = p.split(" ", 1)[1] if " " in p else ""
    words = [w for w in rest.split() if w[:1].isalpha()]
    if not words:
        return False
    small = {"a", "an", "the", "of", "and", "in", "on", "at", "to", "for", "with", "by", "or", "from", "into"}
    return all(w[0].isupper() or w.lower() in small for w in words)


def split_chapters(paras: list[str], min_body=350) -> list[dict]:
    def heads(rx, extra=None):
        return [i for i, p in enumerate(paras) if "\n" not in p and len(p) <= 120 and rx.match(p) and (extra is None or extra(p))]

    def ok(chs):
        real = [c for c in chs if not c.get("front")]
        if len(real) < 3:
            return False
        sizes = [sum(len(p) for p in c["p"]) for c in real]
        return len(real) > 8 or max(sizes) < 0.6 * sum(sizes)

    strong = sorted(set(heads(STRONG)) | set(heads(TITLED, _title_like)))
    bare = heads(BARE)
    upper = heads(UPPER, lambda p: sum(c.isalpha() for c in p) >= 4 and not SENTENCE_END.search(p))
    candidates = []
    if strong:
        grouped = sum(1 for i in strong if GROUP.match(paras[i])) >= len(strong) / 2
        if grouped and len(bare) >= 2 * len(strong):
            candidates.append(sorted(set(strong) | set(bare)))
        candidates.append(strong)
    candidates += [bare, sorted(set(upper) | set(bare))]
    for hs in candidates:
        chs = build(paras, hs, min_body)
        if ok(chs):
            return split_long(chs)
    return chunk(paras)


def build(paras, heads, min_body):
    chapters, group = [], ""
    hs = set(heads)
    first = heads[0] if heads else len(paras)
    front = paras[:first]
    if front and sum(len(p) for p in front) > 2500 and sum(len(p) for p in front) / len(front) > 150:
        chapters.append({"t": "Önsöz", "p": front, "front": True})
    i = first
    while i < len(paras):
        title = paras[i]
        j = i + 1
        while j < len(paras) and j not in hs:
            j += 1
        body = paras[i + 1:j]
        # Başlığın hemen altındaki kısa satır alt başlıktır: "I" + "The Old Sea-dog…" → "I — The Old Sea-dog…"
        if body and len(body[0]) <= 70 and "\n" not in body[0] and " — " not in title and body[0][:1].isupper() and \
                not SENTENCE_END.search(body[0].rstrip("\"”’'")):
            title = f"{title} — {body[0]}"
            body = body[1:]
        size = sum(len(p) for p in body)
        lines = [ln for p in body for ln in p.split("\n")]
        toc = sum(1 for ln in lines if re.search(r"(\. ?){3,}|\s\d{1,4}$", ln)) > 0.4 * max(1, len(lines))
        if size < min_body or toc:
            if GROUP.match(paras[i]):
                group = clean_title(title)
            i = j
            continue
        ch = {"t": clean_title(title), "p": body}
        if group:
            ch["g"] = group
        chapters.append(ch)
        i = j
    return chapters


def split_long(chapters, limit=90000):
    out = []
    for c in chapters:
        size = sum(len(p) for p in c["p"])
        if size <= limit:
            out.append(c)
            continue
        parts = chunk(c["p"], target=size // -(-size // limit) + 1)
        for k, part in enumerate(parts, 1):
            out.append({**c, "t": f"{c['t']} ({k}/{len(parts)})", "p": part["p"]})
    return out


def clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip(" .")
    t = re.sub(r"\s*--\s*", " — ", t)
    t = re.sub(r"\.\s*—\s*", " — ", t)  # "Chapter 1. — Başlık" → "Chapter 1 — Başlık"

    def fix(part):
        if sum(c.isupper() for c in part) > 3 and not any(c.islower() for c in part):
            return " ".join(w if re.fullmatch(r"[IVXLC]+\.?", w) else w.capitalize() for w in part.split(" "))
        return part

    return " — ".join(fix(x) for x in t.split(" — "))


def chunk(paras, target=22000):
    chapters, cur, size = [], [], 0
    for p in paras:
        cur.append(p)
        size += len(p)
        if size >= target:
            chapters.append({"t": f"Bölüm {len(chapters) + 1}", "p": cur})
            cur, size = [], 0
    if cur:
        if chapters and size < target / 4:
            chapters[-1]["p"].extend(cur)
        else:
            chapters.append({"t": f"Bölüm {len(chapters) + 1}", "p": cur})
    return chapters


def gutenberg_book(gid, genres, tr_title, desc):
    raw = fetch(f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt", f"gutenberg/{gid}.txt")
    meta, paras = gutenberg_paragraphs(raw)
    chapters = split_chapters(paras)
    small = {"a", "an", "the", "of", "and", "in", "on", "at", "to", "for", "with", "by", "or", "from", "into", "under"}
    title = sources.TITLES.get(gid) or meta.get("title", tr_title)
    title = " ".join(w if i and w in small else w[:1].upper() + w[1:] for i, w in enumerate(title.split(" ")))
    return {
        "id": f"en-{gid}", "title": title, "tr": tr_title, "author": sources.AUTHORS.get(gid) or meta.get("author", ""),
        "lang": "en", "genres": genres, "desc": desc, "translator": meta.get("translator", ""),
        "source": f"Project Gutenberg #{gid}", "url": f"https://www.gutenberg.org/ebooks/{gid}",
        "chapters": [{k: v for k, v in c.items() if k != "front"} for c in chapters],
    }


# ---------- Vikikaynak ----------
class WsText(HTMLParser):
    SKIP_CLASS = ("ws-noexport", "pagenum", "licenseContainer", "reference", "mw-editsection", "noprint", "ws-pagenum",
                  "mw-references-wrap", "catlinks", "printfooter")
    BLOCK = {"p", "dd", "li", "h2", "h3", "h4", "h5", "div", "tr"}
    VOID = {"br", "img", "hr", "wbr", "meta", "link", "input", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.skip, self.buf, self.paras = [], 0, [], []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            if tag == "br":
                self.buf.append("\n")
            return
        a = dict(attrs)
        cls = a.get("class", "") or ""
        skip = tag in ("style", "script", "table", "sup") or any(c in cls for c in self.SKIP_CLASS) or \
            a.get("id") in ("headerContainer", "toc") or "display:none" in (a.get("style") or "").replace(" ", "")
        if tag in self.BLOCK:
            self.flush()
        self.stack.append((tag, skip))
        if skip:
            self.skip += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.VOID or not any(t == tag for t, _ in self.stack):
            return
        while self.stack:
            t, skip = self.stack.pop()
            if skip:
                self.skip -= 1
            if t == tag:
                break
        if tag in self.BLOCK:
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def flush(self):
        t = "".join(self.buf)
        self.buf = []
        # Vikikaynak'ta paragraflar çoğu zaman <p> ile değil <br> + girintiyle ayrılır; her satır ayrı paragraftır
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in t.split("\n")]
        self.paras.extend(ln for ln in lines if ln)


def ws_paragraphs(page: str) -> list[str]:
    d = ws_api(f"wikisource/{slug(page)}.json", action="parse", page=page, prop="text", redirects=1)
    p = WsText()
    p.feed(d["parse"]["text"])
    p.flush()
    out = []
    for t in p.paras:
        t = html.unescape(t).replace("­", "")
        t = re.sub(r"\(-[^)]{0,30}\)", "", t)  # "görmediğim(-me,isim fiil)" gibi editör notları
        if re.fullmatch(r"[\s\d\-–—.·*]+", t):
            continue
        # sayfa geçişlerinde bölünen paragrafları birleştir
        if out and out[-1][-1:].isalpha() and t[:1].islower():
            out[-1] += " " + t
        else:
            out.append(t)
    return out


def ws_category(cat: str) -> list[str]:
    d = ws_api(f"wikisource/cat-{slug(cat)}.json", action="query", list="categorymembers", cmtitle=cat, cmlimit=500)
    return [m["title"] for m in d["query"]["categorymembers"] if m["ns"] == 0]


def tr_novel(title, author, year, genres, desc):
    paras = ws_paragraphs(title)
    # Baştaki künye satırlarını (ad, yazar, yayınevi…) at; ilk gerçek paragrafa kadar
    while paras and len(paras[0]) < 120:
        paras.pop(0)
    heads = [i for i, p in enumerate(paras) if BARE.match(p.strip())]
    chapters = build(paras, heads, 300) if len(heads) >= 3 else chunk(paras)
    for c in chapters:
        c.pop("front", None)
        if BARE.match(c["t"]):
            c["t"] = f"Bölüm {c['t'].rstrip('.')}"
    return {"id": slug(title), "title": title, "author": author, "lang": "tr", "genres": genres, "desc": desc, "year": year,
            "source": "Vikikaynak", "url": "https://tr.wikisource.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
            "chapters": chapters}


def tr_collection(book_id, title, author, genres, desc, pages):
    chapters = []
    for page in pages:
        try:
            paras = ws_paragraphs(page)
        except Exception as e:  # noqa: BLE001
            print("   ! atlandı:", page, e)
            continue
        name = re.sub(r"\s*\((hikâye|hikaye|Ömer Seyfettin)\)$", "", page)
        if paras and paras[0].strip(" .") == name:
            paras = paras[1:]
        if paras and paras[0].startswith(author):
            paras = paras[1:]
        if sum(len(p) for p in paras) < 400:  # yalnızca başlık sayfası olan, metni olmayan girdiler
            print("   - boş:", page)
            continue
        chapters.append({"t": name, "p": paras})
    chapters.sort(key=lambda c: c["t"].translate(str.maketrans("ÇĞİÖŞÜçğıöşüÂâ", "CGIOSUcgiosuAa")).lower())
    return {"id": book_id, "title": title, "author": author, "lang": "tr", "genres": genres, "desc": desc,
            "source": "Vikikaynak", "url": "https://tr.wikisource.org", "chapters": chapters}


# ---------- Özgün öyküler ----------
def originals():
    out = []
    for f in sorted(ORIGINALS.glob("*.md")):
        text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
        meta = {k.strip(): v.strip() for k, v in (ln.split(":", 1) for ln in m.group(1).split("\n") if ":" in ln)}
        chapters, cur = [], None
        for block in re.split(r"\n\s*\n", m.group(2).strip()):
            block = block.strip()
            if block.startswith("## "):
                cur = {"t": block[3:].strip(), "p": []}
                chapters.append(cur)
                continue
            if cur is None:
                cur = {"t": meta["title"], "p": []}
                chapters.append(cur)
            if re.fullmatch(r"-{3,}|\*\s*\*\s*\*", block):
                block = "⁂"
            # Okuyucu "§§ " ile başlayan paragrafı ara başlık, "§_ " ile başlayanı italik gösterir
            elif m2 := re.fullmatch(r"\*\*(.+?)\*\*", block, re.S):
                block = "§§ " + m2.group(1)
            elif m2 := re.fullmatch(r"\*([^*].*?)\*", block, re.S):
                block = "§_ " + m2.group(1)
            block = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"\1", block)
            # Birden çok satırlı blok şiirdir: satır sonları korunur, okuyucu "poem" olarak gösterir
            cur["p"].append("\n".join(ln.strip() for ln in block.split("\n") if ln.strip()))
        # kind: ozgun (yeni yazılmış), ceviri (Kitap Köşkü çevirisi), derleme (halk edebiyatının yeniden anlatımı)
        kind = meta.get("kind", "ozgun")
        source = {"ozgun": "Kitap Köşkü özgün öyküsü", "ceviri": "Kitap Köşkü çevirisi",
                  "derleme": "Kitap Köşkü derlemesi"}.get(kind, "Kitap Köşkü")
        book = {"id": "ozgun-" + f.stem, "title": meta["title"], "author": meta.get("author", "Kitap Köşkü"),
                "lang": meta.get("lang", "tr"), "genres": [g.strip() for g in meta["genres"].split(",")],
                "desc": meta.get("desc", ""), "source": meta.get("source", source), "chapters": chapters}
        if kind == "ozgun":
            book["original"] = True
        else:
            book["kind"] = kind
        if meta.get("translator"):
            book["translator"] = meta["translator"]
        out.append(book)
    return out


# ---------- yazma ----------
def save(book: dict, catalog: list):
    words = sum(len(p.split()) for c in book["chapters"] for p in c["p"])
    if not book["chapters"] or words < 300:
        print(f"   ! çok kısa, eklenmedi: {book['id']}")
        return
    path = BOOKS / f"{book['id']}.json.gz"
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump(book, fh, ensure_ascii=False, separators=(",", ":"))
    entry = {k: book[k] for k in ("id", "title", "author", "lang", "genres", "desc", "source") if k in book}
    for k in ("tr", "year", "original", "translator", "kind"):
        if book.get(k):
            entry[k] = book[k]
    entry.update(words=words, chapters=len(book["chapters"]), size=path.stat().st_size)
    catalog[:] = [c for c in catalog if c["id"] != book["id"]] + [entry]
    print(f"   ✓ {book['id']:<28} {len(book['chapters']):>4} bölüm {words:>8} kelime  {path.stat().st_size // 1024:>5} KB  {book.get('title')[:50]}")


def main():
    global OFFLINE
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="virgülle ayrılmış kitap kimlikleri")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    OFFLINE = args.offline
    only = set(filter(None, args.only.split(",")))
    BOOKS.mkdir(exist_ok=True)
    cat_path = BOOKS / "catalog.json"
    catalog = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else []

    jobs = []
    for gid, genres, tr, desc in sources.GUTENBERG:
        jobs.append((f"en-{gid}", lambda a=(gid, genres, tr, desc): gutenberg_book(*a)))
    for title, author, year, genres, desc in sources.TR_NOVELS:
        jobs.append((slug(title), lambda a=(title, author, year, genres, desc): tr_novel(*a)))

    def omer(tarihi: bool):
        pages = ws_category("Kategori:Ömer Seyfettin hikayeleri")
        keep = set(sources.OMER_SEYFETTIN_TARIHI)
        pages = [p for p in pages if (p in keep) == tarihi]
        if tarihi:
            return tr_collection("omer-seyfettin-tarihi", "Kahramanlık Hikâyeleri", "Ömer Seyfettin", ["turk", "macera", "oyku"],
                                 "Forsa, Başını Vermeyen Şehit, Pembe İncili Kaftan, Kızıl Elma Neresi? ve diğer tarihî, kahramanlık dolu hikâyeler.", pages)
        return tr_collection("omer-seyfettin-secme", "Seçme Hikâyeler", "Ömer Seyfettin", ["turk", "oyku"],
                             "Kaşağı, Kesik Bıyık, Falaka, Pireler, Perili Köşk… Türk öykücülüğünün ustasından mizah ve hayat dolu hikâyeler.", pages)

    jobs.append(("omer-seyfettin-tarihi", lambda: omer(True)))
    jobs.append(("omer-seyfettin-secme", lambda: omer(False)))
    jobs.append(("turk-halk-masallari", lambda: tr_collection(
        "turk-halk-masallari", "Türk Halk Masalları", "Anonim", ["masal", "turk"],
        "Keloğlan ve Padişah, Kuyruksuz Tilki, Külden Eşek ve Anadolu'dan derlenmiş diğer masallar.",
        ws_category(sources.TR_MASAL_CATEGORY))))

    failed = []
    for bid, job in jobs:
        if only and bid not in only:
            continue
        print("→", bid)
        try:
            save(job(), catalog)
        except Exception as e:  # noqa: BLE001
            failed.append(bid)
            print(f"   ! HATA {bid}: {e}")
    current = originals()
    for book in current:
        if not only or book["id"] in only:
            save(book, catalog)
    # originals/ klasöründen silinen ya da adı değişen öykülerin kayıtlarını temizle
    keep = {b["id"] for b in current}
    for c in [c for c in catalog if c["id"].startswith("ozgun-") and c["id"] not in keep]:
        catalog.remove(c)
        (BOOKS / f"{c['id']}.json.gz").unlink(missing_ok=True)
        print("   - kaldırıldı:", c["id"])

    order = {g: i for i, g in enumerate(["turk", "korku", "polisiye", "macera", "bilimkurgu", "klasik", "masal", "mizah", "oyku"])}
    catalog.sort(key=lambda c: (not c.get("original"), c["lang"] != "tr", order.get(c["genres"][0], 99), c.get("tr") or c["title"]))
    cat_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=0), encoding="utf-8")
    total = sum(c["size"] for c in catalog)
    print(f"\nToplam {len(catalog)} kitap, {total / 1024 / 1024:.1f} MB" + (f"  | başarısız: {', '.join(failed)}" if failed else ""))


if __name__ == "__main__":
    main()
