import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const plan = JSON.parse(
  await fs.readFile(path.join(root, "threads-content-plan.json"), "utf8"),
);
const items = plan.items ?? [];

const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const published = items.filter((item) => item.status === "published").length;
const queued = items.length - published;
const replies = items.reduce((sum, item) => sum + (item.replies?.length ?? 0), 0);
const photos = items.filter((item) => item.media_type === "IMAGE").length;
const days = new Set(items.map((item) => item.date)).size;

const cards = items
  .map((item) => {
    const isLive = item.status === "published";
    const image = item.asset
      ? `<img loading="lazy" src="/${esc(item.asset)}" alt="${esc(item.alt_text || item.topic)}">`
      : `<div class="text-cover"><span>${esc(item.session)}</span><strong>DAY ${String(item.day).padStart(3, "0")}</strong></div>`;
    const liveLink = item.threads_url
      ? `<a class="open" href="${esc(item.threads_url)}" target="_blank" rel="noreferrer">Lihat di Threads ↗</a>`
      : "";
    const replyList = (item.replies ?? [])
      .map((reply) => `<li>${esc(reply)}</li>`)
      .join("");
    const replyBlock = replyList
      ? `<details><summary>${item.replies.length} sambungan</summary><ol>${replyList}</ol></details>`
      : "";
    const search = esc(`${item.id} ${item.topic} ${item.text} ${item.date}`).toLowerCase();

    return `<article class="card" data-status="${isLive ? "live" : "queued"}" data-search="${search}">
      <div class="cover">${image}<span class="badge ${isLive ? "live" : "queued"}">${isLive ? "LIVE" : "TERJADWAL"}</span></div>
      <div class="body">
        <div class="eyebrow">${esc(item.id)} · ${esc(item.date)} · ${esc(item.time_wib)} WIB</div>
        <h2>${esc(item.topic)}</h2>
        <p class="copy">${esc(item.text)}</p>
        ${replyBlock}
        ${liveLink}
      </div>
    </article>`;
  })
  .join("\n");

