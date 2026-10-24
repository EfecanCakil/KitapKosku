"""İngilizce kitapların arka planda, okundukça Türkçeye çevrilmesi.

Okunan bölüm en önce, ardından bir sonraki bölüm çevrilir; "tüm kitabı çevir" istekleri en geride bekler.
İş küçük paragraf dilimleriyle ilerler, böylece yeni bir okuma isteği en geç bir dilim sonra öne geçer.
Çeviriler %APPDATA%\\KitapKosku\\ceviri\\<kitap>.json dosyasına yazılır ve bir daha çevrilmez.
"""
import gzip
import heapq
import itertools
import json
import os
import threading
import time
from pathlib import Path

import mt

READ, NEXT, BOOK = 0, 1, 5  # öncelikler: okunan bölüm, sıradaki bölüm, bütün kitap
SLICE_WORDS = 450  # bir dilimde çevrilen yaklaşık kelime sayısı (≈4 sn)


class Service:
    def __init__(self, data_dir: Path, get_book, bundled_dir: Path | None = None):
        self.dir = data_dir / "ceviri"
        self.bundled = bundled_dir  # uygulamayla gelen hazır çeviriler (books/ceviri/<kitap>.json.gz)
        self.get_book = get_book
        self.cache = {}  # kitap → {"ch": {"3": {"t": str|None, "p": [str|None]}}}
        self.dirty = {}
        self.lock = threading.RLock()
        self.cv = threading.Condition(self.lock)
        self.queue = []
        self.seq = itertools.count()
        self.queued = {}  # (kitap, bölüm) → en iyi öncelik
        self.translator = None
        self.error = "" if mt.available() else "Çeviri modeli bulunamadı."
        self.busy = None
        self.words_cache = {}
        self.thread = None

    # ---------- önbellek ----------
    def _load(self, book_id: str) -> dict:
        with self.lock:
            if book_id not in self.cache:
                try:
                    self.cache[book_id] = json.loads((self.dir / f"{book_id}.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    self.cache[book_id] = self._bundled(book_id) or {"ch": {}}
            return self.cache[book_id]

    def _bundled(self, book_id: str) -> dict | None:
        path = self.bundled / f"{book_id}.json.gz" if self.bundled else None
        if path and path.exists():
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                return json.load(fh)
        return None

    def _flush(self, force=False):
        now = time.time()
        for book_id, at in list(self.dirty.items()):
            if force or now - at > 3:
                self.dir.mkdir(parents=True, exist_ok=True)
                tmp = self.dir / f"{book_id}.tmp"
                with self.lock:
                    data = json.dumps(self.cache[book_id], ensure_ascii=False, separators=(",", ":"))
                    self.dirty.pop(book_id, None)
                tmp.write_text(data, encoding="utf-8")
                os.replace(tmp, self.dir / f"{book_id}.json")
                summary = self.summary()
                summary[book_id] = round(self.progress(book_id)["f"], 3)
                (self.dir / "_ozet.json").write_text(json.dumps(summary), encoding="utf-8")

    def _entry(self, book_id: str, ch: int, n: int) -> dict:
        c = self._load(book_id)["ch"]
        e = c.get(str(ch))
        if not e or len(e["p"]) != n:
            e = c[str(ch)] = {"t": None, "p": [None] * n}
        return e

    # ---------- dışarıya açık ----------
    def chapter(self, book_id: str, ch: int, start: int = 0) -> dict:
        """Bölümün o ana kadar çevrilmiş hâli; eksikse çeviriyi (okunan yerden başlayarak) sıraya koyar."""
        book = self.get_book(book_id)
        chs = book["chapters"]
        with self.lock:
            e = self._entry(book_id, ch, len(chs[ch]["p"]))
            done = e["t"] is not None and all(x is not None for x in e["p"])
            if not done and not self.error:
                self._push(READ, book_id, ch, start)
            if ch + 1 < len(chs):
                n = self._entry(book_id, ch + 1, len(chs[ch + 1]["p"]))
                if (n["t"] is None or None in n["p"]) and not self.error:
                    self._push(NEXT, book_id, ch + 1, 0)
            return {"t": e["t"], "g": e.get("g", ""), "p": list(e["p"]), "done": done, "error": self.error}

    def translate_book(self, book_id: str) -> dict:
        chs = self.get_book(book_id)["chapters"]
        with self.lock:
            for i, c in enumerate(chs):
                e = self._entry(book_id, i, len(c["p"]))
                if e["t"] is None or None in e["p"]:
                    self._push(BOOK, book_id, i, 0)
        return self.progress(book_id)

    def progress(self, book_id: str) -> dict:
        chs = self.get_book(book_id)["chapters"]
        with self.lock:
            c = self._load(book_id)["ch"]
            total = sum(len(x["p"]) for x in chs) or 1
            done = sum(sum(1 for p in c[str(i)]["p"] if p is not None) for i in range(len(chs))
                       if str(i) in c and len(c[str(i)]["p"]) == len(chs[i]["p"]))
            waiting = any(k[0] == book_id for k in self.queued)
            words_left = sum(sum(len(p.split()) for p, t in zip(chs[i]["p"], c.get(str(i), {}).get("p") or [None] * len(chs[i]["p"]))
                                 if t is None) for i in range(len(chs)))
        return {"f": done / total, "queued": waiting, "error": self.error, "eta": int(words_left / 110)}

    def summary(self) -> dict:
        """Kütüphane rozetleri için: diskte çevirisi olan kitapların tamamlanma oranı."""
        out = {}
        for path in ([self.bundled / "_ozet.json"] if self.bundled else []) + [self.dir / "_ozet.json"]:
            try:
                for k, v in json.loads(path.read_text(encoding="utf-8")).items():
                    out[k] = max(v, out.get(k, 0))
            except (OSError, ValueError):
                pass
        return out

    def word(self, text: str) -> str:
        """Sözlükte bulunmayan bir kelimenin makine çevirisi (önbellekli)."""
        text = (text or "").strip()[:60]
        if not text or self.error:
            return ""
        if text not in self.words_cache:
            self._ensure_model()
            out = self.translator.translate([text], beam=4)[0].rstrip(".")
            if text[:1].islower():
                out = out[:1].lower() + out[1:]
            self.words_cache[text] = "" if out.lower() == text.lower() else out
        return self.words_cache[text]

    def warm(self):
        """Model ilk açılışta birkaç saniye yüklenir; İngilizce kitap açılınca arkada önceden yükle."""
        if not self.error and self.translator is None:
            threading.Thread(target=self._ensure_model, daemon=True).start()

    def shutdown(self):
        self._flush(force=True)

    # ---------- kuyruk ----------
    def _push(self, prio, book_id, ch, start):
        key = (book_id, ch)
        if self.queued.get(key, 99) < prio or (self.queued.get(key) == prio and start == 0):
            return
        self.queued[key] = prio
        heapq.heappush(self.queue, (prio, next(self.seq), book_id, ch, start))
        if not self.thread:
            self.thread = threading.Thread(target=self._run, daemon=True, name="ceviri")
            self.thread.start()
        self.cv.notify()

    def _ensure_model(self):
        with self.lock:
            if self.translator is None:
                self.translator = mt.Translator()

    def _run(self):
        try:
            self._ensure_model()
        except Exception as e:  # noqa: BLE001
            self.error = f"Çeviri modeli açılamadı: {e}"
            return
        while True:
            with self.lock:
                while not self.queue:
                    self._flush(force=True)
                    self.busy = None
                    self.cv.wait(timeout=5)
                prio, _, book_id, ch, start = heapq.heappop(self.queue)
                if self.queued.get((book_id, ch)) != prio:
                    continue  # aynı bölüm daha yüksek öncelikle yeniden sıraya girmiş
                del self.queued[(book_id, ch)]
            try:
                more = self._slice(book_id, ch, start)
            except Exception as e:  # noqa: BLE001
                self.error = f"Çeviri hatası: {e}"
                more = False
            with self.lock:
                if more:  # bölüm bitmedi: aynı öncelikle geri koy, araya daha önemli iş girebilsin
                    self._push(prio, book_id, ch, start)
            self._flush()

    def _slice(self, book_id: str, ch: int, start: int) -> bool:
        src = self.get_book(book_id)["chapters"][ch]
        with self.lock:
            e = self._entry(book_id, ch, len(src["p"]))
            todo = [i for i in list(range(start, len(src["p"]))) + list(range(0, start)) if e["p"][i] is None]
            need_title = e["t"] is None
        self.busy = (book_id, ch)
        if need_title:
            t = src["t"] if src["t"] in ("Önsöz",) else self.translator.title(src["t"])
            g = self.translator.title(src["g"]) if src.get("g") else ""
            with self.lock:
                e["t"] = t
                if g:
                    e["g"] = g
                self.dirty.setdefault(book_id, time.time())
        if not todo:
            return False
        # Bölümün ilk dilimi küçük tutulur ki okuyucu ekranı birkaç saniyede dolmaya başlasın
        limit = SLICE_WORDS if any(p is not None for p in e["p"]) else 120
        pick, words = [], 0
        for i in todo:
            pick.append(i)
            words += len(src["p"][i].split())
            if words >= limit:
                break
        texts = [src["p"][i] for i in pick]
        # İşaretli paragraflar ("§§ ara başlık") işaretiyle korunur
        marks = [t[:3] if t.startswith(("§§ ", "§_ ")) else "" for t in texts]
        out = self.translator.paragraphs([t[len(m):] for t, m in zip(texts, marks)])
        with self.lock:
            for i, m, t in zip(pick, marks, out):
                e["p"][i] = m + t
            self.dirty.setdefault(book_id, time.time())
        return len(todo) > len(pick)
