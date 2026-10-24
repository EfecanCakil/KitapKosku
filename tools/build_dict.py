"""İngilizce kitaplardaki kelimeler için İngilizce→Türkçe cep sözlüğü üretir: books/dict-en-tr.json.gz

Kaynak: WikDict en-tr (Vikisözlük'ten derlenmiş, CC BY-SA). Önce indirilir:
  https://download.wikdict.com/dictionaries/sqlite/2/en-tr.sqlite3 → tools/_cache/dict/en-tr.sqlite3
Yalnızca kitaplarda geçen kelimeler alınır; çekimli biçimler ("walked", "said") köke ("walk", "say") bağlanır.
"""
import gzip
import json
import re
import sqlite3
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"
DB = Path(__file__).resolve().parent / "_cache" / "dict" / "en-tr.sqlite3"
URL = "https://download.wikdict.com/dictionaries/sqlite/2/en-tr.sqlite3"

POS_TR = {"Noun": "isim", "Verb": "fiil", "Adjective": "sıfat", "Adverb": "zarf", "Pronoun": "zamir",
          "Preposition": "edat", "Conjunction": "bağlaç", "Interjection": "ünlem", "Phrase": "deyim",
          "ProperNoun": "özel isim", "Proper_noun": "özel isim", "Numeral": "sayı", "Determiner": "belirteç",
          "Article": "tanımlık", "Particle": "edat", "Idiom": "deyim", "Prepositional_phrase": "deyim"}

IRREGULAR = """arise arose arisen|awake awoke awoken|be was were been am is are|bear bore borne born|beat beat beaten|become became|
begin began begun|bend bent|bet|bid bade bidden|bind bound|bite bit bitten|bleed bled|blow blew blown|break broke broken|
breed bred|bring brought|build built|burn burnt|burst|buy bought|cast|catch caught|choose chose chosen|cling clung|come came|
cost|creep crept|cut|deal dealt|dig dug|do did done does|draw drew drawn|dream dreamt|drink drank drunk|drive drove driven|
dwell dwelt|eat ate eaten|fall fell fallen|feed fed|feel felt|fight fought|find found|flee fled|fling flung|fly flew flown|
forbid forbade forbidden|forget forgot forgotten|forgive forgave forgiven|freeze froze frozen|get got gotten|give gave given|
go went gone goes|grind ground|grow grew grown|hang hung|have had has|hear heard|hide hid hidden|hit|hold held|hurt|
keep kept|kneel knelt|know knew known|lay laid|lead led|lean leant|leap leapt|learn learnt|leave left|lend lent|let|
lie lay lain|light lit|lose lost|make made|mean meant|meet met|pay paid|put|quit|read|ride rode ridden|ring rang rung|
rise rose risen|run ran|say said says|see saw seen|seek sought|sell sold|send sent|set|shake shook shaken|shed|shine shone|
shoot shot|show showed shown|shrink shrank shrunk|shut|sing sang sung|sink sank sunk|sit sat|slay slew slain|sleep slept|
slide slid|sling slung|slink slunk|smite smote smitten|speak spoke spoken|speed sped|spend spent|spin spun|spit spat|
split|spread|spring sprang sprung|stand stood|steal stole stolen|stick stuck|sting stung|stink stank stunk|stride strode|
strike struck stricken|string strung|strive strove striven|swear swore sworn|sweep swept|swell swollen|swim swam swum|
swing swung|take took taken|teach taught|tear tore torn|tell told|think thought|throw threw thrown|thrust|tread trod trodden|
understand understood|undertake undertook undertaken|wake woke woken|wear wore worn|weave wove woven|weep wept|win won|
wind wound|withdraw withdrew withdrawn|wring wrung|write wrote written|man men|woman women|child children|foot feet|
tooth teeth|mouse mice|goose geese|good better best|bad worse worst|far farther further farthest furthest|
little less least|much more most|many more most|thou thee thy thine|ye you|knife knives|wife wives|life lives|
wolf wolves|leaf leaves|half halves|self selves|thief thieves|shelf shelves"""