const html = `<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Dashboard kampanye Threads Arga Tirta selama 100 hari.">
  <title>Arga Tirta · Threads 100 Hari</title>
  <style>
    :root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#eef8fa;background:#031014;--cyan:#46d3df;--yellow:#f7c934;--panel:#081b21;--line:#183a42;--muted:#9bb7bd}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(circle at 75% 0,#0d3b45 0,transparent 34rem),#031014;min-height:100vh}.wrap{width:min(1440px,calc(100% - 32px));margin:auto}header{padding:54px 0 30px;border-top:5px solid var(--cyan)}.brand{display:flex;justify-content:space-between;gap:24px;align-items:start}.kicker{font-size:12px;letter-spacing:.18em;color:var(--cyan);font-weight:900;text-transform:uppercase}h1{font-size:clamp(44px,8vw,112px);line-height:.84;letter-spacing:-.065em;margin:18px 0 24px;text-transform:uppercase;max-width:950px}h1 em{font-style:normal;color:var(--yellow)}.intro{max-width:760px;color:#b7ccd0;font-size:17px;line-height:1.65}.profile{display:inline-flex;margin-top:12px;color:#031014;background:var(--yellow);padding:11px 15px;border-radius:999px;text-decoration:none;font-weight:900}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:32px 0}.stat{background:linear-gradient(145deg,#0c252c,#07171c);border:1px solid var(--line);border-radius:15px;padding:18px}.stat strong{font-size:30px;display:block}.stat span{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}.toolbar{position:sticky;top:0;z-index:10;padding:12px 0;background:rgba(3,16,20,.9);backdrop-filter:blur(14px);display:grid;grid-template-columns:1fr auto;gap:12px}.search{width:100%;border:1px solid var(--line);background:#07191e;color:#fff;border-radius:12px;padding:13px 15px;font:inherit}.filters{display:flex;gap:8px}.filters button{border:1px solid var(--line);background:#07191e;color:#b8ced2;border-radius:12px;padding:0 15px;font-weight:800;cursor:pointer}.filters button.active{background:var(--cyan);color:#031014;border-color:var(--cyan)}.result{color:var(--muted);font-size:13px;margin:10px 0 18px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;padding-bottom:64px}.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:hidden;min-width:0}.cover{position:relative;background:#0c262d}.cover img,.text-cover{width:100%;aspect-ratio:16/10;object-fit:cover;display:block}.text-cover{display:flex;flex-direction:column;justify-content:end;padding:20px;background:linear-gradient(135deg,#123c46,#06191e)}.text-cover span{font-size:12px;letter-spacing:.2em;color:var(--cyan)}.text-cover strong{font-size:28px;margin-top:5px}.badge{position:absolute;top:12px;right:12px;border-radius:999px;padding:7px 10px;font-size:10px;letter-spacing:.12em;font-weight:1000}.badge.live{background:#37df8c;color:#032313}.badge.queued{background:var(--yellow);color:#2c2300}.body{padding:17px}.eyebrow{font-size:10px;letter-spacing:.08em;color:var(--muted);font-weight:800}h2{font-size:21px;margin:8px 0 12px}.copy{white-space:pre-line;color:#c9dadd;line-height:1.55;font-size:14px;max-height:14.5em;overflow:auto;padding-right:5px}.open{display:inline-block;margin-top:12px;color:#031014;background:var(--cyan);padding:9px 12px;border-radius:9px;text-decoration:none;font-weight:900;font-size:12px}details{border-top:1px solid var(--line);margin-top:14px;padding-top:12px;color:#bdd0d4;font-size:13px}summary{cursor:pointer;font-weight:800;color:var(--yellow)}ol{padding-left:22px;line-height:1.5}.empty{display:none;text-align:center;padding:60px;color:var(--muted)}footer{border-top:1px solid var(--line);padding:28px 0 44px;color:var(--muted);font-size:13px}@media(max-width:1100px){.grid{grid-template-columns:repeat(3,1fr)}.stats{grid-template-columns:repeat(3,1fr)}}@media(max-width:760px){.brand{display:block}.grid{grid-template-columns:repeat(2,1fr)}.stats{grid-template-columns:repeat(2,1fr)}.toolbar{grid-template-columns:1fr}.filters{overflow:auto}.filters button{min-height:40px}h1{font-size:54px}}@media(max-width:520px){.wrap{width:min(100% - 20px,1440px)}.grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.stat{padding:14px}.stat strong{font-size:24px}}
  </style>
</head>
<body>
  <header class="wrap">
    <div class="brand">
      <div>
        <div class="kicker">Arga Tirta · Dashboard Publikasi</div>
        <h1>Threads<br><em>100 Hari.</em></h1>
        <p class="intro">Konten organik seputar bisnis depot isi ulang, air bersih dan higienis, perawatan sistem, serta pengalaman lapangan Arga Tirta. Terjadwal dua kali sehari pukul 08.17 dan 19.17 WIB.</p>
        <a class="profile" href="https://www.threads.com/@cv.argatirta" target="_blank" rel="noreferrer">Buka @cv.argatirta ↗</a>
      </div>
    </div>
    <section class="stats" aria-label="Ringkasan kampanye">
      <div class="stat"><strong>${days}</strong><span>Hari</span></div>
      <div class="stat"><strong>${items.length}</strong><span>Posting utama</span></div>
      <div class="stat"><strong>${replies}</strong><span>Sambungan</span></div>
      <div class="stat"><strong>${photos}</strong><span>Foto asli</span></div>
      <div class="stat"><strong>${published}</strong><span>Sudah live</span></div>
    </section>
  </header>
  <main class="wrap">
    <div class="toolbar">
      <input id="search" class="search" type="search" placeholder="Cari topik, tanggal, atau isi posting…" aria-label="Cari posting">
      <div class="filters" aria-label="Filter status">
        <button class="active" data-filter="all">Semua</button>
        <button data-filter="live">Live</button>
        <button data-filter="queued">Terjadwal</button>
      </div>
    </div>
    <div id="result" class="result">Menampilkan ${items.length} posting · ${queued} masih terjadwal</div>
    <section id="grid" class="grid">${cards}</section>
    <div id="empty" class="empty">Posting yang dicari belum ditemukan.</div>
  </main>
  <footer><div class="wrap">Arga Tirta · Depot isi ulang, sistem filtrasi, dan tutup galon · <a href="https://argatirta.web.id" style="color:var(--cyan)">argatirta.web.id</a></div></footer>
  <script>
    const cards = [...document.querySelectorAll('.card')];
    const search = document.querySelector('#search');
    const result = document.querySelector('#result');
    const empty = document.querySelector('#empty');
    let filter = 'all';
    function update(){
      const query = search.value.trim().toLowerCase();
      let shown = 0;
      for(const card of cards){
        const okStatus = filter === 'all' || card.dataset.status === filter;
        const okSearch = !query || card.dataset.search.includes(query);
        card.hidden = !(okStatus && okSearch);
        if(!card.hidden) shown++;
      }
      result.textContent = 'Menampilkan ' + shown + ' dari ' + cards.length + ' posting';
      empty.style.display = shown ? 'none' : 'block';
    }
    search.addEventListener('input', update);
    document.querySelectorAll('[data-filter]').forEach((button) => button.addEventListener('click', () => {
      document.querySelector('[data-filter].active').classList.remove('active');
      button.classList.add('active');
      filter = button.dataset.filter;
      update();
    }));
  </script>
</body>
</html>`;

await fs.mkdir(path.join(root, "public"), { recursive: true });
await fs.writeFile(
  path.join(root, "public", "index.html"),
  html.replace(/[ \t]+$/gm, ""),
);
await fs.copyFile(
  path.join(root, "threads-content-plan.json"),
  path.join(root, "public", "threads-content-plan.json"),
);
console.log(
  `Built Threads dashboard: ${days} days, ${items.length} starters, ${replies} replies.`,
);
