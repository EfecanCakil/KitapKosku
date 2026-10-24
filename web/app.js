"use strict";
/* Kitap Köşkü arayüzü. Python tarafına window.pywebview.api ile (geliştirmede /api/* ile) ulaşır. */

// ---------- köprü ----------
let bridge = null;
async function ready() {
  if (window.pywebview?.api) return (bridge = "pv");
  await new Promise((res) => { window.addEventListener("pywebviewready", res, { once: true }); setTimeout(res, 700); });
  if (window.pywebview?.api) return (bridge = "pv");
  try { const r = await fetch("/api/library", { method: "POST", body: "[]" }); if (r.ok) return (bridge = "http"); } catch {}
  await new Promise((res) => window.addEventListener("pywebviewready", res, { once: true }));
  bridge = "pv";
}
async function call(name, ...args) {
  if (bridge === "pv") return window.pywebview.api[name](...args);
  const r = await fetch("/api/" + name, { method: "POST", body: JSON.stringify(args) });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// ---------- sabitler ----------
const GENRES = {
  turk:       { label: "Türk Edebiyatı",   c: ["#0f5257", "#1b7a7f", "#f2c66d"], orn: "tulip" },
  korku:      { label: "Korku",            c: ["#2a0d10", "#5d1a1f", "#e8c9a0"], orn: "moon" },
  polisiye:   { label: "Polisiye",         c: ["#1c2738", "#33465f", "#e5b45b"], orn: "glass" },
  macera:     { label: "Aksiyon & Macera", c: ["#23412b", "#3d6a46", "#f0a35a"], orn: "compass" },
  bilimkurgu: { label: "Bilim Kurgu",      c: ["#1d1640", "#3b2d78", "#7fe0e6"], orn: "planet" },
  klasik:     { label: "Dünya Klasikleri", c: ["#4a1622", "#7a2a3a", "#e9c983"], orn: "quill" },
  masal:      { label: "Masal & Destan",   c: ["#3b1d4a", "#6b3a7d", "#f6c5d6"], orn: "star" },
  oyku:       { label: "Öykü",             c: ["#4a3d1c", "#7a6530", "#f3dfa2"], orn: "book" },
  mizah:      { label: "Mizah",            c: ["#5a3a0f", "#8a5a1a", "#ffd166"], orn: "star" },
};
const ORDER = ["turk", "korku", "polisiye", "macera", "bilimkurgu", "klasik", "masal", "mizah", "oyku"];
const ORN = {
  moon: '<path d="M31 6a17 17 0 1 0 11 30A14 14 0 0 1 31 6z" fill="currentColor"/><circle cx="12" cy="10" r="1.3" fill="currentColor"/><circle cx="7" cy="22" r="1" fill="currentColor"/>',
  glass: '<circle cx="20" cy="20" r="11" fill="none" stroke="currentColor" stroke-width="3.5"/><path d="M28.5 28.5L41 41" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>',
  compass: '<circle cx="24" cy="24" r="17" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M24 9l4.5 15L24 39l-4.5-15z" fill="currentColor"/><path d="M9 24l15-3.5L39 24l-15 3.5z" fill="currentColor" opacity=".55"/>',
  planet: '<circle cx="24" cy="24" r="10" fill="currentColor"/><ellipse cx="24" cy="24" rx="21" ry="6.5" fill="none" stroke="currentColor" stroke-width="2.5" transform="rotate(-22 24 24)"/>',
  quill: '<path d="M40 6C24 9 14 20 11 38l3 1C17 28 22 21 30 16c-5 6-8 11-10 18 9-4 16-13 20-28z" fill="currentColor"/><path d="M8 43l6-5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>',
  tulip: '<path d="M24 30c-8 0-12-6-12-15l6 4 6-10 6 10 6-4c0 9-4 15-12 15z" fill="currentColor"/><path d="M24 30v14M24 40c-4-5-9-6-12-6 2 5 7 8 12 8M24 40c4-5 9-6 12-6-2 5-7 8-12 8" fill="none" stroke="currentColor" stroke-width="2.2"/>',
  star: '<path d="M24 5l5.6 12.2 13.4 1.5-10 9 2.8 13.1L24 34.2 12.2 40.8 15 27.7l-10-9 13.4-1.5z" fill="currentColor"/>',
  book: '<path d="M6 12c6-2 12-1 17 3v24c-5-4-11-5-17-3zM42 12c-6-2-12-1-17 3v24c5-4 11-5 17-3z" fill="currentColor"/>',
};
const MODES = { en: "İngilizce", tr: "Türkçe", both: "İkisi yan yana" };

// ---------- durum ----------
const S = {
  books: [], byId: {}, progress: {}, favorites: [], bookmarks: [], seconds: {}, settings: {}, words: [], translated: {}, mt: true,
  view: { nav: "home", genre: null, sort: "featured", q: "" }, dict: null,
};
const R = { id: null, info: null, ch: null, trans: null, mode: "orig", saveT: null, pollT: null, active: Date.now(), pending: 0 };

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nf = new Intl.NumberFormat("tr-TR");
const fold = (s) => String(s || "").toLocaleLowerCase("tr").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ı/g, "i");
const strip = (t) => String(t || "").replace(/^§[§_] /, "");

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove("show"), 2200);
}

function hash(s) { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; }
function minutes(b) { return Math.max(1, Math.round(b.words / (b.lang === "en" ? 180 : 220))); }
function duration(min) {
  if (min < 60) return `${min} dk`;
  const h = Math.floor(min / 60), m = min % 60;
  return m && h < 10 ? `${h} sa ${m} dk` : `${h} sa`;
}
function pages(b) { return Math.max(1, Math.round(b.words / 260)); }
function displayTitle(b) { return b.tr || b.title; }
function shortAuthor(a) { return (a || "").replace(/^graf\s+/i, "").replace(/\s*\(.*?\)\s*/g, "").split(/;| and /)[0].trim(); }
const isEn = (b) => b.lang === "en";

// ---------- kapak ----------
function cover(b, extra = "") {
  const g = GENRES[b.genres[0]] || GENRES.klasik;
  const h = hash(b.id);
  const [c1, c2, c3] = g.c;
  const pats = [
    `repeating-linear-gradient(135deg, ${c2} 0 2px, transparent 2px 13px)`,
    `radial-gradient(circle at 50% 118%, ${c2} 0 38%, transparent 38.5%), radial-gradient(circle at 50% 118%, transparent 0 46%, ${c2} 46% 47%, transparent 47.5%)`,
    `linear-gradient(${c2}, ${c2}) 0 72% / 100% 3px no-repeat, linear-gradient(${c2}, ${c2}) 0 75% / 100% 1px no-repeat, linear-gradient(180deg, transparent 55%, ${c2} 100%)`,
    `repeating-radial-gradient(circle at 100% 0, transparent 0 16px, ${c2} 16px 17px)`,
    `conic-gradient(from 200deg at 50% 0%, transparent 0 40deg, ${c2} 40deg 80deg, transparent 80deg)`,
    `linear-gradient(90deg, transparent 0 10%, ${c2} 10% 13%, transparent 13% 87%, ${c2} 87% 90%, transparent 90%)`,
  ];
  const title = displayTitle(b);
  const label = b.original ? "ÖZGÜN" : { ceviri: "ÇEVİRİ", derleme: "DERLEME" }[b.kind];
  const badge = label ? `<span class="badge">${label}</span>` : "";
  const lang = isEn(b) ? `EN${S.mt ? "·TR" : ""}` : "TR";
  return `<div class="cover ${extra}" style="--c1:${c1};--c3:${c3};--pat:${pats[h % pats.length]};filter:hue-rotate(${(h >> 8) % 24 - 12}deg)">
    <span class="frame"></span>${badge}<span class="lang">${lang}</span>
    <svg class="orn" viewBox="0 0 48 48">${ORN[g.orn]}</svg>
    <div class="ct ${title.length > 28 ? "long" : ""}">${esc(title)}</div>
    <div class="ca">${esc(shortAuthor(b.author))}</div></div>`;
}

