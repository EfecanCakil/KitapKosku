"""Çevrimdışı İngilizce→Türkçe makine çevirisi (Helsinki-NLP opus-mt-tc-big-en-tr, CTranslate2 int8, CC BY 4.0).

Model exe içinde mt-model/ klasöründe, geliştirmede tools/_models/en-tr-big altında durur. Yoksa şu komutla üretilir:
  ct2-transformers-converter --model Helsinki-NLP/opus-mt-tc-big-en-tr --output_dir tools/_models/en-tr-big \
      --quantization int8 --copy_files source.spm target.spm
"""
import os
import re
import sys
import unicodedata
from pathlib import Path

_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
MODEL = next((p for p in (_BASE / "mt-model", _BASE / "tools" / "_models" / "en-tr-big") if (p / "model.bin").exists()),
             _BASE / "mt-model")

ABBR = {"mr", "mrs", "ms", "dr", "st", "mt", "jr", "sr", "prof", "capt", "col", "gen", "lt", "sgt", "rev", "hon", "no",
        "vol", "chap", "viz", "etc", "co", "messrs", "mme", "mlle", "m", "i.e", "e.g", "esq", "fig"}
_SPLIT = re.compile(r"([.!?][\"”’')\]]*)\s+(?=[\"“‘'(\[]*[A-Z0-9—])")
_HEAD = {"chapter": "Bölüm", "chap": "Bölüm", "stave": "Bölüm", "letter": "Mektup", "part": "Kısım", "book": "Kitap",
         "volume": "Cilt", "adventure": "Macera", "canto": "Kanto"}


def available() -> bool:
    return (MODEL / "model.bin").exists()


def sentences(par: str) -> list[str]:
    """Paragrafı cümlelere böler; modelin kaldıramayacağı kadar uzun cümleleri virgülden de böler."""
    out, start = [], 0
    for m in _SPLIT.finditer(par):
        word = re.search(r"([\w.]+)$", par[start:m.start(1) + 1].rstrip("."))
        w = word.group(1).lower() if word else ""
        if par[m.start(1)] == "." and (w in ABBR or len(w) == 1):  # "Mr. Holmes", "J. Watson"
            continue
        out.append(par[start:m.end(1)].strip())
        start = m.end()
    out.append(par[start:].strip())
    res = []
    for s in filter(None, out):
        while len(s) > 600:
            cut = max(s.rfind("; ", 0, 500), s.rfind(", ", 0, 500))
            if cut < 100:
                break
            res.append(s[:cut + 1])
            s = s[cut + 2:]
        res.append(s)
    return res


def _prepare(s: str) -> str:
    s = s.replace("æ", "ae").replace("Æ", "Ae").replace("œ", "oe").replace("Œ", "Oe").replace("£", "sterlin ")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"\s*—\s*", " — ", s).strip()


def _finish(src: str, out: str) -> str:
    out = out.replace(" ⁇ ", " — " if "—" in src else " ").replace("⁇", "—" if "—" in src else "")
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    return re.sub(r"\s{2,}", " ", out).strip()


class Translator:
    def __init__(self, threads: int | None = None):
        import ctranslate2
        import sentencepiece as spm

        threads = threads or max(2, min(6, (os.cpu_count() or 4) - 2))
        self.tr = ctranslate2.Translator(str(MODEL), device="cpu", compute_type="int8", inter_threads=1, intra_threads=threads)
        self.sp_src = spm.SentencePieceProcessor(model_file=str(MODEL / "source.spm"))
        self.sp_tgt = spm.SentencePieceProcessor(model_file=str(MODEL / "target.spm"))

    def translate(self, texts: list[str], beam: int = 2) -> list[str]:
        if not texts:
            return []
        src = [_prepare(t) for t in texts]
        toks = [self.sp_src.encode(t, out_type=str)[:400] + ["</s>"] for t in src]
        res = self.tr.translate_batch(toks, beam_size=beam, max_batch_size=2048, batch_type="tokens",
                                      max_decoding_length=512, repetition_penalty=1.1, no_repeat_ngram_size=4)
        return [_finish(s, self.sp_tgt.decode([t for t in r.hypotheses[0] if t != "</s>"])) for s, r in zip(src, res)]

    def paragraphs(self, paras: list[str], beam: int = 2) -> list[str]:
        """Paragrafları cümle cümle çevirip aynı sırayla paragraf olarak geri birleştirir (şiir satırları korunur)."""
        flat, owner = [], []
        for i, p in enumerate(paras):
            for li, line in enumerate(p.split("\n")):
                for s in sentences(line) if line.strip() else []:
                    flat.append(s)
                    owner.append((i, li))
        order = sorted(range(len(flat)), key=lambda k: len(flat[k]))
        done = self.translate([flat[k] for k in order], beam=beam)
        trans = [""] * len(flat)
        for k, t in zip(order, done):
            trans[k] = t
        out = [[[] for _ in p.split("\n")] for p in paras]
        for (i, li), t in zip(owner, trans):
            out[i][li].append(t)
        return ["\n".join(" ".join(x) for x in lines) for lines in out]

    def title(self, t: str) -> str:
        """"Chapter IV — The Sea-chest" → "Bölüm IV — Deniz Sandığı": numaralı kısım kuralla, kalanı modelle çevrilir."""
        out = []
        for part in t.split(" — "):
            m = re.match(r"^(chapter|chap\.?|stave|letter|part|book|volume|adventure|canto)\s+(.+)$", part, re.I)
            if m and len(m.group(2)) < 20 and re.fullmatch(r"[IVXLC\d]+|[A-Za-z]+(-[A-Za-z]+)?|the [a-z]+", m.group(2), re.I):
                out.append(f"{_HEAD[m.group(1).lower().rstrip('.')]} {m.group(2)}")
            elif re.fullmatch(r"[IVXLC\d]+\.?", part):
                out.append(part)
            else:
                out.append(self.translate([part])[0].rstrip("."))
        return " — ".join(out)
