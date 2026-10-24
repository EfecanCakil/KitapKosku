"""Kitap Köşkü: internetsiz çalışan kitap okuma uygulaması.

Giriş noktası. pywebview ile yerel bir pencere açar; arayüz (web/) Python tarafına window.pywebview.api üzerinden ulaşır.
Kitaplar books/ klasöründe sıkıştırılmış JSON olarak durur (tools/build_library.py üretir).
Okuma ilerlemesi, favoriler, yer imleri ve ayarlar %APPDATA%\\KitapKosku\\state.json dosyasında tutulur.
"""
import gzip
import json
import os
import re
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path

if sys.stdout is None:  # konsolsuz exe'de kütüphanelerin yazdıkları hata vermesin
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
BOOKS = BASE / "books"
WEB = BASE / "web"
DATA = Path(os.environ.get("APPDATA", Path.home())) / "KitapKosku"
STATE_FILE = DATA / "state.json"
APP_NAME = "Kitap Köşkü"

DEFAULT_SETTINGS = {"theme": "sepya", "font": "serif", "size": 20, "line": 1.75, "width": 680, "align": "left",
                    "mode": "tr", "hover": True}


class Api:
    """Arayüzün çağırdığı fonksiyonlar. pywebview her çağrıyı ayrı bir iş parçacığında çalıştırır."""

    def __init__(self):
        import ceviri

        self._lock = threading.Lock()
        self._books = OrderedDict()  # son açılan birkaç kitap bellekte kalır
        self._catalog = json.loads((BOOKS / "catalog.json").read_text(encoding="utf-8"))
        self._state = self._load_state()
        self._tr = ceviri.Service(DATA, self._book, BOOKS / "ceviri")
        self._dict = None

    # ---------- durum ----------
    def _load_state(self) -> dict:
        try:
            s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            s = {}
        s.setdefault("progress", {})
        s.setdefault("favorites", [])
        s.setdefault("bookmarks", [])
        s.setdefault("seconds", {})
        s.setdefault("words", [])
        s["settings"] = {**DEFAULT_SETTINGS, **s.get("settings", {})}
        return s

    def _save_state(self):
        DATA.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, STATE_FILE)

    def _book(self, book_id: str) -> dict:
        with self._lock:
            if book_id in self._books:
                self._books.move_to_end(book_id)
                return self._books[book_id]
        if not re.fullmatch(r"[a-z0-9-]+", book_id or ""):
            raise ValueError("Geçersiz kitap.")
        with gzip.open(BOOKS / f"{book_id}.json.gz", "rt", encoding="utf-8") as fh:
            book = json.load(fh)
        for ch in book["chapters"]:
            ch["w"] = sum(len(p.split()) for p in ch["p"])
        with self._lock:
            self._books[book_id] = book
            while len(self._books) > 4:
                self._books.popitem(last=False)
        return book

    # ---------- kütüphane ----------
    def library(self) -> dict:
        s = self._state
        return {"books": self._catalog, "progress": s["progress"], "favorites": s["favorites"],
                "settings": s["settings"], "bookmarks": s["bookmarks"], "seconds": s["seconds"], "words": s["words"],
                "translated": self._tr.summary(), "mt": not self._tr.error}

    def book_info(self, book_id: str) -> dict:
        b = self._book(book_id)
        if b.get("lang") == "en":
            self._tr.warm()
        info = {k: v for k, v in b.items() if k != "chapters"}
        info["toc"] = [{"t": c["t"], "g": c.get("g", ""), "w": c["w"]} for c in b["chapters"]]
        return info

    def chapter(self, book_id: str, index: int) -> dict:
        chs = self._book(book_id)["chapters"]
        index = max(0, min(int(index), len(chs) - 1))
        c = chs[index]
        return {"i": index, "t": c["t"], "g": c.get("g", ""), "p": c["p"], "w": c["w"], "n": len(chs)}

    def search(self, book_id: str, query: str) -> list:
        q = (query or "").strip()
        if len(q) < 2:
            return []
        rx = re.compile(re.escape(q), re.I)
        hits = []
        for ci, c in enumerate(self._book(book_id)["chapters"]):
            for pi, p in enumerate(c["p"]):
                p = re.sub(r"^§[§_] ", "", p)
                m = rx.search(p)
                if m:
                    a, b = max(0, m.start() - 60), min(len(p), m.end() + 80)
                    hits.append({"c": ci, "p": pi, "t": c["t"], "pre": ("…" if a else "") + p[a:m.start()],
                                 "hit": p[m.start():m.end()], "post": p[m.end():b] + ("…" if b < len(p) else "")})
                    if len(hits) >= 150:
                        return hits
        return hits

    # ---------- Türkçe çeviri ve sözlük ----------
    def translation(self, book_id: str, index: int, start: int = 0) -> dict:
        """İngilizce bölümün Türkçesi; henüz çevrilmemiş paragraflar None döner ve çeviri sıraya girer."""
        return self._tr.chapter(book_id, int(index), int(start))

    def translate_book(self, book_id: str) -> dict:
        return self._tr.translate_book(book_id)

    def translation_progress(self, book_id: str) -> dict:
        return self._tr.progress(book_id)

    def dictionary(self) -> dict:
        if self._dict is None:
            with gzip.open(BOOKS / "dict-en-tr.json.gz", "rt", encoding="utf-8") as fh:
                self._dict = json.load(fh)
        return self._dict

    def translate_word(self, word: str) -> str:
        return self._tr.word(word)

    def save_word(self, entry: dict) -> list:
        words = self._state["words"]
        key = (entry.get("w") or "").lower()
        words[:] = [w for w in words if w["w"].lower() != key]
        words.insert(0, {k: str(entry.get(k, ""))[:300] for k in ("w", "l", "tr", "b", "x")} | {"at": int(time.time())})
        self._save_state()
        return words

    def remove_word(self, word: str) -> list:
        words = self._state["words"]
        words[:] = [w for w in words if w["w"].lower() != (word or "").lower()]
        self._save_state()
        return words

    # ---------- kayıt ----------
    def save_progress(self, book_id: str, chapter: int, para: int, frac: float, total: float, mode: str = "") -> bool:
        self._state["progress"][book_id] = {"c": int(chapter), "p": int(para), "f": round(float(frac), 4),
                                            "t": round(float(total), 4), "at": int(time.time())}
        if mode in ("en", "tr", "both"):
            self._state["progress"][book_id]["m"] = mode  # İngilizce kitap hangi dilde okunuyordu
        self._save_state()
        return True

    def add_time(self, book_id: str, seconds: int) -> bool:
        sec = self._state["seconds"]
        sec[book_id] = sec.get(book_id, 0) + max(0, min(int(seconds), 600))
        self._save_state()
        return True

    def toggle_favorite(self, book_id: str) -> list:
        fav = self._state["favorites"]
        fav.remove(book_id) if book_id in fav else fav.insert(0, book_id)
        self._save_state()
        return fav

    def add_bookmark(self, book_id: str, chapter: int, para: int, text: str, title: str = "") -> list:
        bm = self._state["bookmarks"]
        bm[:] = [b for b in bm if not (b["b"] == book_id and b["c"] == chapter and b["p"] == para)]
        bm.insert(0, {"b": book_id, "c": int(chapter), "p": int(para), "x": (text or "")[:160], "t": (title or "")[:120],
                      "at": int(time.time())})
        self._save_state()
        return bm

    def remove_bookmark(self, book_id: str, chapter: int, para: int) -> list:
        bm = self._state["bookmarks"]
        bm[:] = [b for b in bm if not (b["b"] == book_id and b["c"] == chapter and b["p"] == para)]
        self._save_state()
        return bm

    def reset_progress(self, book_id: str) -> bool:
        self._state["progress"].pop(book_id, None)
        self._save_state()
        return True

    def save_settings(self, settings: dict) -> dict:
        self._state["settings"] = {**self._state["settings"], **{k: v for k, v in settings.items() if k in DEFAULT_SETTINGS}}
        self._save_state()
        return self._state["settings"]