function pct(id) { return S.progress[id]?.t || 0; }
function tile(b) {
  const p = pct(b.id);
  const tf = S.translated[b.id] || 0;
  let sub = p >= 0.99 ? "✓ Bitti" : shortAuthor(b.author);
  if (isEn(b) && tf >= 0.99 && p < 0.99) sub += " · Türkçesi hazır";
  return `<button class="tile" data-book="${b.id}">${cover(b)}<b>${esc(displayTitle(b))}</b><span class="sub">${esc(sub)}</span>
    ${p > 0 && p < 0.99 ? `<div class="pbar"><i style="width:${(p * 100).toFixed(1)}%"></i></div>` : ""}</button>`;
}

// ---------- kütüphane ----------
const trBooks = () => S.books.filter((b) => !isEn(b));
const enBooks = () => S.books.filter(isEn);
const readyTr = () => enBooks().filter((b) => (S.translated[b.id] || 0) >= 0.999);

// Türkçe bölümün rafları: [başlık, alt yazı, kitaplar]
function trShelves() {
  const tr = trBooks();
  return [
    ["Kitap Köşkü'ne özel öyküler", "Bu uygulama için yazılmış yeni öykü ve romanlar", tr.filter((b) => b.original)],
    ["Kitap Köşkü çevirileri", "Frankenstein'ın tam metni; Poe, O. Henry, Çehov, Grimm, Andersen ve Ezop seçkileri; elle Türkçeye çevrildi", tr.filter((b) => b.kind === "ceviri")],
    ["Halk edebiyatı", "Nasreddin Hoca, Keloğlan ve Dede Korkut, bugünün Türkçesiyle", tr.filter((b) => b.kind === "derleme")],
    ["Türk edebiyatı", "Telifi dolmuş eserler", tr.filter((b) => !b.original && !b.kind)],
    ["Türkçesi hazır dünya klasikleri", "Makine çevirisiyle önceden Türkçeye çevrildi; İngilizcesiyle yan yana da okunabilir", readyTr()],
  ].filter((s) => s[2].length);
}

function sortBooks(list) {
  const s = S.view.sort;
  const by = (f) => [...list].sort((a, b) => (f(a) < f(b) ? -1 : f(a) > f(b) ? 1 : 0));
  if (s === "title") return by((b) => fold(displayTitle(b)));
  if (s === "author") return by((b) => fold(shortAuthor(b.author).split(" ").pop()));
  if (s === "short") return by((b) => b.words);
  if (s === "long") return by((b) => -b.words);
  return list;
}

function continueList() {
  return Object.entries(S.progress)
    .filter(([id, p]) => S.byId[id] && p.t < 0.99)
    .sort((a, b) => b[1].at - a[1].at)
    .map(([id]) => S.byId[id]);
}

function contCard(b) {
  const p = S.progress[b.id];
  const left = Math.round(minutes(b) * (1 - p.t));
  const mode = isEn(b) && p.m ? ` · ${MODES[p.m] || ""}` : "";
  return `<button class="cont" data-open="${b.id}">${cover(b)}<div class="meta"><b>${esc(displayTitle(b))}</b>
    <span class="sub">${esc(shortAuthor(b.author))}${esc(mode)}</span><span class="ch">Kalan ≈ ${duration(left)}</span>
    <div class="pbar"><i style="width:${(p.t * 100).toFixed(1)}%"></i></div></div></button>`;
}

function sortSeg() {
  const o = [["featured", "Önerilen"], ["title", "Ada göre"], ["author", "Yazara göre"], ["short", "Kısadan uzuna"], ["long", "Uzundan kısaya"]];
  return `<div class="seg small" id="sortSeg">${o.map(([k, l]) => `<button data-sort="${k}" class="${S.view.sort === k ? "on" : ""}">${l}</button>`).join("")}</div>`;
}

function langHead(lang, n, note) {
  const t = lang === "tr" ? "Türkçe Kitaplar" : "İngilizce Kitaplar";
  return `<div class="lang-head ${lang}"><span class="flag">${lang.toUpperCase()}</span><div><h2>${t} <small>${n} kitap</small></h2>${note ? `<p>${note}</p>` : ""}</div>
    <button class="more" data-nav="${lang}">Tümü →</button></div>`;
}
const EN_NOTE = "Özgün dilinde okuyun; bilmediğiniz kelimenin üstüne gelince Türkçesi çıkar. Dilerseniz Türkçe ya da iki dil yan yana okuyun: çeviri bu bilgisayarda, okudukça yapılır.";

function groupGrid(list, emptyText) {
  const tr = list.filter((b) => !isEn(b)), en = list.filter(isEn);
  if (!list.length) return `<div class="empty">${emptyText}</div>`;
  return (tr.length ? `<h3 class="grp"><span class="flag tr">TR</span>Türkçe <small>${tr.length}</small></h3><div class="grid">${sortBooks(tr).map(tile).join("")}</div>` : "") +
    (en.length ? `<h3 class="grp"><span class="flag en">EN</span>İngilizce <small>${en.length}</small></h3><div class="grid">${sortBooks(en).map(tile).join("")}</div>` : "");
}

