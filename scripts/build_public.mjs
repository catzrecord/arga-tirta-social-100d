import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const plan = JSON.parse(await fs.readFile(path.join(root, "content-plan.json"), "utf8"));
const esc = (s) => String(s ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const cards = plan.map((item) => `<article>
  <div class="cover"><img loading="lazy" src="${item.asset}" alt="${esc(item.title)}"><span>${item.post_type === "carousel" ? `${item.slide_count} SLIDE` : "SINGLE"}</span></div>
  <div class="meta"><small>DAY ${String(item.id).padStart(3,"0")} · ${item.date} · ${item.time_wib} WIB</small><h2>${esc(item.title)}</h2><p>${esc(item.weekly_theme)}</p><b>${item.status === "published" ? "LIVE" : "QUEUED"}</b></div>
</article>`).join("\n");
const html = `<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arga Tirta · 100 Hari</title><style>
:root{font-family:Arial,sans-serif;color:#f5f3ec;background:#02070b}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 70% 0,#0a3440,#02070b 38%);padding:28px}header{max-width:1320px;margin:0 auto 30px;border-top:4px solid #51ceda;padding:36px 0 12px}small{letter-spacing:.12em;color:#9db2b5;font-weight:700}h1{font-size:clamp(50px,9vw,124px);line-height:.82;letter-spacing:-.07em;margin:18px 0;text-transform:uppercase}header h1 i{font-style:normal;color:#faca1e}header p{max-width:760px;color:#aebfc1;font-size:18px;line-height:1.5}.grid{max-width:1320px;margin:auto;display:grid;grid-template-columns:repeat(4,1fr);gap:18px}article{background:#071017;border:1px solid #18333b;border-radius:16px;overflow:hidden}.cover{position:relative}.cover img{width:100%;display:block;aspect-ratio:4/5;object-fit:cover}.cover span{position:absolute;top:10px;right:10px;background:#faca1e;color:#061015;padding:7px 10px;border-radius:18px;font-weight:900;font-size:10px}.meta{padding:14px}.meta h2{font-size:17px;line-height:1.05;text-transform:uppercase;margin:10px 0}.meta p{font-size:12px;color:#9db2b5}.meta b{color:#51ceda;font-size:11px;letter-spacing:.12em}@media(max-width:900px){.grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:640px){body{padding:14px}.grid{grid-template-columns:repeat(2,1fr);gap:10px}}
</style></head><body><header><small>ARGA TIRTA · CINEMATIC FIELD NOTES</small><h1>100 HARI.<br><i>200 ASET.</i></h1><p>Catatan visual tentang instalasi depot air isi ulang, perawatan sistem, tutup galon, dan orang-orang yang menjaga prosesnya. Posting setiap hari pukul 19.17 WIB.</p></header><main class="grid">${cards}</main></body></html>`;
await fs.writeFile(path.join(root, "public", "index.html"), html);
await fs.copyFile(path.join(root, "content-plan.json"), path.join(root, "public", "content-plan.json"));
console.log(`Built public dashboard for ${plan.length} posts.`);