# Vikisözlük'te Türkçe karşılığı olmayan, ama metinlerde çok geçen kelimeler
EXTRA = {
    "of": [["edat", ["-in", "-nın", "-den (iyelik/kaynak)"]]], "to": [["edat", ["-e", "-a", "-ye doğru", "için"]]],
    "at": [["edat", ["-de", "-da", "-e (yer/zaman)"]]], "from": [["edat", ["-den", "-dan"]]],
    "could": [["fiil", ["-ebildi", "-ebilirdi"]]], "should": [["fiil", ["-meli", "-malı"]]],
    "would": [["fiil", ["-erdi", "-ecekti"]]], "might": [["fiil", ["-ebilirdi", "belki"]]],
    "without": [["edat", ["olmadan", "-sız", "-siz"]]], "cannot": [["fiil", ["-emez", "yapamaz"]]],
    "mr": [["isim", ["Bay"]]], "mrs": [["isim", ["Bayan (evli)"]]], "miss": [["isim", ["Bayan", "hanım"]], ["fiil", ["özlemek", "kaçırmak"]]],
    "don't": [["fiil", ["yapma", "-me", "-ma"]]], "doesn't": [["fiil", ["-mez", "-maz"]]], "didn't": [["fiil", ["-medi", "-madı"]]],
    "can't": [["fiil", ["-emez", "yapamaz"]]], "won't": [["fiil", ["-meyecek", "-mayacak"]]], "isn't": [["fiil", ["değil"]]],
    "aren't": [["fiil", ["değil"]]], "wasn't": [["fiil", ["değildi"]]], "weren't": [["fiil", ["değildi"]]],
    "couldn't": [["fiil", ["-emedi", "-emezdi"]]], "wouldn't": [["fiil", ["-mezdi", "-mazdı"]]], "shouldn't": [["fiil", ["-memeli"]]],
    "haven't": [["fiil", ["-medim", "-madı (henüz)"]]], "hasn't": [["fiil", ["-medi (henüz)"]]], "hadn't": [["fiil", ["-memişti"]]],
    "i'm": [["", ["ben ...-im"]]], "i'll": [["", ["ben ...-eceğim"]]], "i've": [["", ["ben ...-dim/-miş"]]], "i'd": [["", ["ben ...-erdim"]]],
    "it's": [["", ["o ...-dir", "bu"]]], "that's": [["", ["bu ...-dir", "işte"]]], "he's": [["", ["o ...-dir (erkek)"]]],
    "she's": [["", ["o ...-dir (kadın)"]]], "we're": [["", ["biz ...-iz"]]], "they're": [["", ["onlar ...-dir"]]],
    "you're": [["", ["sen/siz ...-sin"]]], "you'll": [["", ["sen ...-eceksin"]]], "let's": [["", ["haydi", "-elim"]]],
    "there's": [["", ["... var"]]], "what's": [["", ["ne ...?"]]], "o'clock": [["zarf", ["saat ... (tam)"]]],
    "de": [["edat", ["(Fransızca) -in, -den"]]], "ere": [["edat", ["-den önce (eski)"]]], "hath": [["fiil", ["-e sahip (eski)"]]],
    "thou": [["zamir", ["sen (eski)"]]], "thee": [["zamir", ["seni", "sana (eski)"]]], "thy": [["zamir", ["senin (eski)"]]],
}


def irregular_map() -> dict:
    m = {}
    for group in IRREGULAR.replace("\n", "").split("|"):
        words = group.split()
        for w in words[1:]:
            m.setdefault(w, words[0])
    return m


