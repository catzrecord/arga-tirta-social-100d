# Arga Tirta — Digital Imaging 6 Bulan

Kampanye Instagram harian **24 Agustus 2026–23 Februari 2027** dengan tiga karakter konsisten:

- **Pak Tirto:** quality-control old-school yang terlalu teliti.
- **Bu Yati:** cerewet, praktis, dan baik hati.
- **Pak Udin:** teknisnya pintar, ritme kerjanya santai, sering dicari.

## Struktur kampanye

- Total: **184 posting** pukul **19.17 WIB**.
- Mingguan: **3 carousel, 2 single, 2 Reel**.
- Total format: **79 carousel, 53 single, 52 Reel**.
- Visual: photoreal digital imaging, perspektif variatif, metafora tematik, pencahayaan terarah, contact shadow, rim light, dan typography **Bebas Neue + Montserrat**.
- Antrean produksi: `content-plan.json`.
- Media publik: `public/posts/arga-tirta-6m-v2/`.
- Kalender editorial: `planning/pak-tirto-6-months/`.
- Master visual dan laporan: `campaign-v2/`.

## Perintah lokal

```bash
python3 planning/pak-tirto-6-months/build_plan.py
python3 scripts/generate_6m_campaign_v2.py
npm run validate
npm run build
npm run verify:local
```

## Autopost GitHub Actions

Workflow `.github/workflows/arga-tirta-instagram.yml` berjalan setiap hari pada **12.17 UTC / 19.17 WIB**. Publisher memilih satu item paling lama dengan:

```text
status=queued_auto
approval_status=approved
date + time_wib <= waktu sekarang
```

Mode manual workflow:

- `verify`: periksa akun dan URL aset berikutnya.
- `audio-check`: cocokkan allowlist musik Barat dengan katalog trending Instagram.
- `preflight`: buat container media tanpa memublikasikan.
- `due`: publikasikan item yang jatuh tempo.
- `publish-id`: publikasikan queue ID tertentu.

Repository secrets yang dipakai:

- `META_ACCESS_TOKEN`
- `META_TOKEN_ENCRYPTION_KEY`
- `INSTAGRAM_USER_ID`
- `PUBLIC_ASSET_BASE_URL`
- `META_AUDIO_ACCESS_TOKEN`
- `META_AUDIO_INSTAGRAM_USER_ID`

Repository variables:

- `EXPECTED_INSTAGRAM_USERNAME`
- `META_GRAPH_VERSION`
- `META_GRAPH_HOST`

Setiap Reel memakai MP4 1080×1920 H.264. Jika dua secret Audio API tersedia, musik dipilih saat publish berdasarkan `trending-western-audio.json`; publisher tetap menjalankan Reel melalui Graph API utama ketika koneksi Audio API belum dipasang.

## Dashboard

GitHub Pages menampilkan seluruh antrean dari `public/index.html`. Push ke `main` menjalankan validasi, build, dan deployment Pages.
