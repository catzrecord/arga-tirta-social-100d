# Arga Tirta Social 100D

## Threads via GitHub Actions

- Queue: `threads-content-plan.json`
- 100 days, 2 starter posts/day at 08:17 and 19:17 WIB
- 28 mini-thread sessions with 3 replies each
- 10 unique local Arga Tirta photos are used once each; no repeated photo assets
- 4 additional originals were recovered from the local 2026 Arga Tirta catalog PDF
- Workflow: `.github/workflows/arga-tirta-threads.yml`
- Required secret: `THREADS_ACCESS_TOKEN`
- Existing secrets reused: `META_TOKEN_ENCRYPTION_KEY`, `PUBLIC_ASSET_BASE_URL`
- Variables: `THREADS_EXPECTED_USERNAME=cv.argatirta`, `THREADS_GRAPH_BASE=https://graph.threads.net`

Local checks:

```powershell
npm run validate:threads
npm run verify:threads:local
```

Kampanye Instagram 100 hari untuk Arga Tirta.

- 100 post terjadwal, 5 Agustus sampai 12 November 2026
- 57 single photo
- 29 rangkaian foto dan 14 rangkaian teks yang dirender menjadi Reel 9:16 selama masih antre
- 200 aset final berukuran 1080 x 1350
- Jadwal otomatis 19.17 WIB
- Logo AT konsisten di kanan bawah

## Pemeriksaan lokal

```powershell
npm run validate
npm run reels
npm run build
npm run verify:local
```

Dashboards:

- https://arga-tirta-social-100d.vercel.app/
- https://catzrecord.github.io/arga-tirta-social-100d/

## Reel dan audio Barat

`npm run reels` memakai seluruh gambar carousel yang sudah ada, menatanya ke video 1080×1920 H.264 dengan cut cepat, lalu menyimpan MP4 di folder hari yang sama. Post yang telanjur live dipertahankan sebagaimana adanya.

Setiap Reel memakai `trending-western-audio.json`, allowlist musik Barat yang diverifikasi 10 Agustus 2026. Saat publish, Instagram Audio API mengecek respons trending saat itu dan hanya memasang kecocokan judul plus artis yang tepat. Kredensial Audio API memakai Facebook Login dan disimpan sebagai `META_AUDIO_ACCESS_TOKEN` serta `META_AUDIO_INSTAGRAM_USER_ID`, terpisah dari token Instagram Login yang sudah berjalan.

## Hubungkan akun Instagram

Jalankan helper berikut. Token dimasukkan melalui prompt tersembunyi dan langsung
disimpan sebagai GitHub Actions secret.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_meta_secrets.ps1
```


Setup interaktif kredensial musik Reel:

```bash
bash scripts/setup_audio_secrets.sh
```