def candidates(w: str) -> list[str]:
    """Çekimli bir kelimenin olası kökleri, olasılık sırasıyla."""
    c = []
    if w.endswith("'s") or w.endswith("s'"):
        c.append(w[:-2])
    if w.endswith("ies") and len(w) > 4:
        c.append(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        c += [w[:-2], w[:-1]]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        c.append(w[:-1])
    if w.endswith("ied") and len(w) > 4:
        c.append(w[:-3] + "y")
    if w.endswith("ed") and len(w) > 3:
        base = w[:-2]
        c += [base, w[:-1]]
        if len(base) > 2 and base[-1] == base[-2]:
            c.append(base[:-1])
    if w.endswith("ing") and len(w) > 4:
        base = w[:-3]
        c += [base, base + "e"]
        if len(base) > 2 and base[-1] == base[-2]:
            c.append(base[:-1])
        if base.endswith("y"):
            c.append(base[:-1] + "ie")
    for suf, rep in (("iest", "y"), ("ier", "y"), ("est", ""), ("er", ""), ("est", "e"), ("er", "e")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            base = w[: -len(suf)] + rep
            c.append(base)
            if rep == "" and len(base) > 2 and base[-1] == base[-2]:
                c.append(base[:-1])
    if w.endswith("ily") and len(w) > 5:
        c.append(w[:-3] + "y")
    if w.endswith("ly") and len(w) > 4:
        c += [w[:-2], w[:-2] + "e", w[:-1] + "e"]
    if w.endswith("ness") and len(w) > 6:
        c.append(w[:-4])
    return c


def load_db() -> dict:
    if not DB.exists():
        DB.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL, headers={"User-Agent": "KitapKosku/1.0"})
        DB.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    con = sqlite3.connect(DB)
    entries = defaultdict(lambda: defaultdict(list))  # kelime → tür → [türkçe]
    rows = con.execute("SELECT lexentry, written_rep, trans_list, score FROM translation ORDER BY score DESC, importance DESC")
    for lex, rep, trans, _score in rows:
        if not rep or " " in rep.strip() or not trans:
            continue
        pos = ""
        if lex:
            m = re.match(r"eng/.+?__(.+?)__\d+", lex)
            pos = POS_TR.get(m.group(1), "") if m else ""
        key = rep.strip().lower()
        bucket = entries[key][pos]
        for t in trans.split("|"):
            t = t.strip()
            if t and not t.startswith("-") and t not in bucket and len(bucket) < 6:
                bucket.append(t)
    for rep, trans in con.execute("SELECT written_rep, trans_list FROM simple_translation"):
        key = (rep or "").strip().lower()
        if key and " " not in key and key not in entries and trans:
            entries[key][""] = [t.strip() for t in trans.split("|") if t.strip() and not t.strip().startswith("-")][:6]
    return entries


def corpus_words() -> Counter:
    cnt = Counter()
    cat = json.loads((BOOKS / "catalog.json").read_text(encoding="utf-8"))
    for b in cat:
        if b["lang"] != "en":
            continue
        with gzip.open(BOOKS / f"{b['id']}.json.gz", "rt", encoding="utf-8") as fh:
            book = json.load(fh)
        for ch in book["chapters"]:
            for p in ch["p"]:
                cnt.update(w.lower() for w in re.findall(r"[A-Za-z]+(?:['’][a-z]+)?", p.replace("’", "'")))
    return cnt


def main():
    entries = load_db()
    irr = irregular_map()
    cnt = corpus_words()
    words, forms = {}, {}

    def pack(key):
        e = entries[key]
        # Türü bilinen anlamlar önce; türü bilinmeyen liste, zaten listelenmiş kelimeleri tekrar etmesin
        out, seen = [], set()
        for pos in sorted(e, key=lambda p: (p == "", 0)):
            tr = [t for t in e[pos] if t not in seen]
            seen.update(tr)
            if tr:
                out.append([pos, tr[:5]])
        return out[:4]

    found = 0
    for w, n in cnt.items():
        if w in EXTRA:
            words[w] = EXTRA[w]
            found += n
            continue
        if w in entries:
            words[w] = pack(w)
            found += n
            continue
        cands = ([irr[w]] if w in irr else []) + candidates(w)
        for c in cands:
            if c in entries:
                words.setdefault(c, pack(c))
                forms[w] = c
                found += n
                break
    words = {k: v for k, v in words.items() if v}
    total = sum(cnt.values())
    out = BOOKS / "dict-en-tr.json.gz"
    with gzip.open(out, "wt", encoding="utf-8", compresslevel=9) as fh:
        json.dump({"w": words, "f": forms}, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(cnt)} farklı kelime, {len(words)} sözlük maddesi, {len(forms)} çekim; metin kapsaması %{100 * found / total:.1f}; "
          f"{out.stat().st_size // 1024} KB")
    missing = [w for w, n in cnt.most_common(400) if w not in words and w not in forms]
    print("Bulunamayan sık kelimeler:", missing[:60])


if __name__ == "__main__":
    main()