function renderLibrary() {
  const v = S.view, el = $("#content");
  $$(".sidebar nav button[data-nav]").forEach((b) => b.classList.toggle("on", b.dataset.nav === v.nav && !v.q));
  $$("#genreNav button").forEach((b) => b.classList.toggle("on", v.nav === "genre" && b.dataset.genre === v.genre && !v.q));
  $("#cntContinue").textContent = continueList().length || "";
  $("#cntFav").textContent = S.favorites.length || "";
  $("#cntBm").textContent = S.bookmarks.length || "";
  $("#cntWords").textContent = S.words.length || "";
  $("#cntTr").textContent = trBooks().length + readyTr().length;
  $("#cntEn").textContent = enBooks().length;

  if (v.q.trim()) {
    const q = fold(v.q.trim());
    const hits = S.books.filter((b) => fold([b.title, b.tr, b.author, b.desc, ...b.genres.map((g) => GENRES[g]?.label)].join(" ")).includes(q));
    el.innerHTML = `<div class="toolbar"><h2 class="sec">“${esc(v.q)}” <small>${hits.length} sonuç</small></h2>${sortSeg()}</div>` +
      groupGrid(hits, "<b>Sonuç bulunamadı</b>Başka bir kelime deneyin.");
    return;
  }
  if (v.nav === "genre") {
    const list = S.books.filter((b) => b.genres.includes(v.genre));
    el.innerHTML = `<div class="toolbar"><h2 class="sec">${GENRES[v.genre].label} <small>${list.length} kitap</small></h2>${sortSeg()}</div>` + groupGrid(list, "");
    return;
  }
  if (v.nav === "tr") {
    const shelves = trShelves();
    const n = shelves.reduce((a, s) => a + s[2].length, 0);
    el.innerHTML = `<div class="toolbar"><h2 class="sec">Türkçe Kitaplar <small>${n} kitap</small></h2>${sortSeg()}</div>` +
      shelves.map(([t, sub, list]) => `<h3 class="grp">${esc(t)} <small>${list.length} · ${esc(sub)}</small></h3><div class="grid">${sortBooks(list).map(tile).join("")}</div>`).join("");
    return;
  }
  if (v.nav === "en") {
    let html = `<div class="toolbar"><h2 class="sec">İngilizce Kitaplar <small>${enBooks().length} kitap</small></h2>${sortSeg()}</div><p class="lead">${EN_NOTE}</p>`;
    for (const g of ORDER) {
      const list = enBooks().filter((b) => b.genres[0] === g);
      if (list.length) html += `<h3 class="grp">${GENRES[g].label} <small>${list.length}</small></h3><div class="grid">${sortBooks(list).map(tile).join("")}</div>`;
    }
    el.innerHTML = html;
    return;
  }
  if (v.nav === "continue") {
    const list = continueList();
    const done = Object.keys(S.progress).filter((id) => S.byId[id] && S.progress[id].t >= 0.99).map((id) => S.byId[id]);
    el.innerHTML = `<h2 class="sec">Okumaya devam et</h2>` +
      (list.length ? `<div class="cont-row">${list.map(contCard).join("")}</div>` : `<div class="empty"><b>Henüz yarım kalan kitap yok</b>Bir kitap açın, kaldığınız yeri ben hatırlarım.</div>`) +
      (done.length ? `<h2 class="sec">Bitirdikleriniz <small>${done.length}</small></h2><div class="grid">${done.map(tile).join("")}</div>` : "");
    return;
  }
  if (v.nav === "favorites") {
    const list = S.favorites.map((id) => S.byId[id]).filter(Boolean);
    el.innerHTML = `<h2 class="sec">Favoriler <small>${list.length} kitap</small></h2>` +
      groupGrid(list, "<b>Favori listeniz boş</b>Kitap kartındaki ☆ düğmesiyle ekleyebilirsiniz.");
    return;
  }
  if (v.nav === "bookmarks") {
    const list = S.bookmarks.filter((m) => S.byId[m.b]);
    el.innerHTML = `<h2 class="sec">Yer imleri <small>${list.length}</small></h2>` + (list.length ? `<div class="bm-list">${list.map((m) => {
      const b = S.byId[m.b];
      return `<div class="bm" role="button" data-jump="${m.b}|${m.c}|${m.p}">${cover(b)}<div><b>${esc(displayTitle(b))}</b> <small style="color:var(--muted)">· ${esc(m.t || `Bölüm ${m.c + 1}`)}</small>
        <p>“${esc(m.x)}”</p></div><button class="del" data-del="${m.b}|${m.c}|${m.p}" title="Sil">✕</button></div>`;
    }).join("")}</div>` : `<div class="empty"><b>Yer imi yok</b>Okurken ❙ düğmesine ya da B tuşuna basın.</div>`);
    return;
  }
  if (v.nav === "words") {
    el.innerHTML = `<h2 class="sec">Kelimelerim <small>${S.words.length} kelime</small></h2>` + (S.words.length
      ? `<p class="lead">İngilizce okurken kelimenin üstüne gelip ☆ düğmesine bastığınız kelimeler.</p><div class="word-list">${S.words.map((w) => `
        <div class="wcard"><div class="wtop"><b>${esc(w.w)}</b>${w.l && w.l !== w.w.toLowerCase() ? `<span class="lemma">→ ${esc(w.l)}</span>` : ""}
          <button class="del" data-delword="${esc(w.w)}" title="Sil">✕</button></div>
          <div class="wtr">${esc(w.tr)}</div>${w.x ? `<p>“${esc(w.x)}”</p>` : ""}${S.byId[w.b] ? `<small>${esc(displayTitle(S.byId[w.b]))}</small>` : ""}</div>`).join("")}</div>`
      : `<div class="empty"><b>Henüz kelime kaydetmediniz</b>İngilizce bir kitapta kelimenin üstüne gelin, çıkan kutudaki ☆ ile kaydedin.</div>`);
    return;
  }

  // ana sayfa: önce Türkçe, sonra İngilizce kitaplar
  const cont = continueList().slice(0, 4);
  let html = "";
  if (cont.length) html += `<h2 class="sec">Kaldığınız yerden devam edin</h2><div class="cont-row">${cont.map(contCard).join("")}</div>`;
  else html += `<h2 class="sec">Hoş geldiniz</h2><p class="lead">${nf.format(S.books.length)} kitap bu bilgisayarda, internet gerekmeden okunmaya hazır: ${trBooks().length} Türkçe, ${enBooks().length} İngilizce. İngilizce kitapları Türkçe de okuyabilirsiniz.</p>
    <button class="btn" id="luckyBtn" style="margin-bottom:6px">🎲 Bana bir kitap seç</button>`;
  const shelves = trShelves();
  html += langHead("tr", shelves.reduce((a, s) => a + s[2].length, 0));
  for (const [t, sub, list] of shelves) html += shelf(t, list, null, `${list.length} kitap · ${sub}`);
  html += langHead("en", enBooks().length, EN_NOTE);
  for (const g of ORDER) {
    const list = enBooks().filter((b) => b.genres.includes(g));
    if (list.length) html += shelf(GENRES[g].label, list, g);
  }
  el.innerHTML = html;
}

function shelf(title, list, genre, sub) {
  return `<h2 class="sec">${esc(title)} <small>${sub ? esc(sub) : list.length + " kitap"}</small>${genre ? `<button class="more" data-genre="${genre}">Tümünü gör →</button>` : ""}</h2>
    <div class="shelf">${list.slice(0, 14).map(tile).join("")}</div>`;
}

function renderSidebar() {
  $("#genreNav").innerHTML = ORDER.map((g) => {
    const n = S.books.filter((b) => b.genres.includes(g)).length;
    return n ? `<button data-genre="${g}"><span class="dot" style="background:${GENRES[g].c[2]}"></span>${GENRES[g].label}<span class="count">${n}</span></button>` : "";
  }).join("");
  const words = S.books.reduce((a, b) => a + b.words, 0);
  const secs = Object.values(S.seconds).reduce((a, b) => a + b, 0);
  $("#sideStats").innerHTML = `${nf.format(S.books.length)} kitap · ${(words / 1e6).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} milyon kelime` +
    (secs > 60 ? `<br>Toplam okuma: ${duration(Math.round(secs / 60))}` : "") + `<br><span style="opacity:.7">İnternet bağlantısı gerekmez</span>`;
}