api = Api()


def _window_size(want_w=1320, want_h=880) -> tuple[int, int]:
    """Pencereyi ekranın kullanılabilir alanına sığdırır (ölçekli ekranlarda taşmasın diye mantıksal piksel)."""
    try:
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
        dpi = ctypes.windll.user32.GetDpiForSystem() or 96
        w = (rect.right - rect.left) * 96 // dpi
        h = (rect.bottom - rect.top) * 96 // dpi
        return min(want_w, w - 40), min(want_h, h - 40)
    except Exception:  # noqa: BLE001
        return 1200, 760


def selftest():
    """Pencere açmadan paketin çeviri ve sözlük parçalarını dener; sonucu %APPDATA%\\KitapKosku\\selftest.txt'ye yazar."""
    import mt

    try:
        t = time.time()
        res = mt.Translator().translate(["The ship sailed at dawn, and the captain stood silent on the deck."])[0]
        msg = f"ok\n{res}\nsözlük: {len(api.dictionary()['w'])} madde\nsüre: {time.time() - t:.1f} sn\nmodel: {mt.MODEL}"
    except Exception as e:  # noqa: BLE001
        msg = f"hata: {e!r}"
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "selftest.txt").write_text(msg, encoding="utf-8")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    import webview

    w, h = _window_size()
    window = webview.create_window(APP_NAME, str(WEB / "index.html"), js_api=api, width=w, height=h,
                                   min_size=(900, 600), background_color="#1b1714")
    webview.start(private_mode=False, storage_path=str(DATA / "webview"))
    api._tr.shutdown()  # yarım kalan çevirileri diske yaz
    return window


if __name__ == "__main__":
    main()
