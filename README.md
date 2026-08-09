# Arga Tirta Social 100D

## Threads via GitHub Actions

- Queue: `threads-content-plan.json`
- 100 days, 2 starter posts/day at 08:17 and 19:17 WIB
- 28 mini-thread sessions with 3 replies each
- 6 unique gallery photos are used once each; no repeated photo assets
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
- 29 photo carousel
- 14 text-only carousel, satu kali setiap minggu
- 200 aset final berukuran 1080 x 1350
- Jadwal otomatis 19.17 WIB
- Logo AT konsisten di kanan bawah

## Pemeriksaan lokal

```powershell
npm run validate
npm run build
npm run verify:local
```

Dashboards:

- https://arga-tirta-social-100d.vercel.app/
- https://catzrecord.github.io/arga-tirta-social-100d/

## Hubungkan akun Instagram

Jalankan helper berikut. Token dimasukkan melalui prompt tersembunyi dan langsung
disimpan sebagai GitHub Actions secret.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_meta_secrets.ps1
```