// ---------- kitap kartı ----------
async function openDetail(id) {
  const b = S.byId[id];
  const m = $("#detail"), card = $("#detailCard");
  const p = S.progress[id];
  const fav = S.favorites.includes(id);
  const label = p ? (p.t >= 0.99 ? "Yeniden oku" : "Okumaya devam et") : "Okumaya başla";
  const buttons = isEn(b) && S.mt
    ? `<button class="btn" data-open="${id}" data-mode="tr">Türkçe oku</button>
       <div class="btn-row"><button class="btn ghost" data-open="${id}" data-mode="en">İngilizce</button><button class="btn ghost" data-open="${id}" data-mode="both">İkisi yan yana</button></div>
       ${p ? `<button class="btn ghost" data-open="${id}">${label} (${MODES[p.m || S.settings.mode] || "İngilizce"})</button>` : ""}`
    : `<button class="btn" data-open="${id}">${label}</button>`;
  card.innerHTML = `<div class="left">${cover(b)}${buttons}
      <div class="btn-row"><button class="btn ghost" id="favBtn">${fav ? "★ Favoride" : "☆ Favorilere ekle"}</button></div>
      ${p ? `<div class="pbar"><i style="width:${(p.t * 100).toFixed(1)}%"></i></div><small style="color:var(--muted);text-align:center">%${Math.round(p.t * 100)} okundu ${p.t > 0 ? `· <a href="#" id="resetBtn" style="color:inherit">sıfırla</a>` : ""}</small>` : ""}
    </div>
    <div class="right">
      <h1>${esc(displayTitle(b))}</h1>
      ${b.tr && b.tr !== b.title ? `<div class="orig">${esc(b.title)}</div>` : ""}
      <div class="by">${esc(b.author)}${b.year ? ` · ${b.year}` : ""}</div>
      <div class="chips">${b.genres.map((g) => `<span class="chip">${GENRES[g]?.label || g}</span>`).join("")}<span class="chip">${isEn(b) ? "İngilizce" : "Türkçe"}</span></div>
      <p class="desc">${esc(b.desc)}</p>
      <div class="facts"><div><b>≈ ${nf.format(pages(b))}</b><span>sayfa</span></div><div><b>${duration(minutes(b))}</b><span>okuma süresi</span></div><div><b>${b.chapters}</b><span>bölüm</span></div></div>
      ${isEn(b) ? `<div class="note" id="trNote">Özgün dilinde, İngilizce (Project Gutenberg). ${S.mt ? "Türkçesi bu bilgisayarda makine çevirisiyle, siz okudukça hazırlanır." : ""}</div>` : ""}
      ${b.original ? `<div class="note">Bu öykü Kitap Köşkü için özel olarak yazıldı.</div>` : ""}
      ${b.kind === "ceviri" ? `<div class="note">Telifi dolmuş metinden Türkçeye çevrildi. Çeviren: ${esc(b.translator || "Kitap Köşkü")}.</div>` : ""}
      ${b.kind === "derleme" ? `<div class="note">Kuşaktan kuşağa anlatılan halk edebiyatı; Kitap Köşkü için bugünün Türkçesiyle yeniden anlatıldı.</div>` : ""}
      <div class="toc-mini"><h4>İçindekiler</h4><ol id="miniToc"><li style="color:var(--muted)">Yükleniyor…</li></ol></div>
      <small style="color:var(--muted);margin-top:16px">Kaynak: ${esc(b.source)}</small>
    </div>`;
  m.classList.remove("hidden");
  $("#favBtn").onclick = async () => {
    S.favorites = await call("toggle_favorite", id);
    $("#favBtn").textContent = S.favorites.includes(id) ? "★ Favoride" : "☆ Favorilere ekle";
    renderLibrary();
  };
  const rb = $("#resetBtn");
  if (rb) rb.onclick = async (e) => { e.preventDefault(); await call("reset_progress", id); delete S.progress[id]; openDetail(id); renderLibrary(); };
  const info = await call("book_info", id);
  if (m.classList.contains("hidden")) return;
  const cur = p?.c ?? -1;
  const show = info.toc.slice(0, 60);
  $("#miniToc").innerHTML = show.map((c, i) => `<li class="${i < cur ? "done" : ""}"><button data-open="${id}" data-ch="${i}">${esc(c.t)}</button></li>`).join("") +
    (info.toc.length > show.length ? `<li style="color:var(--muted)">… ve ${info.toc.length - show.length} bölüm daha</li>` : "");
  if (isEn(b) && S.mt) detailTranslation(id);
}

async function detailTranslation(id) {
  const note = $("#trNote");
  if (!note || $("#detail").classList.contains("hidden")) return;
  const pr = await call("translation_progress", id);
  if (pr.error) { note.textContent = "Türkçe çeviri kullanılamıyor: " + pr.error; return; }
  const pc = Math.floor(pr.f * 100);
  S.translated[id] = pr.f;
  note.innerHTML = pr.f >= 0.999
    ? "Özgün dilinde, İngilizce. <b>Türkçe çevirisi tamamen hazır.</b> Makine çevirisidir; yer yer hatalı olabilir."
    : `Özgün dilinde, İngilizce. Türkçe çeviri: <b>%${pc} hazır.</b> Kalan bölümler siz okudukça çevrilir.
       ${pr.queued ? `<span class="spin"></span> Arka planda çevriliyor (kalan ≈ ${duration(Math.max(1, Math.round(pr.eta / 60)))})` :
         `<button class="linkbtn" id="trAll">Tamamını şimdi çevir (≈ ${duration(Math.max(1, Math.round(pr.eta / 60)))})</button>`}`;
  const btn = $("#trAll");
  if (btn) btn.onclick = async () => { await call("translate_book", id); toast("Kitap arka planda çevriliyor"); detailTranslation(id); };
  if (pr.queued) setTimeout(() => detailTranslation(id), 4000);
}
function closeDetail() { $("#detail").classList.add("hidden"); }

// ---------- okuyucu ----------
function applySettings() {
  const s = S.settings, page = $("#page");
  document.documentElement.dataset.theme = s.theme;
  page.style.setProperty("--size", s.size + "px");
  page.style.setProperty("--line-h", s.line);
  page.style.setProperty("--width", s.width + "px");
  page.classList.toggle("font-book", s.font === "book");
  page.classList.toggle("font-sans", s.font === "sans");
  page.classList.toggle("justify", s.align === "justify");
  $("#vSize").textContent = s.size + " px";
  $("#vLine").textContent = Number(s.line).toFixed(2);
  $("#vWidth").textContent = s.width + " px";
  $$("#themePick button").forEach((b) => b.classList.toggle("on", b.dataset.theme === s.theme));
  $$("#fontPick button").forEach((b) => b.classList.toggle("on", b.dataset.font === s.font));
  $$("#alignPick button").forEach((b) => b.classList.toggle("on", b.dataset.align === s.align));
  $$("#hoverPick button").forEach((b) => b.classList.toggle("on", (b.dataset.hover === "1") === !!s.hover));
}
let setT;
function setSetting(k, v) {
  S.settings[k] = v;
  const sc = $("#rScroll");
  const anchor = R.ch && sc.scrollTop > 120 ? topPara() : null;
  applySettings();
  if (anchor != null) scrollToPara(anchor, false);
  clearTimeout(setT);
  setT = setTimeout(() => call("save_settings", S.settings), 400);
}

async function openBook(id, ch, para, mode) {
  closeDetail();
  const b = S.byId[id];
  R.id = id;
  R.info = await call("book_info", id);
  const p = S.progress[id];
  R.mode = isEn(b) ? (mode || (ch == null && p?.m) || S.settings.mode || "en") : "orig";
  if (isEn(b) && !S.mt) R.mode = "en";
  if (isEn(b) && mode) setSetting("mode", mode);
  if (isEn(b) && !S.dict && S.settings.hover) call("dictionary").then((d) => (S.dict = d));
  $("#rBook").textContent = displayTitle(b);
  $("#modeSeg").classList.toggle("hidden", !isEn(b) || !S.mt);
  $("#hoverRow").classList.toggle("hidden", !isEn(b));
  $("#libraryView").classList.add("hidden");
  $("#readerView").classList.remove("hidden");
  if (ch == null) {
    if (p && p.t < 0.99) { ch = p.c; para = p.p; }
    else { ch = 0; para = 0; }
  }
  buildToc();
  await loadChapter(ch, para || 0);
}

function paraClass(t, i, firstDone) {
  if (t.includes("\n")) return "poem";
  if (t.length <= 4 || /^[\s*·•.⁂✦❧🙝🙟—–\-_=~]+$/u.test(t)) return "center";
  if (/^([IVXLC]{1,7}|\d{1,3})\.?$/.test(t)) return "sub";
  if (!firstDone && t.length > 140 && /^[\p{L}]/u.test(t)) return "first";
  return "";
}

// Bir paragrafın HTML'i: işaretli paragraflar (§§ ara başlık, §_ italik) ve sınıflar dahil
function paraHtml(t, k, extra, state) {
  if (t.startsWith("§§ ")) return `<p data-i="${k}" class="sub ${extra}">${esc(t.slice(3))}</p>`;
  if (t.startsWith("§_ ")) return `<p data-i="${k}" class="em ${extra}">${esc(t.slice(3))}</p>`;
  let cls = paraClass(t, k, state.first);
  if (cls === "first" || (!state.first && t.length > 140)) state.first = true;
  if (state.noDrop && cls === "first") cls = "";
  return `<p data-i="${k}" class="${cls} ${extra}">${esc(t)}</p>`;
}

function renderChapter() {
  const c = R.ch, tr = R.trans, mode = R.mode;
  const page = $("#page");
  page.classList.toggle("bi", mode === "both");
  page.classList.toggle("en-mode", mode === "en" || mode === "both");
  let body = "";
  if (mode === "both") {
    const s1 = { first: false, noDrop: true }, s2 = { first: false, noDrop: true };
    body = c.p.map((t, k) => {
      const tt = tr?.p[k];
      const right = tt != null ? paraHtml(tt, k, "dst", s2) : `<p class="dst pending">çevriliyor…</p>`;
      return `<div class="pair" data-i="${k}">${paraHtml(t, k, "src en-text", s1).replace(` data-i="${k}"`, "")}${right.replace(` data-i="${k}"`, "")}</div>`;
    }).join("");
  } else if (mode === "tr") {
    const st = { first: false };
    body = c.p.map((t, k) => {
      const tt = tr?.p[k];
      return tt != null ? paraHtml(tt, k, "dst", st) : `<p data-i="${k}" class="pending" title="Çevriliyor">${esc(strip(t))}</p>`;
    }).join("");
  } else {
    const st = { first: false };
    body = c.p.map((t, k) => paraHtml(t, k, R.mode === "en" ? "en-text" : "", st)).join("");
  }
  const title = mode === "tr" || mode === "both" ? (tr?.t || c.t) : c.t;
  const nextT = R.info.toc[c.i + 1];
  const end = nextT
    ? `<div class="end"><small>Bölüm sonu</small><button class="btn" data-go="${c.i + 1}">Sonraki bölüm ›</button></div>`
    : `<div class="end"><small>Kitabın sonu</small><div style="font:600 1.2em 'Sitka Heading',Georgia,serif;margin-top:8px">Tebrikler, bu kitabı bitirdiniz!</div><button class="btn" id="finishBtn">Kütüphaneye dön</button></div>`;
  const note = mode === "tr" || mode === "both"
    ? `<div class="mt-note">${tr?.error ? "Çeviri yapılamadı: " + esc(tr.error) : `Makine çevirisi · yer yer hatalı olabilir${mode === "tr" ? " · Bir paragrafa tıklayınca İngilizcesi görünür" : " · Soldaki kelimelerin üstüne gelince sözlük açılır"}`}
       ${tr && !tr.done && !tr.error ? `<span class="spin"></span> <span id="trCount"></span>` : ""}</div>` : "";
  const group = mode === "tr" && tr?.g ? tr.g : c.g;
  page.innerHTML = (group ? `<div class="group">${esc(group)}</div>` : "") + `<h1>${esc(title)}</h1>` +
    (mode === "both" && tr?.t ? `<div class="h1-sub">${esc(c.t)}</div>` : "") + `<div class="orn">✦ ✦ ✦</div>` + note + body + end;
  $("#rChap").textContent = `${title} · ${c.i + 1}/${c.n}`;
  $$("#modeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  updateTrCount();
  markBookmarks();
}

function updateTrCount() {
  const el = $("#trCount");
  if (el && R.trans) {
    const n = R.trans.p.filter((x) => x != null).length;
    el.textContent = `Çevriliyor: ${n}/${R.trans.p.length} paragraf`;
  }
}

async function loadChapter(i, para = 0, flash = false) {
  clearTimeout(R.pollT);
  hideTip(true);
  const c = await call("chapter", R.id, i);
  R.ch = c;
  R.trans = null;
  if (R.mode === "tr" || R.mode === "both") R.trans = await call("translation", R.id, c.i, para);
  renderChapter();
  $("#rPrev").disabled = c.i === 0;
  $("#rNext").disabled = c.i >= c.n - 1;
  $$(".toc-i").forEach((el) => el.classList.toggle("cur", +el.dataset.ch === c.i));
  if (para > 0) scrollToPara(para, flash); else $("#rScroll").scrollTop = 0;
  updateProgress(true);
  schedulePoll();
}

// Çeviri sürerken birkaç saniyede bir yeni paragrafları getirip yerlerine koyar (okunan yer kaymaz)
function schedulePoll() {
  clearTimeout(R.pollT);
  if (!R.trans || R.trans.done || R.trans.error || R.mode === "en") return;
  const id = R.id, ch = R.ch.i;
  R.pollT = setTimeout(async () => {
    if (R.id !== id || R.ch?.i !== ch || R.mode === "en") return;
    const fresh = await call("translation", id, ch, topPara() ?? 0);
    if (R.id !== id || R.ch?.i !== ch) return;
    const changed = fresh.p.some((x, k) => x !== R.trans.p[k]) || fresh.t !== R.trans.t;
    if (changed) {
      const anchor = topPara(), sc = $("#rScroll");
      const el = anchor != null ? $(`#page [data-i="${anchor}"]`) : null;
      const off = el ? el.offsetTop - sc.scrollTop : 0;
      R.trans = fresh;
      renderChapter();
      const el2 = anchor != null ? $(`#page [data-i="${anchor}"]`) : null;
      if (el2) sc.scrollTop = el2.offsetTop - off;
    } else R.trans = fresh;
    schedulePoll();
  }, R.trans.p.some((x) => x != null) ? 2500 : 1200);
}

async function setMode(mode) {
  if (!R.ch || mode === R.mode) return;
  const anchor = topPara() ?? 0;
  R.mode = mode;
  setSetting("mode", mode);
  hideTip(true);
  if ((mode === "tr" || mode === "both") && !R.trans) R.trans = await call("translation", R.id, R.ch.i, anchor);
  if (mode !== "en" && !S.dict && S.settings.hover) call("dictionary").then((d) => (S.dict = d));
  renderChapter();
  scrollToPara(anchor, false);
  updateProgress(true);
  schedulePoll();
}

function markBookmarks() {
  const set = new Set(S.bookmarks.filter((m) => m.b === R.id && m.c === R.ch?.i).map((m) => m.p));
  $$("#page [data-i]").forEach((p) => p.classList.toggle("marked", set.has(+p.dataset.i)));
}

function scrollToPara(i, flash) {
  const el = $(`#page [data-i="${i}"]`);
  if (!el) return;
  $("#rScroll").scrollTop = el.offsetTop - 40;
  if (flash) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
}

function topPara() {
  const sc = $("#rScroll");
  const ps = $$("#page [data-i]");
  if (!ps.length) return null;
  const y = sc.scrollTop + 60;
  let lo = 0, hi = ps.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (ps[mid].offsetTop <= y) lo = mid; else hi = mid - 1;
  }
  return +ps[lo].dataset.i;
}

function updateProgress(immediate) {
  if (!R.ch) return;
  const sc = $("#rScroll");
  const max = sc.scrollHeight - sc.clientHeight;
  const frac = max > 0 ? Math.min(1, sc.scrollTop / max) : 1;
  const toc = R.info.toc;
  const total = toc.reduce((a, c) => a + c.w, 0) || 1;
  const before = toc.slice(0, R.ch.i).reduce((a, c) => a + c.w, 0);
  const t = Math.min(1, (before + frac * R.ch.w) / total);
  $("#rBar").style.width = (t * 100).toFixed(2) + "%";
  const b = S.byId[R.id];
  const left = Math.round(minutes(b) * (1 - t));
  $("#rPct").textContent = `%${Math.floor(t * 100)} · kalan ≈ ${duration(left)}`;
  const save = () => {
    const p = topPara() ?? 0;
    const m = isEn(b) ? R.mode : undefined;
    S.progress[R.id] = { c: R.ch.i, p, f: frac, t, at: Math.floor(Date.now() / 1000), m };
    call("save_progress", R.id, R.ch.i, p, frac, t, m || "");
  };
  clearTimeout(R.saveT);
  R.saveT = setTimeout(save, immediate ? 50 : 700);
}

function closeReader() {
  clearTimeout(R.saveT);
  clearTimeout(R.pollT);
  hideTip(true);
  if (R.ch) {
    const p = topPara() ?? 0;
    const prev = S.progress[R.id];
    if (prev) { prev.p = p; call("save_progress", R.id, R.ch.i, p, prev.f, prev.t, prev.m || ""); }
  }
  flushTime();
  closePanels();
  $("#readerView").classList.add("hidden");
  $("#libraryView").classList.remove("hidden");
  R.id = null; R.ch = null; R.trans = null;
  if (document.fullscreenElement) document.exitFullscreen();
  call("library").then((lib) => { S.translated = lib.translated; renderLibrary(); });
  renderSidebar();
  renderLibrary();
}

function buildToc() {
  let g = null, html = "";
  const cur = R.ch?.i ?? -1;
  R.info.toc.forEach((c, i) => {
    if (c.g && c.g !== g) { g = c.g; html += `<div class="toc-g">${esc(g)}</div>`; }
    html += `<button class="toc-i ${i === cur ? "cur" : ""}" data-ch="${i}"><span>${esc(c.t)}</span><small>${duration(Math.max(1, Math.round(c.w / (R.info.lang === "en" ? 180 : 220))))}</small></button>`;
  });
  $("#tocList").innerHTML = html;
}

function closePanels() {
  $$(".panel").forEach((p) => p.classList.remove("open"));
  $("#fontPop").classList.remove("open");
}
function togglePanel(id) {
  const el = $(id), open = !el.classList.contains("open");
  closePanels();
  if (open) {
    el.classList.add("open");
    if (id === "#tocPanel") $(".toc-i.cur")?.scrollIntoView({ block: "center" });
    if (id === "#searchPanel") setTimeout(() => $("#rq").focus({ preventScroll: true }), 230);
  }
}

let searchT;
async function bookSearch(q) {
  const list = $("#searchList");
  if (q.trim().length < 2) { list.innerHTML = `<div class="panel-note">En az iki harf yazın.</div>`; return; }
  const hits = await call("search", R.id, q);
  list.innerHTML = hits.length
    ? `<div class="panel-note">${hits.length >= 150 ? "150+" : hits.length} sonuç</div>` + hits.map((h) => `<button class="hit" data-c="${h.c}" data-p="${h.p}"><small>${esc(h.t)}</small>${esc(h.pre)}<mark>${esc(h.hit)}</mark>${esc(h.post)}</button>`).join("")
    : `<div class="panel-note">Bulunamadı.</div>`;
}

async function addBookmark() {
  if (!R.ch) return;
  const p = topPara() ?? 0;
  const exists = S.bookmarks.some((m) => m.b === R.id && m.c === R.ch.i && m.p === p);
  if (exists) {
    S.bookmarks = await call("remove_bookmark", R.id, R.ch.i, p);
    toast("Yer imi kaldırıldı");
  } else {
    const text = strip(R.mode === "tr" && R.trans?.p[p] ? R.trans.p[p] : R.ch.p[p]);
    S.bookmarks = await call("add_bookmark", R.id, R.ch.i, p, text, R.mode === "tr" && R.trans?.t ? R.trans.t : R.ch.t);
    toast("Yer imi eklendi");
  }
  markBookmarks();
}

// ---------- kelime ipucu (İngilizce metinde) ----------
const TIP = { word: null, range: null, pinned: false, timer: null, mt: {} };
const POS_ORDER = ["fiil", "isim", "sıfat", "zarf"];

function lookup(raw) {
  const d = S.dict;
  if (!d) return null;
  let w = raw.toLowerCase().replace(/’/g, "'").replace(/^'+|'+$/g, "");
  const tries = [w];
  if (w.endsWith("'s")) tries.push(w.slice(0, -2));
  if (w.includes("-")) tries.push(...w.split("-").filter((x) => x.length > 2));
  for (const t of tries) {
    if (d.w[t]) return { w: raw, l: t, s: d.w[t] };
    const f = d.f[t];
    if (f && d.w[f]) return { w: raw, l: f, s: d.w[f] };
  }
  return { w: raw, l: w, s: null };
}

function wordAt(x, y) {
  const r = document.caretRangeFromPoint?.(x, y);
  if (!r || r.startContainer.nodeType !== 3) return null;
  const host = r.startContainer.parentElement?.closest(".en-text");
  if (!host || !$("#page").contains(host)) return null;
  const text = r.startContainer.data, i = r.startOffset;
  const isW = (ch) => /[A-Za-z'’\-]/.test(ch || "");
  let a = i, b = i;
  while (a > 0 && isW(text[a - 1])) a--;
  while (b < text.length && isW(text[b])) b++;
  while (a < b && /['’\-]/.test(text[a])) a++;
  while (b > a && /['’\-]/.test(text[b - 1])) b--;
  if (b - a < 2) return null;
  const range = document.createRange();
  range.setStart(r.startContainer, a);
  range.setEnd(r.startContainer, b);
  const rect = range.getBoundingClientRect();
  if (x < rect.left - 2 || x > rect.right + 2 || y < rect.top - 2 || y > rect.bottom + 2) return null;
  return { word: text.slice(a, b), range, rect, host, offset: a };
}

function sentenceAround(host, word) {
  const t = host.textContent;
  const i = t.indexOf(word);
  if (i < 0) return "";
  const a = Math.max(t.lastIndexOf(". ", i), t.lastIndexOf("! ", i), t.lastIndexOf("? ", i));
  let b = t.slice(i).search(/[.!?](\s|$)/);
  b = b < 0 ? t.length : i + b + 1;
  return t.slice(a < 0 ? 0 : a + 2, b).trim().slice(0, 220);
}

function showTip(hit) {
  const tip = $("#wordTip");
  const e = lookup(hit.word);
  if (!e) return;
  TIP.word = hit.word; TIP.range = hit.range; TIP.entry = e; TIP.host = hit.host;
  try { CSS.highlights?.set("kelime", new Highlight(hit.range)); } catch {}
  const saved = S.words.some((w) => w.w.toLowerCase() === hit.word.toLowerCase());
  let body;
  if (e.s) {
    const senses = [...e.s].sort((a, b) => (POS_ORDER.indexOf(a[0]) + 99) % 99 - (POS_ORDER.indexOf(b[0]) + 99) % 99);
    body = senses.map(([pos, tr]) => `<div class="sense">${pos ? `<i>${esc(pos)}</i>` : ""}${esc(tr.join(", "))}</div>`).join("");
  } else {
    const m = TIP.mt[e.l];
    body = `<div class="sense muted">${m === undefined ? '<span class="spin"></span> Sözlükte yok, çevriliyor…' : m ? `<i>makine çevirisi</i>${esc(m)}` : "Sözlükte bulunamadı."}</div>`;
    if (m === undefined && S.mt) {
      call("translate_word", e.l).then((t) => { TIP.mt[e.l] = t || ""; if (TIP.word === hit.word) showTip(hit); });
    }
  }
  tip.innerHTML = `<div class="tip-head"><b>${esc(hit.word)}</b>${e.l !== hit.word.toLowerCase() ? `<span class="lemma">→ ${esc(e.l)}</span>` : ""}
    <button class="tip-save ${saved ? "on" : ""}" title="Kelimelerime ekle">${saved ? "★" : "☆"}</button></div>${body}
    ${TIP.pinned ? "" : '<div class="tip-hint">Tıklayınca sabitlenir</div>'}`;
  tip.classList.add("show");
  tip.classList.toggle("pinned", TIP.pinned);
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  let left = Math.min(window.innerWidth - tw - 10, Math.max(10, hit.rect.left + hit.rect.width / 2 - tw / 2));
  let top = hit.rect.top - th - 10;
  if (top < 60) top = hit.rect.bottom + 10;
  tip.style.left = left + "px";
  tip.style.top = top + "px";
  tip.querySelector(".tip-save").onclick = (ev) => { ev.stopPropagation(); saveWord(); };
}

function hideTip(force) {
  if (TIP.pinned && !force) return;
  TIP.pinned = false; TIP.word = null;
  $("#wordTip").classList.remove("show", "pinned");
  try { CSS.highlights?.delete("kelime"); } catch {}
}

async function saveWord() {
  const e = TIP.entry;
  if (!e) return;
  const exists = S.words.some((w) => w.w.toLowerCase() === e.w.toLowerCase());
  if (exists) {
    S.words = await call("remove_word", e.w);
    toast("Kelime listeden çıkarıldı");
  } else {
    if (!e.s && TIP.mt[e.l] === undefined && S.mt) TIP.mt[e.l] = (await call("translate_word", e.l)) || "";
    const tr = e.s ? e.s.map(([pos, t]) => (pos ? pos + ": " : "") + t.slice(0, 3).join(", ")).join(" · ") : (TIP.mt[e.l] || "");
    S.words = await call("save_word", { w: e.w, l: e.l, tr, b: R.id, x: TIP.host ? sentenceAround(TIP.host, e.w) : "" });
    toast("Kelimelerime eklendi");
  }
  const btn = $("#wordTip .tip-save");
  if (btn) { const on = !exists; btn.classList.toggle("on", on); btn.textContent = on ? "★" : "☆"; }
}

function bindTips() {
  const page = $("#page");
  page.addEventListener("mousemove", (ev) => {
    if (!S.settings.hover || TIP.pinned || !page.classList.contains("en-mode")) return;
    clearTimeout(TIP.timer);
    const { clientX: x, clientY: y } = ev;
    TIP.timer = setTimeout(() => {
      const hit = wordAt(x, y);
      if (!hit) return hideTip();
      if (hit.word !== TIP.word || !$("#wordTip").classList.contains("show")) showTip(hit);
    }, 160);
  });
  page.addEventListener("mouseleave", () => { clearTimeout(TIP.timer); hideTip(); });
  page.addEventListener("click", (ev) => {
    if (window.getSelection()?.toString()) return;
    // Türkçe okurken paragrafa tıklamak İngilizcesini gösterir/gizler
    if (R.mode === "tr") {
      const p = ev.target.closest("p[data-i]");
      if (p && !p.classList.contains("pending")) return toggleSource(p);
    }
    if (!S.settings.hover || !page.classList.contains("en-mode")) return;
    const hit = wordAt(ev.clientX, ev.clientY);
    if (hit) { TIP.pinned = true; showTip(hit); } else hideTip(true);
  });
  $("#rScroll").addEventListener("scroll", () => hideTip(true), { passive: true });
  document.addEventListener("click", (ev) => { if (TIP.pinned && !ev.target.closest("#wordTip,#page")) hideTip(true); });
}

function toggleSource(p) {
  const next = p.nextElementSibling;
  if (next?.classList.contains("src-peek")) return next.remove();
  const k = +p.dataset.i;
  p.insertAdjacentHTML("afterend", `<p class="src-peek en-text">${esc(strip(R.ch.p[k]))}</p>`);
}

// okuma süresi: pencere görünürken ve son 2 dakikada etkileşim varken sayılır
setInterval(() => {
  if (R.id && document.visibilityState === "visible" && Date.now() - R.active < 120000) {
    R.pending += 15;
    if (R.pending >= 60) flushTime();
  }
}, 15000);
function flushTime() {
  if (R.id && R.pending) {
    S.seconds[R.id] = (S.seconds[R.id] || 0) + R.pending;
    call("add_time", R.id, R.pending);
  }
  R.pending = 0;
}

// ---------- olaylar ----------
function bind() {
  document.addEventListener("click", async (e) => {
    const t = e.target.closest("[data-book],[data-open],[data-genre],[data-nav],[data-sort],[data-jump],[data-del],[data-delword],[data-go],[data-ch],[data-theme],[data-font],[data-align],[data-step],[data-mode],[data-hover],.hit,#luckyBtn,#finishBtn");
    if (!t) {
      if (e.target.id === "detail") closeDetail();
      if (!e.target.closest(".panel,.pop,.rtools")) closePanels();
      return;
    }
    if (t.id === "luckyBtn") {
      const list = S.books.filter((b) => !S.progress[b.id]);
      const b = list[Math.floor(Math.random() * list.length)];
      if (b) openDetail(b.id);
      return;
    }
    if (t.id === "finishBtn") return closeReader();
    if (t.matches(".hit")) { closePanels(); return loadChapter(+t.dataset.c, +t.dataset.p, true); }
    if (t.dataset.del) {
      e.stopPropagation();
      const [b, c, p] = t.dataset.del.split("|");
      S.bookmarks = await call("remove_bookmark", b, +c, +p);
      return renderLibrary();
    }
    if (t.dataset.delword) { S.words = await call("remove_word", t.dataset.delword); return renderLibrary(); }
    if (t.dataset.jump) { const [b, c, p] = t.dataset.jump.split("|"); return openBook(b, +c, +p); }
    if (t.dataset.open) return openBook(t.dataset.open, t.dataset.ch != null ? +t.dataset.ch : undefined, undefined, t.dataset.mode);
    if (t.dataset.book) return openDetail(t.dataset.book);
    if (t.dataset.go) return loadChapter(+t.dataset.go);
    if (t.dataset.ch != null && t.classList.contains("toc-i")) { closePanels(); return loadChapter(+t.dataset.ch); }
    if (t.dataset.mode && t.closest("#modeSeg")) return setMode(t.dataset.mode);
    if (t.dataset.genre) { S.view = { ...S.view, nav: "genre", genre: t.dataset.genre, q: "" }; $("#q").value = ""; $("#main").scrollTop = 0; return renderLibrary(); }
    if (t.dataset.nav) { S.view = { ...S.view, nav: t.dataset.nav, q: "" }; $("#q").value = ""; $("#main").scrollTop = 0; return renderLibrary(); }
    if (t.dataset.sort) { S.view.sort = t.dataset.sort; return renderLibrary(); }
    if (t.dataset.theme) return setSetting("theme", t.dataset.theme);
    if (t.dataset.font) return setSetting("font", t.dataset.font);
    if (t.dataset.align) return setSetting("align", t.dataset.align);
    if (t.dataset.hover) {
      setSetting("hover", t.dataset.hover === "1");
      if (S.settings.hover && !S.dict) S.dict = await call("dictionary");
      if (!S.settings.hover) hideTip(true);
      return;
    }
    if (t.dataset.step) {
      const [k, d] = t.dataset.step.split(":");
      const lim = { size: [14, 34], line: [1.2, 2.4], width: [480, 1100] }[k];
      const v = Math.round(Math.min(lim[1], Math.max(lim[0], +S.settings[k] + +d)) * 100) / 100;
      return setSetting(k, v);
    }
  });

  $("#q").addEventListener("input", (e) => { S.view.q = e.target.value; renderLibrary(); });
  $("#themeBtn").onclick = () => {
    const order = ["sepya", "acik", "koyu", "gece"];
    setSetting("theme", order[(order.indexOf(S.settings.theme) + 1) % order.length]);
  };
  $("#rBack").onclick = closeReader;
  $("#rPrev").onclick = () => R.ch && R.ch.i > 0 && loadChapter(R.ch.i - 1);
  $("#rNext").onclick = () => R.ch && R.ch.i < R.ch.n - 1 && loadChapter(R.ch.i + 1);
  $("#rTocBtn").onclick = (e) => { e.stopPropagation(); togglePanel("#tocPanel"); };
  $("#rSearchBtn").onclick = (e) => { e.stopPropagation(); togglePanel("#searchPanel"); };
  $("#rFontBtn").onclick = (e) => { e.stopPropagation(); const o = !$("#fontPop").classList.contains("open"); closePanels(); $("#fontPop").classList.toggle("open", o); };
  $("#rMarkBtn").onclick = addBookmark;
  $("#rFullBtn").onclick = toggleFull;
  $$(".panel .x").forEach((x) => (x.onclick = closePanels));
  $("#rq").addEventListener("input", (e) => { clearTimeout(searchT); searchT = setTimeout(() => bookSearch(e.target.value), 250); });
  $("#rScroll").addEventListener("scroll", () => { R.active = Date.now(); updateProgress(false); }, { passive: true });
  ["mousemove", "keydown", "wheel"].forEach((ev) => document.addEventListener(ev, () => (R.active = Date.now()), { passive: true }));
  bindTips();

  document.addEventListener("keydown", (e) => {
    const typing = /INPUT|TEXTAREA/.test(document.activeElement?.tagName);
    const reading = !$("#readerView").classList.contains("hidden");
    if (e.key === "Escape") {
      if (typing) { document.activeElement.blur(); }
      if (TIP.word) return hideTip(true);
      if ($(".panel.open,.pop.open")) return closePanels();
      if (!$("#detail").classList.contains("hidden")) return closeDetail();
      if (reading && !document.fullscreenElement) return closeReader();
      return;
    }
    if (reading && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f") { e.preventDefault(); return togglePanel("#searchPanel"); }
    if (typing) return;
    if (!reading) {
      if (e.key === "/") { e.preventDefault(); $("#q").focus(); }
      return;
    }
    const sc = $("#rScroll");
    if (e.key === "ArrowRight" && !e.shiftKey) $("#rNext").click();
    else if (e.key === "ArrowLeft") $("#rPrev").click();
    else if (e.key === "b" || e.key === "B") addBookmark();
    else if (e.key === "f" || e.key === "F") toggleFull();
    else if (e.key === "t" || e.key === "T") togglePanel("#tocPanel");
    else if (e.key === "l" || e.key === "L") { if (!$("#modeSeg").classList.contains("hidden")) setMode({ en: "tr", tr: "both", both: "en" }[R.mode]); }
    else if (e.key === " " && !e.shiftKey && sc.scrollTop + sc.clientHeight >= sc.scrollHeight - 4 && R.ch.i < R.ch.n - 1) { e.preventDefault(); $("#rNext").click(); }
    else if (e.key === "PageDown" || (e.key === " " && !e.shiftKey)) { e.preventDefault(); sc.scrollBy({ top: sc.clientHeight - 80 }); }
    else if (e.key === "PageUp" || (e.key === " " && e.shiftKey)) { e.preventDefault(); sc.scrollBy({ top: -(sc.clientHeight - 80) }); }
    else if (e.key === "+" || e.key === "=") setSetting("size", Math.min(34, S.settings.size + 1));
    else if (e.key === "-") setSetting("size", Math.max(14, S.settings.size - 1));
  });
  document.addEventListener("fullscreenchange", () => $("#readerView").classList.toggle("zen", !!document.fullscreenElement));
  window.addEventListener("beforeunload", () => { flushTime(); });
}

function toggleFull() {
  if (document.fullscreenElement) document.exitFullscreen();
  else $("#readerView").requestFullscreen?.().catch(() => {});
}

// ---------- başlat ----------
(async function start() {
  await ready();
  const lib = await call("library");
  Object.assign(S, lib);
  S.byId = Object.fromEntries(S.books.map((b) => [b.id, b]));
  for (const m of S.bookmarks) m.t = m.t || "";
  applySettings();
  renderSidebar();
  bind();
  renderLibrary();
})();
