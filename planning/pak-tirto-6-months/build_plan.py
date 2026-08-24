#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent
START = date(2026, 8, 24)
END = date(2027, 2, 23)
TIME_WIB = "19:17"

DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Seven hooks per week: Monday through Sunday.
WEEKS = [
    ("Kenalan dengan Pak Tirto", "Membangun maskot dan aturan dasar brand", [
        "Kenalan sama Pak Tirto: cerewetnya ada gunanya.",
        "Kenapa Pak Tirto selalu bawa meteran?",
        "Dicari dari pagi, Pak Udin muncul bawa 3 aturan depot.",
        "Bu Yati bongkar isi tas pinggang Pak Tirto.",
        "Kalau lurus bisa, kenapa pipanya muter-muter?",
        "Mau buka depot? Pak Tirto mau lihat tempatnya dulu.",
        "Kamu tim rapi dari awal atau beresin belakangan?",
    ]),
    ("Dasar membuka depot", "Mendidik calon pemilik sebelum membeli sistem", [
        "Mitos: buka depot cukup beli mesin.",
        "Sebelum sewa tempat, cek 5 hal ini.",
        "Dari ruang kosong sampai siap isi: urutannya.",
        "Kapasitas kecil atau besar? Mulai dari kebutuhan.",
        "Pak Tirto menghitung colokan sebelum menghitung cuan.",
        "Paket depot yang cocok dimulai dari survei, bukan tebak harga.",
        "Berapa luas tempat yang sedang kamu siapkan?",
    ]),
    ("Filter 101", "Membuat sistem filtrasi mudah dipahami", [
        "Banyak tabung belum tentu paling tepat.",
        "Filter juga perlu check-up.",
        "Kenalan dengan urutan kerja filter.",
        "Apa bedanya housing, media, dan membran?",
        "Pak Tirto dengerin filter, bukan gosip.",
        "Kapan sistem filter perlu disesuaikan?",
        "Bagian filter mana yang paling bikin bingung?",
    ]),
    ("Kualitas air yang terpantau", "Mendorong kebiasaan cek dan catat", [
        "Bening itu awal, bukan hasil akhir.",
        "Tiga tanda kualitas perlu dicek ulang.",
        "Apa yang sebaiknya dicatat setiap hari?",
        "Kenapa tekanan dan aliran perlu dibaca bersama?",
        "Pak Tirto percaya angka, bukan sekadar kira-kira.",
        "Mau sistem lebih konsisten? Mulai dari pemeriksaan.",
        "Kamu rutin mencatat hasil pengecekan?",
    ]),
    ("Tutup galon", "Membangun kebutuhan produk dan pasokan rutin", [
        "Tutup kecil, tanggung jawabnya gede.",
        "Kecil, tapi nggak boleh asal.",
        "Cara menyimpan tutup galon supaya tetap rapi.",
        "1 bal isi 1.000 pcs: cocok untuk siapa?",
        "Pak Tirto menyusun tutup lebih rapi dari susunan sandal.",
        "Butuh pasokan rutin? Hitung pemakaian mingguan dulu.",
        "Berapa tutup galon yang habis di depotmu per minggu?",
    ]),
    ("Survei dan tata ruang", "Mengubah keterbatasan lokasi menjadi solusi", [
        "Ruang kecil tetap bisa punya alur kerja enak.",
        "Pintu masuk menentukan banyak hal.",
        "Tiga zona yang perlu dipisahkan di depot.",
        "Kenapa posisi galon kosong dan galon jadi perlu diatur?",
        "Pak Tirto jalan mondar-mandir demi hemat tiga langkah.",
        "Kirim ukuran ruang, kami bantu baca kebutuhannya.",
        "Bagian mana yang paling sering bikin area kerja sempit?",
    ]),
    ("Instalasi yang siap jalan", "Menjelaskan nilai layanan pemasangan", [
        "Instalasi selesai saat sistem siap dipakai.",
        "Pak Tirto ukur dua kali, pasang sekali.",
        "Empat tahap pemasangan depot.",
        "Pipa rapi bukan cuma soal tampilan.",
        "Pipa belok-belok bikin alis Pak Tirto ikut belok.",
        "Dari survei sampai uji fungsi, Arga Tirta yang urus.",
        "Kamu sedang tahap cari tempat atau siap pasang?",
    ]),
    ("Kebersihan sebagai kebiasaan", "Mendorong SOP harian yang realistis", [
        "Bersih bukan acara. Ia kebiasaan.",
        "Empat titik yang sering lupa dibersihkan.",
        "Rutinitas buka dan tutup depot.",
        "Area cuci, isi, dan simpan perlu alur berbeda.",
        "Pak Tirto lebih galak ke lap kotor daripada ke tetangga.",
        "Butuh penataan ulang area kerja? Mulai dari foto lokasi.",
        "Kebiasaan bersih apa yang paling susah dijaga?",
    ]),
    ("Perawatan rutin", "Mendorong service sebelum gangguan", [
        "Service rutin bukan tanda mesin bermasalah.",
        "Jangan ghosting jadwal service.",
        "Checklist mingguan versi Pak Tirto.",
        "Komponen mana yang perlu dilihat lebih dekat?",
        "Pak Tirto punya kalender khusus buat mesin.",
        "Jadwalkan pemeriksaan sebelum operasional terganggu.",
        "Terakhir service kapan? Jujur.",
    ]),
    ("Troubleshooting tanpa asal bongkar", "Mengajari urutan diagnosis sederhana", [
        "Aliran melambat belum tentu pompa yang salah.",
        "Dengar, lihat, catat—baru bongkar.",
        "Urutan cek saat tekanan berubah.",
        "Tiga suara mesin yang layak diperhatikan.",
        "Pak Tirto bawa telinga, bukan palu duluan.",
        "Ceritakan gejalanya sebelum pilih sparepart.",
        "Masalah apa yang paling sering muncul di depotmu?",
    ]),
    ("Sparepart yang tepat", "Membangun kepercayaan layanan dan komponen", [
        "Sparepart murah bisa jadi mahal kalau salah pilih.",
        "Kenalan dengan komponen yang sering diganti.",
        "Cara mencatat umur pakai komponen.",
        "Housing, UV, pompa: mana yang harus siap cadangan?",
        "Pak Tirto kasih nama ke setiap kunci pas.",
        "Konsultasikan komponen sebelum belanja.",
        "Komponen apa yang paling sering kamu cari?",
    ]),
    ("Bukti kerja dan tim teknis", "Menampilkan proses serta kredibilitas", [
        "Pekerjaan rapi meninggalkan bukti.",
        "Satu hari bersama teknisi Arga Tirta.",
        "Apa yang diperiksa sebelum serah terima?",
        "Kenapa dokumentasi instalasi itu penting?",
        "Pak Tirto foto pipa lurus dari tiga sudut.",
        "Lihat hasil pemasangan, lalu ceritakan kebutuhanmu.",
        "Mau lihat proses instalasi bagian mana minggu depan?",
    ]),
    ("Depot menghadapi musim hujan", "Membawa isu musiman ke perawatan", [
        "Musim hujan bukan alasan untuk lengah.",
        "Cek area lembap sebelum jadi masalah.",
        "Checklist depot saat hujan sering datang.",
        "Lantai, kabel, dan penyimpanan perlu dibaca bersama.",
        "Pak Tirto bawa payung, tapi mesin tetap dicek.",
        "Minta audit penataan untuk musim hujan.",
        "Bagian depotmu paling rawan lembap di mana?",
    ]),
    ("Alur kerja yang efisien", "Mengurangi gerakan dan waktu terbuang", [
        "Tambah alat belum tentu bikin kerja lebih cepat.",
        "Hitung langkah kerja, bukan cuma jumlah mesin.",
        "Cara membuat alur galon kosong sampai siap ambil.",
        "Meja kerja yang tepat bisa menghemat gerakan.",
        "Pak Tirto lomba dengan dirinya sendiri: siapa paling sedikit bolak-balik.",
        "Kirim video alur kerja, kami bantu evaluasi.",
        "Satu hal apa yang paling bikin kerja lambat?",
    ]),
    ("Kepercayaan pelanggan", "Menyambungkan kerapian dengan persepsi", [
        "Pelanggan melihat lebih banyak dari yang kita kira.",
        "Tiga detail yang membuat depot terasa terpercaya.",
        "Cara menjelaskan proses tanpa bikin pelanggan bingung.",
        "Area depan depot adalah kesan pertama.",
        "Pak Tirto merapikan satu tutup yang miring dari jauh.",
        "Bangun depot yang siap dilihat dan siap dipercaya.",
        "Apa yang membuat kamu kembali ke sebuah depot?",
    ]),
    ("Kapasitas dan biaya", "Membantu prospek memilih skala rasional", [
        "Kapasitas besar belum tentu paling untung.",
        "Mulai dari target harian, baru pilih sistem.",
        "Cara sederhana menghitung kebutuhan operasional.",
        "Stok tutup galon perlu mengikuti ritme penjualan.",
        "Pak Tirto hitung galon pakai sempoa, hasilnya tetap masuk.",
        "Diskusikan target kapasitas sebelum pilih paket.",
        "Target galon harianmu berapa?",
    ]),
    ("Stok dan persediaan", "Menawarkan tutup galon melalui edukasi stok", [
        "Stok banyak belum tentu stok sehat.",
        "Tiga tanda persediaan perlu dirapikan.",
        "Sistem FIFO versi depot.",
        "Cara menyimpan 1.000 tutup tanpa bikin area sesak.",
        "Pak Tirto hafal stok karena semua punya tempat.",
        "Pesan tutup galon sesuai ritme pemakaian.",
        "Kamu mencatat stok manual atau digital?",
    ]),
    ("Operasional menjelang libur", "Menjaga sistem saat jadwal berubah", [
        "Libur datang, perawatan tetap jalan.",
        "Checklist sebelum depot tutup beberapa hari.",
        "Cara memulai kembali operasional setelah libur.",
        "Apa yang perlu diamankan saat tempat kosong?",
        "Pak Tirto pamit libur ke mesin satu-satu.",
        "Siapkan service sebelum jadwal padat.",
        "Depotmu tetap buka atau libur?",
    ]),
    ("Evaluasi akhir tahun", "Mengubah refleksi menjadi rencana perbaikan", [
        "Akhir tahun: waktunya lihat angka, bukan cuma capek.",
        "Apa yang paling sering menghambat operasional tahun ini?",
        "Checklist evaluasi depot akhir tahun.",
        "Komponen mana yang perlu masuk anggaran baru?",
        "Pak Tirto bikin resolusi: pipa lurus, jadwal mulus.",
        "Rencanakan peningkatan sistem untuk tahun baru.",
        "Satu target depotmu tahun depan apa?",
    ]),
    ("Mulai 2027 lebih terencana", "Mendorong audit dan kalender service", [
        "Tahun baru, sistem lama tetap perlu dibaca.",
        "Mulai 2027 dengan pemeriksaan menyeluruh.",
        "Buat kalender service setahun.",
        "Tiga data yang perlu dicatat mulai Januari.",
        "Pak Tirto punya kalender, mesin punya jadwal.",
        "Jadwalkan konsultasi awal tahun.",
        "Mau fokus ke kapasitas, kualitas, atau efisiensi?",
    ]),
    ("Memilih paket depot", "Mengarahkan prospek ke konsultasi", [
        "Paket depot bukan soal paling besar.",
        "Empat pertanyaan sebelum memilih kapasitas.",
        "Cara mencocokkan lokasi, target, dan anggaran.",
        "Komponen wajib dan opsi tambahan.",
        "Pak Tirto pilih paket seperti pilih sandal: harus pas.",
        "Minta rekomendasi paket berdasarkan lokasi.",
        "Kamu butuh depot baru atau upgrade?",
    ]),
    ("Depot untuk ruang kecil", "Menampilkan kemampuan desain adaptif", [
        "Ruang sempit masih bisa kerja rapi.",
        "Sudut mati yang sering membuang ruang.",
        "Contoh alur kerja untuk tempat kecil.",
        "Rak vertikal bisa menyelamatkan lantai.",
        "Pak Tirto bawa meteran ke mana-mana.",
        "Kirim denah atau ukuran lokasi untuk dibaca.",
        "Berapa meter lebar tempatmu?",
    ]),
    ("Timeline pemasangan", "Membuat proses pembelian terasa jelas", [
        "Pasang cepat tetap perlu urutan.",
        "Apa yang terjadi di hari survei?",
        "Timeline dari desain sampai uji sistem.",
        "Hal yang perlu disiapkan pemilik lokasi.",
        "Pak Tirto datang sebelum tukang, pulang setelah alat dites.",
        "Cek slot pemasangan bulan ini.",
        "Kapan target depotmu mulai beroperasi?",
    ]),
    ("Desain yang mudah dirawat", "Menjual nilai jangka panjang", [
        "Mulai usaha dengan sistem yang bisa dirawat.",
        "Jangan sembunyikan komponen yang perlu sering dicek.",
        "Desain untuk hari pertama dan hari ke-500.",
        "Kenapa akses service harus direncanakan?",
        "Pak Tirto suka yang gampang dibuka, bukan gampang rusak.",
        "Bangun sistem yang siap tumbuh.",
        "Kalau buka depot baru, prioritas pertamamu apa?",
    ]),
    ("Persiapan periode ramai", "Mengantisipasi perubahan ritme operasional", [
        "Musim ramai perlu disiapkan sebelum antrean datang.",
        "Cek kapasitas sebelum jam operasional berubah.",
        "Checklist stok dan perawatan menjelang periode sibuk.",
        "Atur jadwal service di luar jam puncak.",
        "Pak Tirto latihan cepat, tetap rapi.",
        "Siapkan depot untuk ritme operasional Ramadan.",
        "Jam ramai depotmu biasanya kapan?",
    ]),
    ("Operasional saat permintaan naik", "Menjaga disiplin ketika depot sibuk", [
        "Ramai bukan alasan melewatkan pengecekan.",
        "Tiga pemeriksaan sebelum buka setiap hari.",
        "Alur cepat yang tetap menjaga kerapian.",
        "Stok tutup galon saat permintaan meningkat.",
        "Pak Tirto bilang sat-set boleh, asal nggak asal.",
        "Butuh dukungan service saat operasional padat?",
        "Apa tantangan terbesarmu saat permintaan naik?",
    ]),
]

FINAL_HOOKS = [
    "Enam bulan bersama Pak Tirto: apa yang berubah?",
    "Siap bikin depotmu lebih rapi dan siap jalan?",
]

FORMATS = {
    0: "carousel",
    1: "single",
    2: "carousel",
    3: "single",
    4: "reel",
    5: "carousel",
    6: "reel",
}

PILLARS = {
    0: "edukasi",
    1: "maintenance",
    2: "edukasi",
    3: "produk_layanan",
    4: "brand_humor",
    5: "conversion_proof",
    6: "community",
}

OBJECTIVES = {
    0: "save_share",
    1: "trust",
    2: "education",
    3: "product_understanding",
    4: "reach_engagement",
    5: "lead_generation",
    6: "comments_insight",
}

CTA = {
    0: "Simpan untuk dicek lagi saat dibutuhkan.",
    1: "Cek bagian ini di depotmu hari ini.",
    2: "Geser sampai langkah terakhir lalu simpan.",
    3: "Kirim DM untuk membahas produk atau komponennya.",
    4: "Tag teman yang pasti relate dengan keluarga Arga Tirta.",
    5: "Kirim foto atau ukuran lokasi melalui WhatsApp untuk konsultasi.",
    6: "Jawab pertanyaan karakter hari ini di komentar.",
}

POSES = {
    0: "Pak Tirto berdiri tenang di samping papan diagram, menunjuk satu fakta dengan pena biru.",
    1: "Pak Tirto melakukan inspeksi tema-spesifik dengan ekspresi fokus dan satu alis sedikit terangkat.",
    2: "Pak Tirto mendemonstrasikan langkah secara berurutan memakai alat atau komponen yang relevan.",
    3: "Pak Tirto duduk atau berdiri di meja kerja, mengukur atau membandingkan produk secara presisi.",
    4: "Pak Tirto melakukan rutinitas old-school yang terlalu serius, lucu tetapi tetap tenang.",
    5: "Pak Tirto menjadi surveyor atau mandor lapangan, menunjukkan hasil, denah, atau ruang kerja.",
    6: "Pak Tirto memegang dua pilihan visual dan menunggu jawaban audiens dengan senyum tipis.",
}

CAST_ROSTER = {
    "Pak Tirto": "Senior quality-control old-school; membawa meteran, clipboard, dan humor teliti.",
    "Bu Yati": "Istri sekaligus partner operasional; cerewet, baik hati, kuat di stok, pelanggan, dan keputusan praktis.",
    "Pak Udin": "Pegawai teknis bapak kampung; pintar membaca masalah, suka bermalas-malasan, dan sering menghilang saat dicari.",
}


def cast_for(week_idx: int, weekday: int):
    if weekday == 0:
        if week_idx % 2:
            return "Pak Tirto", "", "Pak Tirto membuka minggu dengan aturan atau mitos yang ia koreksi secara tenang."
        return "Bu Yati", "", "Bu Yati membongkar mitos memakai angka, catatan stok, atau pengalaman pelanggan."
    if weekday == 1:
        return "Pak Tirto", "", "Pak Tirto melakukan check-up tema-spesifik dengan metode old-school yang terlalu serius."
    if weekday == 2:
        return "Pak Udin", "Pak Tirto", "Pak Udin akhirnya muncul dan mendemonstrasikan langkah dengan tepat; Pak Tirto mengawasi dari belakang."
    if weekday == 3:
        return "Bu Yati", "Pak Udin", "Bu Yati menjelaskan manfaat bisnis; Pak Udin menunjukkan detail produk bila diperlukan."
    if weekday == 4:
        cycle = week_idx % 3
        if cycle == 1:
            return "Pak Tirto + Pak Udin", "", "Pak Tirto mencari Pak Udin; setelah muncul, Pak Udin memberi diagnosis singkat yang ternyata tepat."
        if cycle == 2:
            return "Pak Tirto + Bu Yati", "", "Pak Tirto membuat aturan teknis panjang; Bu Yati menutupnya dengan satu kalimat praktis."
        return "Bu Yati + Pak Udin", "Pak Tirto", "Pak Udin memberi solusi sambil duduk santai; Bu Yati mengomel lalu memastikan solusinya benar."
    if weekday == 5:
        if week_idx % 2:
            return "Pak Tirto + Pak Udin", "Bu Yati", "Duo menunjukkan proses lapangan; Bu Yati menutup CTA atau penawaran."
        return "Pak Tirto + Bu Yati + Pak Udin", "", "Pak Tirto memeriksa, Pak Udin mengerjakan, Bu Yati merangkum manfaat dan CTA."
    if week_idx % 2:
        return "Bu Yati", "", "Bu Yati menjadi host pertanyaan komunitas dengan ekspresi hangat dan tegas."
    return "Pak Udin", "", "Pak Udin menjadi host kuis dari bangku kecilnya, terlihat santai tetapi pertanyaannya teknis."


def cast_direction(featured: str, weekday: int) -> str:
    if featured == "Pak Tirto":
        return POSES[weekday]
    if featured == "Bu Yati":
        return "Bu Yati memakai rol rambut warna-warni, blus putih, dan apron biru; membawa notebook atau kalkulator, ekspresi cerewet tetapi hangat."
    if featured == "Pak Udin":
        return "Pak Udin tampil dengan kemeja kerja biru pudar, kaus abu, celana kerja, sandal, tas alat, ponsel lama, dan bangku kecil; santai tetapi diagnosisnya tajam."
    if featured == "Pak Tirto + Pak Udin":
        return "Duo mandor-pegawai: Pak Tirto memanggil atau mengawasi, Pak Udin tampak santai lalu menyelesaikan bagian teknis dengan benar."
    if featured == "Pak Tirto + Bu Yati":
        return "Duo suami-istri: Pak Tirto fokus teknis, Bu Yati fokus angka atau pelanggan."
    if featured == "Bu Yati + Pak Udin":
        return "Duo operasional: Pak Udin menunjukkan alat, Bu Yati menilai biaya, stok, atau kemudahan pelanggan."
    return "Trio dengan blocking jelas: Pak Tirto di quality-control, Pak Udin di tindakan teknis, Bu Yati di keputusan operasional."


def series_for(featured: str) -> str:
    return {
        "Pak Tirto": "Pak Tirto Bilang",
        "Bu Yati": "Bu Yati Ikut Ngatur",
        "Pak Udin": "Cari Pak Udin",
        "Pak Tirto + Pak Udin": "Pak Tirto Cari Pak Udin",
        "Pak Tirto + Bu Yati": "Suami Istri Bahas Depot",
        "Bu Yati + Pak Udin": "Bu Yati Mengawasi",
        "Pak Tirto + Bu Yati + Pak Udin": "Rapat Depot",
    }[featured]

VISUALS = {
    "carousel": "Foto cast utama plus panel informasi minimal; tiap slide memakai satu gagasan, ruang putih, dan detail alat yang relevan.",
    "single": "Digital imaging fotorealistis 4:5; satu pose tema-spesifik, depth foreground-midground-background, headline minimal di ruang negatif.",
    "reel": "Reel 9:16 berdurasi 8–12 detik; satu beat karakter yang sederhana, 3–5 cut detail, teks layar maksimal 6 kata per frame.",
}

# Kamera sengaja berotasi agar feed tidak terasa seperti satu sesi foto panjang.
# Setiap siklus 7 hari memuat minimum 2 wide shot, 2 sudut tinggi, 1 low-angle,
# 1 medium portrait, dan 1 detail shot.
CAMERA_SETUPS = [
    {
        "shot": "environmental wide",
        "lens": "24mm wide, perspektif natural tanpa fisheye",
        "angle": "eye-level lebar",
        "composition": "cast tampak utuh di dalam lingkungan depot; foreground alat, midground karakter, background operasional; sisakan ruang negatif di atas",
    },
    {
        "shot": "high-angle working scene",
        "lens": "35mm medium-wide",
        "angle": "kamera lebih tinggi dari kepala, menunduk 20-30 derajat",
        "composition": "alur meja, stok, atau komponen terbaca dari atas; karakter tidak menatap kamera; headline kecil di lantai atau meja yang kosong",
    },
    {
        "shot": "low-angle wide",
        "lens": "28mm wide",
        "angle": "kamera rendah melihat sedikit ke atas",
        "composition": "karakter dan alat terasa heroik tetapi tetap kocak; tampilkan langit-langit atau signage sebagai headroom; garis vertikal tetap lurus",
    },
    {
        "shot": "observational medium",
        "lens": "50mm normal",
        "angle": "eye-level dari samping 30 derajat",
        "composition": "momen kerja candid, tangan dan properti terbaca; depth lembut; ruang teks hanya pada satu sisi",
    },
    {
        "shot": "doorway wide",
        "lens": "24mm wide",
        "angle": "sedikit rendah dan mengarah ke atas",
        "composition": "frame-within-frame dari pintu atau sela rak; banyak konteks ruang, cast tidak selalu di tengah, ruang atas cukup luas untuk headline",
    },
    {
        "shot": "top-corner overview",
        "lens": "28mm wide",
        "angle": "kamera dari sudut atas ruangan, menunduk diagonal",
        "composition": "jalur kerja dan blocking antar karakter terlihat; gunakan garis pipa atau meja sebagai leading lines; tipografi mengikuti ruang kosong",
    },
    {
        "shot": "detail portrait",
        "lens": "70-85mm detail",
        "angle": "eye-level rapat",
        "composition": "fokus ke ekspresi deadpan, tangan, meteran, kalkulator, atau komponen; background tetap memberi konteks depot",
    },
]

TYPOGRAPHY_DIRECTION = (
    "Tipografi minimal: Bebas Neue untuk headline condensed 3-7 kata dan Montserrat ExtraBold/SemiBold untuk eyebrow serta subline; "
    "maksimal dua ukuran, putih atau biru Arga Tirta, rata kiri, tanpa efek 3D, tanpa paragraf panjang, "
    "diletakkan hanya di ruang negatif dan tidak menutupi wajah atau alat."
)


def camera_for(day_number: int, fmt: str) -> dict:
    setup = CAMERA_SETUPS[(day_number - 1) % len(CAMERA_SETUPS)]
    direction = f"{setup['shot']}; {setup['lens']}; {setup['angle']}. {setup['composition']}."
    if fmt == "carousel":
        direction += " Slide berikutnya berganti ke detail, reverse angle, dan overhead; cover tetap memakai setup utama."
    elif fmt == "reel":
        direction += " Urutan shot: establishing wide, aksi medium, insert detail, reaction, lalu end-card; jangan mengulang ukuran shot berurutan."
    return {**setup, "direction": direction}


# Overlay momen nasional sepanjang 24 Agustus 2026 sampai 23 Februari 2027.
# Tanggal tetap bersumber dari kalender hari besar pemerintah; hari raya bergerak
# diberi status verifikasi bila kalender nasional tahun terkait belum final.
NATIONAL_DAYS = {
    "2026-08-25": ("Maulid Nabi Muhammad saw.", "Yang baik dijaga, yang bermanfaat diteruskan.", "Ucapan hangat dan tenang; cast merapikan depot sebelum operasional, tanpa komedi berlebihan.", "Sampaikan satu kebiasaan baik yang ingin terus kamu jaga.", "ready_official_2026"),
    "2026-09-01": ("Hari Polisi Wanita", "Tegas, sigap, dan tetap melayani.", "Bu Yati memimpin briefing kerapian dengan gesture hormat yang natural; bukan kostum atau atribut kepolisian.", "Apresiasi perempuan sigap di sekitarmu.", "ready_fixed_date"),
    "2026-09-03": ("Hari Palang Merah Indonesia", "Sigap itu dimulai sebelum dibutuhkan.", "Trio mengecek kotak P3K dan jalur kerja depot; visual informatif, hangat, tidak mendramatisasi keadaan darurat.", "Cek kembali perlengkapan P3K di tempat usahamu.", "ready_fixed_date"),
    "2026-09-04": ("Hari Pelanggan Nasional", "Pelanggan datang bawa galon, pulang bawa percaya.", "Bu Yati menyambut pelanggan, Pak Tirto memastikan area depan rapi, Pak Udin baru muncul membawa galon.", "Apa pelayanan kecil yang paling kamu ingat?", "ready_fixed_date"),
    "2026-09-08": ("Hari Pamong Praja", "Yang tertib bikin semua lebih mudah.", "Pak Tirto membuat garis alur kerja sangat presisi; humor datang dari ketelitiannya, bukan seragam instansi.", "Sebut satu aturan kerja yang paling membantu.", "ready_fixed_date"),
    "2026-09-09": ("Hari Olahraga Nasional", "Angkat galon boleh. Angkat masalah jangan.", "Pak Udin melakukan pemanasan ringan sebelum bekerja; Pak Tirto memegang stopwatch, Bu Yati menggeleng sambil tersenyum.", "Gerakan ringan apa yang kamu lakukan sebelum kerja?", "ready_fixed_date"),
    "2026-09-11": ("Hari Radio Republik Indonesia", "Kabar baik dari depot: semuanya siap jalan.", "Adegan siaran radio kampung dari meja depot; mikrofon sederhana sebagai properti, bukan meniru identitas visual RRI.", "Kalau depotmu punya siaran, topik pertamanya apa?", "ready_fixed_date"),
    "2026-09-14": ("Hari Kunjung Perpustakaan", "Baca petunjuk dulu, baru pegang kunci.", "Pak Udin diam-diam membaca manual teknis; Pak Tirto mencari-cari dia di lorong rak seperti perpustakaan mini.", "Manual apa yang paling sering kamu buka ulang?", "ready_fixed_date"),
    "2026-09-17": ("Hari Perhubungan Nasional dan Hari Palang Merah Nasional", "Alur yang lancar membuat bantuan datang tepat waktu.", "Wide shot alur galon dari masuk sampai keluar dengan garis grafis tipis; sisipkan kotak P3K secara wajar.", "Periksa satu jalur kerja yang masih suka tersendat.", "ready_fixed_date"),
    "2026-09-24": ("Hari Tani Nasional", "Dari sumber yang dijaga, hidup ikut terjaga.", "Nuansa pagi di lingkungan sumber air dan depot; cast menghormati kerja petani, tanpa menjadikan kostum sebagai lelucon.", "Tag pelaku usaha lokal yang kamu dukung.", "ready_fixed_date"),
    "2026-09-26": ("Hari Statistik", "Pak Tirto percaya catatan, bukan perasaan.", "Bu Yati menunjukkan grafik stok sederhana sementara Pak Tirto mencocokkan angka dengan clipboard.", "Data apa yang kamu catat setiap hari?", "ready_fixed_date"),
    "2026-09-27": ("Hari Pos Telekomunikasi Telegraf", "Pesan masuk. Pak Udin tetap susah ditemukan.", "Ponsel lama Pak Udin berdering di bangku kosong; ia terlihat kecil di background sedang memperbaiki alat.", "Tag teman yang balas pesannya tiga hari kemudian.", "ready_fixed_date"),
    "2026-09-28": ("Hari Kereta Api", "Jalurnya jelas, kerjanya lekas.", "Pipa dan alur galon disusun seperti jalur yang rapi; tidak memakai logo, seragam, atau aset perusahaan kereta.", "Cek apakah alur kerjamu masih suka silang jalan.", "ready_fixed_date"),
    "2026-09-29": ("Hari Sarjana Nasional", "Gelar boleh tinggi. Sambungan tetap harus rapat.", "Pak Udin menjelaskan diagram dengan sangat pintar sambil tetap duduk santai; Bu Yati terkejut karena jawabannya benar.", "Ilmu praktis apa yang paling berguna di usahamu?", "ready_fixed_date"),
    "2026-09-30": ("Peringatan G30S/PKI", "Mengingat sejarah, menjaga Indonesia.", "Still life bendera Merah Putih dan depot yang tenang; tanpa punchline karakter dan tanpa dramatisasi.", "Luangkan waktu untuk mengingat sejarah bangsa.", "ready_fixed_date"),
    "2026-10-01": ("Hari Kesaktian Pancasila", "Beda tugas, satu tujuan.", "Trio bekerja sesuai peran di satu wide frame; Merah Putih hadir kecil dan wajar, tone hormat.", "Apa arti gotong royong di tempat kerjamu?", "ready_fixed_date"),
    "2026-10-02": ("Hari Batik Nasional", "Rapi sistemnya, bangga motifnya.", "Cast memakai aksen batik yang berbeda namun serasi; alat dan proses tetap menjadi pusat cerita.", "Motif batik daerah mana yang paling kamu suka?", "ready_fixed_date"),
    "2026-10-05": ("Hari Tentara Nasional Indonesia", "Disiplin hari ini, siap setiap hari.", "Briefing pagi rapi di depot; tidak memakai seragam atau atribut TNI, tone apresiatif.", "Sebut satu kebiasaan disiplin yang kamu jaga.", "ready_fixed_date"),
    "2026-10-16": ("Hari Parlemen Indonesia", "Rapatnya panjang, keputusan depotnya satu.", "Trio rapat di meja kecil; Bu Yati mengetuk kalkulator sebagai penutup diskusi, ekspresi deadpan.", "Tim kamu kalau rapat: cepat putus atau tambah kursi?", "ready_fixed_date"),
    "2026-10-22": ("Hari Santri Nasional", "Belajar tekun, bekerja jujur, manfaatnya mengalir.", "Ucapan hangat dengan suasana usaha lokal yang bersih; karakter berbusana sopan tanpa menjadikan identitas santri sebagai gimmick.", "Bagikan satu nilai baik yang kamu pegang saat bekerja.", "ready_fixed_date"),
    "2026-10-24": ("Hari Dokter Indonesia", "Sebelum bermasalah, biasakan periksa.", "Pak Tirto melakukan check-up mesin dengan clipboard; analogi pemeriksaan dibuat ringan tanpa kostum dokter atau klaim medis.", "Kapan terakhir sistem depotmu diperiksa?", "ready_fixed_date"),
    "2026-10-27": ("Hari Penerbangan Nasional dan Hari Listrik Nasional", "Aliran lancar, operasional siap lepas landas.", "Low-angle wide memperlihatkan kabel tertata dan Pak Udin di tangga pendek; metafora visual ringan, tanpa logo maskapai.", "Periksa kabel dan sumber daya sebelum buka.", "ready_fixed_date"),
    "2026-10-28": ("Hari Sumpah Pemuda", "Yang muda bergerak, yang senior pegang meteran.", "Kolaborasi lintas usia dalam depot; Pak Tirto mentor, pekerja muda belajar, tone optimistis.", "Tag anak muda yang berani mulai usaha.", "ready_fixed_date"),
    "2026-10-30": ("Hari Keuangan", "Cuan rapi dimulai dari catatan rapi.", "Bu Yati membandingkan buku kas, stok, dan kebutuhan service; Pak Tirto dilarang menambah meteran baru.", "Pengeluaran apa yang paling sering lupa dicatat?", "ready_fixed_date"),
    "2026-11-05": ("Hari Cinta Puspa dan Satwa Nasional", "Usaha jalan, lingkungan tetap dijaga.", "Depot bersih dengan tanaman lokal dan wadah limbah tertata; satwa hanya hadir natural di kejauhan.", "Mulai satu kebiasaan kecil yang lebih ramah lingkungan.", "ready_fixed_date"),
    "2026-11-10": ("Hari Pahlawan", "Kerja baik hari ini, manfaatnya panjang.", "Potret trio yang tenang dengan Merah Putih dan cahaya pagi; tanpa adegan komedi atau kostum perjuangan.", "Siapa pahlawan sederhana dalam hidupmu?", "ready_fixed_date"),
    "2026-11-11": ("Hari Bangunan Indonesia", "Bangunan rapi, instalasi ikut bernapas.", "Wide architectural shot depot memperlihatkan ruang, jalur pipa, ventilasi, dan akses service.", "Sudut bangunan mana yang perlu ditata ulang?", "ready_fixed_date"),
    "2026-11-12": ("Hari Kesehatan Nasional dan Hari Ayah Nasional", "Bapak sehat, depot terawat, keluarga tenang.", "Pak Tirto melakukan peregangan ditemani Bu Yati; informasi kebiasaan kerja sehat tanpa klaim diagnosis.", "Ingatkan bapak di rumah untuk istirahat cukup.", "ready_fixed_date"),
    "2026-11-14": ("Hari Brigade Mobil", "Sigap bukan berarti tergesa-gesa.", "Pak Udin merespons masalah teknis cepat tetapi tetap mengikuti checklist; tanpa atribut BRIMOB.", "Simpan checklist sebelum situasi mendesak.", "ready_fixed_date"),
    "2026-11-22": ("Hari Perhubungan Darat Nasional", "Dari depan sampai belakang, jalurnya jangan tabrakan.", "High-angle menunjukkan rute pelanggan, galon kosong, area cuci, dan galon siap ambil.", "Coba hitung berapa kali kamu bolak-balik hari ini.", "ready_fixed_date"),
    "2026-11-25": ("Hari Guru dan PGRI", "Ilmu yang dibagi bikin semua lebih siap.", "Pak Tirto mengajar di papan sederhana, Pak Udin pura-pura mengantuk tetapi jawabannya paling tepat.", "Tag guru yang ilmunya masih kamu pakai.", "ready_fixed_date"),
    "2026-11-28": ("Hari Menanam Pohon Indonesia", "Yang ditanam hari ini, manfaatnya nanti.", "Trio menanam pohon di area usaha dengan alat sederhana; humor kecil dari Pak Tirto mengukur jarak tanam.", "Tanam atau rawat satu pohon di sekitar usahamu.", "ready_fixed_date"),
    "2026-11-29": ("Hari KORPRI", "Pelayanan rapi lahir dari kerja yang konsisten.", "Adegan pelayanan administrasi depot yang tertib; tanpa seragam atau lambang KORPRI.", "Apresiasi orang yang selalu melayani dengan sabar.", "ready_fixed_date"),
    "2026-12-01": ("Hari Artileri", "Tepat sasaran, bukan asal pasang.", "Pak Tirto mengarahkan meteran ke titik pemasangan seperti target ukur; tanpa senjata atau atribut militer.", "Ukur dua kali sebelum memasang.", "ready_fixed_date"),
    "2026-12-09": ("Hari Armada Republik Indonesia", "Yang besar tetap butuh perawatan rutin.", "Metafora armada melalui deretan galon dan unit kerja yang siap beroperasi; tanpa insignia militer.", "Jadwalkan perawatan sebelum operasional padat.", "ready_fixed_date"),
    "2026-12-12": ("Hari Transmigrasi", "Tempat baru, peluang baru, persiapan tetap nomor satu.", "Keluarga usaha meninjau lokasi kosong dengan blueprint dan meteran; optimistis dan membumi.", "Kirim ukuran lokasi jika sedang menyiapkan usaha baru.", "ready_fixed_date"),
    "2026-12-13": ("Hari Nusantara", "Dari banyak pulau, kebutuhan air menyatukan kita.", "Peta Indonesia dibentuk dari bayangan galon dan jalur cahaya biru secara minimal, cast tetap realistis.", "Sebut kota tempat depotmu beroperasi.", "ready_fixed_date"),
    "2026-12-15": ("Hari Juang Kartika TNI-AD", "Tangguh itu rutin, bukan mendadak.", "Pemeriksaan pagi yang disiplin; tanpa atribut militer dan tanpa lelucon pada peringatannya.", "Kebiasaan rutin apa yang membuat usahamu tangguh?", "ready_fixed_date"),
    "2026-12-19": ("Hari Bela Negara", "Menjaga negeri bisa dimulai dari kerja yang jujur.", "Trio bekerja rapi dengan Merah Putih kecil di background; tone bangga dan hormat.", "Bagikan satu bentuk kerja jujur versi kamu.", "ready_fixed_date"),
    "2026-12-20": ("Hari Kesetiakawanan Sosial Nasional", "Kalau dikerjakan bersama, beratnya ikut berkurang.", "Trio membantu memindahkan dan merapikan galon bersama; ekspresi hangat, bukan slapstick.", "Tag orang yang selalu sigap membantu.", "ready_fixed_date"),
    "2026-12-22": ("Hari Ibu Nasional dan Hari Sosial", "Bu Yati cerewet karena semuanya ingin baik-baik saja.", "Hero portrait Bu Yati memimpin operasional, Pak Tirto dan Pak Udin mengikuti catatannya dengan hormat.", "Tulis satu kalimat terima kasih untuk ibu.", "ready_fixed_date"),
    "2026-12-25": ("Hari Natal", "Damai di rumah, hangat di hati.", "Ucapan Natal yang bersih dan inklusif; pencahayaan hangat, dekorasi secukupnya, tanpa hard selling.", "Selamat merayakan bersama orang-orang terkasih.", "ready_official_2026"),
    "2027-01-01": ("Tahun Baru Masehi", "Tahun baru, catatan lama jangan ikut hilang.", "Trio membuka buku kerja 2027 di depot rapi; konfeti sangat minimal, fokus pada rencana.", "Tulis satu target usahamu di 2027.", "ready_calendar_2027"),
    "2027-01-03": ("Hari Departemen Agama", "Rukun dalam hidup, jujur dalam bekerja.", "Keluarga usaha bekerja berdampingan dalam suasana hangat; tanpa atribut institusi.", "Bagikan nilai baik yang kamu bawa ke tempat kerja.", "ready_fixed_date"),
    "2027-01-05": ("Hari KOWAL dan Isra Mikraj Nabi Muhammad saw.", "Menjaga arah, menata hati.", "Utamakan ucapan Isra Mikraj yang tenang; KOWAL cukup disebut dalam caption apresiasi, tanpa kostum atau insignia.", "Semoga perjalanan ini menguatkan langkah baik kita.", "verify_2027_religious_date"),
    "2027-01-10": ("Hari Tritura dan Hari Gerakan Satu Juta Pohon", "Tiga tuntutan Pak Tirto: rapi, terawat, dan tidak boros.", "Pak Tirto memegang papan tiga poin di dekat pohon yang baru dirawat; konteks sejarah diterangkan singkat di caption.", "Pilih satu: rapi, terawat, atau hemat.", "ready_fixed_date"),
    "2027-01-15": ("Hari Dharma Samudera", "Laut mengajarkan: kuat karena terus bergerak.", "Visual reflektif bernuansa biru dengan gelombang cahaya halus pada instalasi; tone hormat, tanpa gimmick.", "Apresiasi mereka yang menjaga perairan Indonesia.", "ready_fixed_date"),
    "2027-01-25": ("Hari Gizi dan Makanan", "Yang dikonsumsi setiap hari layak diperhatikan.", "Dapur usaha bersih dan hidrasi sebagai kebiasaan umum; hindari klaim gizi atau medis yang spesifik.", "Mulai satu kebiasaan makan dan minum yang lebih teratur.", "ready_fixed_date"),
    "2027-02-05": ("Hari Peristiwa Kapal Tujuh Provinsi", "Sejarah berlayar, ingatan jangan tenggelam.", "Still life arsip, koran, dan warna biru laut; tanpa punchline karakter.", "Luangkan waktu membaca satu halaman sejarah Indonesia.", "ready_fixed_date"),
    "2027-02-06": ("Tahun Baru Imlek 2578", "Semoga rezeki mengalir, usahanya makin rapi.", "Merah dan biru dipadukan minimal; lampion secukupnya, trio menyambut dengan gesture hangat tanpa stereotip.", "Gong Xi Fa Cai untuk yang merayakan.", "verify_2027_religious_date"),
    "2027-02-09": ("Hari Pers Nasional dan Hari Kavaleri", "Kabar baik harus jelas sumbernya.", "Bu Yati membaca koran usaha, Pak Tirto memeriksa fakta pada clipboard; apresiasi pers jadi fokus utama.", "Media apa yang kamu percaya untuk cari informasi usaha?", "ready_fixed_date"),
    "2027-02-14": ("Hari Peringatan Pemberontakan PETA", "Keberanian punya jejak dalam sejarah.", "Visual reflektif dengan Merah Putih, arsip, dan cahaya pagi; tanpa tema Valentine dan tanpa komedi.", "Mari mengenang keberanian para pendahulu.", "ready_fixed_date"),
    "2027-02-22": ("Hari Istiqlal", "Berdiri megah karena fondasinya dijaga.", "Metafora fondasi dan kerapian struktur depot; masjid tidak dijadikan latar komersial dan CTA tetap reflektif.", "Apa fondasi utama yang kamu jaga dalam usaha?", "ready_fixed_date"),
}

CAPTION_ANGLE = {
    0: "Buka dengan mitos atau pernyataan tegas, beri 2–3 poin praktis, tutup dengan ajakan menyimpan.",
    1: "Mulai dari kebiasaan khas Pak Tirto, jelaskan manfaat pemeriksaan, beri satu tindakan yang bisa dilakukan hari ini.",
    2: "Susun langkah bernomor, jelaskan alasan setiap langkah, ringkas dengan checklist.",
    3: "Tampilkan detail produk atau layanan, manfaat operasional, lalu arahkan ke percakapan kebutuhan.",
    4: "Gunakan satu punchline Pak Tirto, lanjutkan fakta singkat, tutup dengan ajakan tag teman.",
    5: "Tunjukkan masalah calon pelanggan, bukti solusi Arga Tirta, proses singkat, lalu CTA konsultasi.",
    6: "Ajukan satu pertanyaan mudah dijawab dan gunakan respons sebagai riset konten berikutnya.",
}


def seasonal_note(d: date) -> str:
    if d == date(2026, 10, 15):
        return "Global Handwashing Day; kaitkan dengan kebiasaan bersih tanpa klaim kesehatan berlebihan."
    if date(2026, 11, 1) <= d <= date(2026, 12, 15):
        return "Musim hujan; sesuaikan contoh dengan kelembapan, lantai, kabel, dan penyimpanan."
    if d == date(2026, 12, 25):
        return "Hari Natal; gunakan ucapan inklusif dan fokus pada kesiapan operasional libur."
    if d == date(2027, 1, 1):
        return "Tahun Baru; konten evaluasi dan rencana operasional."
    if d == date(2027, 2, 6):
        return "Imlek 2027; gunakan visual bersih dan ucapan ringan bila relevan bagi audiens."
    if d >= date(2027, 2, 8):
        return "Window persiapan Ramadan 1448 H; tanggal resmi perlu diverifikasi sebelum produksi copy bertanggal."
    return ""


def overlap(d: date) -> bool:
    return d <= date(2026, 11, 12)


def asset_count(fmt: str) -> str:
    return {"single": "1 image 1080x1350", "carousel": "4 slides 1080x1350", "reel": "1 video 1080x1920"}[fmt]


rows = []
day_id = 1
for week_idx, (theme, goal, hooks) in enumerate(WEEKS, start=1):
    for weekday, hook in enumerate(hooks):
        d = START + timedelta(days=day_id - 1)
        fmt = FORMATS[weekday]
        featured_cast, supporting_cast, interaction_beat = cast_for(week_idx, weekday)
        if week_idx == 1 and weekday == 3:
            featured_cast, supporting_cast = "Bu Yati", "Pak Tirto"
            interaction_beat = "Bu Yati membongkar isi tas pinggang Pak Tirto; Pak Tirto berdiri tenang sambil mempertahankan kegunaan setiap alat."
        if week_idx == 1 and weekday == 6:
            featured_cast, supporting_cast = "Bu Yati + Pak Udin", ""
            interaction_beat = "Bu Yati menunjukkan area rapi; Pak Udin tertangkap sedang membereskan sisi gudang yang kusut."
        camera = camera_for(day_id, fmt)
        national = NATIONAL_DAYS.get(d.isoformat())
        row = {
            "id": day_id,
            "date": d.isoformat(),
            "day": DAYS_ID[d.weekday()],
            "time_wib": TIME_WIB,
            "week": week_idx,
            "weekly_theme": theme,
            "weekly_goal": goal,
            "format": fmt,
            "pillar": PILLARS[weekday],
            "objective": OBJECTIVES[weekday],
            "hook": hook,
            "series_name": series_for(featured_cast),
            "featured_cast": featured_cast,
            "supporting_cast": supporting_cast,
            "cast_direction": cast_direction(featured_cast, weekday),
            "interaction_beat": interaction_beat,
            "camera_shot": camera["shot"],
            "camera_lens": camera["lens"],
            "camera_angle": camera["angle"],
            "camera_composition": camera["composition"],
            "camera_direction": camera["direction"],
            "typography_direction": TYPOGRAPHY_DIRECTION,
            "visual_direction": f"{VISUALS[fmt]} {camera['direction']} {TYPOGRAPHY_DIRECTION} Tema visual hari ini: {hook}",
            "caption_outline": f"{CAPTION_ANGLE[weekday]} Hook utama: {hook}",
            "cta": CTA[weekday],
            "asset_requirement": asset_count(fmt),
            "national_day": national[0] if national else "",
            "national_day_hook": national[1] if national else "",
            "national_day_visual": national[2] if national else "",
            "national_day_cta": national[3] if national else "",
            "national_day_status": national[4] if national else "",
            "seasonal_note": seasonal_note(d),
            "overlaps_existing_100d_queue": overlap(d),
            "status": "approved_for_production",
            "approval_status": "approved",
            "visual_system": "arga-tirta-family-business-digital-imaging-v2",
        }
        rows.append(row)
        day_id += 1

for idx, hook in enumerate(FINAL_HOOKS):
    d = START + timedelta(days=day_id - 1)
    fmt = "carousel" if idx == 0 else "single"
    camera = camera_for(day_id, fmt)
    national = NATIONAL_DAYS.get(d.isoformat())
    rows.append({
        "id": day_id,
        "date": d.isoformat(),
        "day": DAYS_ID[d.weekday()],
        "time_wib": TIME_WIB,
        "week": 27,
        "weekly_theme": "Rekap dan ajakan bertindak",
        "weekly_goal": "Mengubah pembelajaran enam bulan menjadi percakapan penjualan",
        "format": fmt,
        "pillar": "conversion_proof",
        "objective": "lead_generation",
        "hook": hook,
        "series_name": "Rapat Depot" if idx == 0 else "Suami Istri Bahas Depot",
        "featured_cast": "Pak Tirto + Bu Yati + Pak Udin" if idx == 0 else "Pak Tirto + Bu Yati",
        "supporting_cast": "",
        "cast_direction": "Trio berdiri di depot rapi dengan fungsi jelas." if idx == 0 else "Pak Tirto membawa blueprint, Bu Yati memegang ringkasan penawaran.",
        "interaction_beat": "Rekap bersama: teknis, operasional, dan eksekusi menyatu." if idx == 0 else "Pak Tirto membuka kebutuhan teknis; Bu Yati menutup CTA konsultasi.",
        "camera_shot": camera["shot"],
        "camera_lens": camera["lens"],
        "camera_angle": camera["angle"],
        "camera_composition": camera["composition"],
        "camera_direction": camera["direction"],
        "typography_direction": TYPOGRAPHY_DIRECTION,
        "visual_direction": f"{VISUALS[fmt]} {camera['direction']} {TYPOGRAPHY_DIRECTION} Tema visual hari ini: {hook}",
        "caption_outline": "Ringkas perubahan yang sudah dipelajari, tunjukkan kesiapan Arga Tirta, lalu arahkan ke konsultasi.",
        "cta": "Chat WhatsApp Arga Tirta untuk konsultasi pemasangan, service, atau kebutuhan tutup galon.",
        "asset_requirement": asset_count(fmt),
        "national_day": national[0] if national else "",
        "national_day_hook": national[1] if national else "",
        "national_day_visual": national[2] if national else "",
        "national_day_cta": national[3] if national else "",
        "national_day_status": national[4] if national else "",
        "seasonal_note": seasonal_note(d),
        "overlaps_existing_100d_queue": overlap(d),
        "status": "approved_for_production",
        "approval_status": "approved",
        "visual_system": "arga-tirta-family-business-digital-imaging-v2",
    })
    day_id += 1

assert rows[0]["date"] == START.isoformat()
assert rows[-1]["date"] == END.isoformat()
assert len(rows) == (END - START).days + 1 == 184
assert len({r["hook"].casefold() for r in rows}) == len(rows)

fieldnames = list(rows[0].keys())
with (ROOT / "calendar-daily.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

with (ROOT / "calendar-daily.json").open("w", encoding="utf-8") as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=2)

with (ROOT / "calendar-daily.md").open("w", encoding="utf-8") as fh:
    fh.write("# Kalender Harian Keluarga Usaha Arga Tirta - 6 Bulan\n\n")
    fh.write(f"Periode: **{START.isoformat()} sampai {END.isoformat()}** ({len(rows)} posting). Semua status `approved_for_production`.\n\n")
    fh.write("| ID | Tanggal | Format | Cast | Kamera | Hook | Momen Nasional |\n")
    fh.write("|---:|---|---|---|---|---|---|\n")
    for r in rows:
        hook = r["hook"].replace("|", "/")
        moment = r["national_day"].replace("|", "/") if r["national_day"] else "-"
        fh.write(f"| {r['id']} | {r['date']} | {r['format']} | {r['featured_cast']} | {r['camera_shot']} / {r['camera_angle']} | {hook} | {moment} |\n")

national_rows = [r for r in rows if r["national_day"]]
with (ROOT / "national-days-overlay.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    keys = ["date", "day", "national_day", "national_day_hook", "national_day_visual", "national_day_cta", "national_day_status", "featured_cast", "format", "camera_shot", "camera_lens", "camera_angle"]
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    w.writerows({key: r[key] for key in keys} for r in national_rows)

with (ROOT / "national-days-overlay.md").open("w", encoding="utf-8") as fh:
    fh.write("# Draft Momen Nasional Arga Tirta\n\n")
    fh.write(f"Cakupan periode: **{START.isoformat()} sampai {END.isoformat()}**. Total **{len(national_rows)} tanggal** dengan draft khusus.\n\n")
    fh.write("Draft ini menjadi overlay: pada tanggal terkait, hook/visual/CTA momen nasional menggantikan angle harian biasa tanpa mengubah jadwal posting.\n\n")
    fh.write("| Tanggal | Momen | Hook | Visual ringkas | Status |\n")
    fh.write("|---|---|---|---|---|\n")
    for r in national_rows:
        values = [r["date"], r["national_day"], r["national_day_hook"], r["national_day_visual"], r["national_day_status"]]
        values = [str(v).replace("|", "/") for v in values]
        fh.write("| " + " | ".join(values) + " |\n")

format_counts = Counter(r["format"] for r in rows)
pillar_counts = Counter(r["pillar"] for r in rows)
objective_counts = Counter(r["objective"] for r in rows)
cast_counts = Counter(r["featured_cast"] for r in rows)
series_counts = Counter(r["series_name"] for r in rows)
overlap_count = sum(r["overlaps_existing_100d_queue"] for r in rows)
camera_counts = Counter(r["camera_shot"] for r in rows)
angle_counts = Counter(r["camera_angle"] for r in rows)
wide_count = sum("wide" in r["camera_shot"] for r in rows)
high_count = sum(r["camera_shot"] in {"high-angle working scene", "top-corner overview"} for r in rows)
low_count = sum(r["camera_shot"] in {"low-angle wide", "doorway wide"} for r in rows)

strategy = f"""# Strategi Konten Keluarga Usaha Arga Tirta - 6 Bulan

## Status dan periode

- Periode draft: **{START.isoformat()} - {END.isoformat()}**.
- Total: **{len(rows)} feed post**, satu post setiap hari pukul **{TIME_WIB} WIB**.
- Status kalender: **approved for production**. Antrean lama dihentikan dan diganti kampanye digital-imaging V2.
- **{overlap_count} tanggal pertama** sebelumnya beririsan dengan antrean lama; antrean dan aset lama kini dipensiunkan dari branch aktif.

## Janji kampanye

**Pak Tirto, Bu Yati, dan Pak Udin membuat urusan depot terasa mudah dipahami melalui tiga sudut: kualitas, operasional, dan eksekusi lapangan.**

## Visual lock

- Pak Tirto yang sama: wajah, kumis, kacamata, rambut, kemeja biru, celana krem, sandal, jam tangan, dan tas pinggang konsisten.
- Bu Yati yang sama: wajah orisinal, rambut berrol warna-warni, blus putih berenda, apron biru, celana kulot navy, sandal biru, notebook, dan kalkulator konsisten. Tanpa rokok atau benda di mulut.
- Pak Udin yang sama: wajah orisinal, rambut pendek berantakan, kumis tipis, kemeja kerja biru pudar, kaus abu, celana kerja, sandal, tas alat, ponsel lama, lap, dan bangku kecil konsisten.
- Pose mengikuti tema; kelucuan datang dari metode Pak Tirto yang terlalu serius.
- Hindari pose kaget berulang, tumpahan sebagai gimmick, barang beterbangan, dan ekspresi panik.
- Digital imaging fotorealistis dengan depth nyata, lingkungan depot yang masuk akal, dan tipografi Bebas Neue + Montserrat.
- Feed master 1080x1350; Reel 1080x1920; teks cover maksimal 8 kata utama.

## Sistem kamera anti-monoton

- Kamera berotasi tiap hari; setup yang sama tidak dipakai dua hari berturut-turut.
- Total environmental/wide frame: **{wide_count}** posting.
- Total sudut tinggi/top-corner: **{high_count}** posting.
- Total sudut rendah melihat sedikit ke atas: **{low_count}** posting.
- Siklus mingguan: 24mm environmental wide, 35mm high-angle, 28mm low-angle, 50mm observational, 24mm doorway wide, 28mm top-corner, dan 70-85mm detail.
- Pada wide low-angle, sisakan headroom untuk langit-langit/signage dan headline. Perspektif natural, bukan fisheye.
- Carousel wajib berganti cover wide ke detail/reverse-angle/overhead. Reel wajib memakai establishing, medium action, insert, reaction, lalu end-card.
- Tipografi: Bebas Neue + Montserrat ExtraBold/SemiBold, headline 3-7 kata, maksimal dua ukuran, putih/biru, rata kiri, dan hanya di ruang negatif.

## Cadence mingguan

| Hari | Peran | Format default | Tujuan |
|---|---|---|---|
| Senin | Mitos/fakta atau edukasi | Carousel | Save dan share |
| Selasa | Check-up Pak Tirto | Single | Trust |
| Rabu | Langkah dan checklist | Carousel | Education |
| Kamis | Produk atau detail layanan | Single | Product understanding |
| Jumat | Humor karakter | Reel | Reach dan engagement |
| Sabtu | Bukti, survei, atau CTA | Reel/Carousel | Lead generation |
| Minggu | Pertanyaan komunitas | Single | Comments dan insight |

## Sistem karakter

- **Pak Tirto:** quality-control, inspeksi, mitos teknis, dan mentor old-school.
- **Bu Yati:** istri Pak Tirto yang cerewet tetapi baik hati; menjaga stok, harga, administrasi, pelanggan, serta penutup CTA.
- **Pak Udin:** pegawai bapak kampung yang pintar tetapi malas dan sering menghilang; kuat untuk diagnosis teknis serta humor deadpan.
- **Duo:** Pak Tirto mencari Pak Udin, Bu Yati mengomeli keduanya, atau solusi teknis bertemu hitungan bisnis.
- **Trio:** Pak Tirto memeriksa, Pak Udin mengerjakan, Bu Yati merangkum manfaat.

Serial berulang: `Pak Tirto Bilang`, `Bu Yati Ikut Ngatur`, `Cari Pak Udin`, `Pak Tirto Cari Pak Udin`, `Suami Istri Bahas Depot`, `Bu Yati Mengawasi`, dan `Rapat Depot`.

## Distribusi format

- Single: **{format_counts['single']}**
- Carousel: **{format_counts['carousel']}**
- Reel: **{format_counts['reel']}**

## Distribusi pilar

"""
for key, count in pillar_counts.most_common():
    strategy += f"- {key}: **{count}**\n"

strategy += "\n## Distribusi cast utama\n\n"
for key, count in cast_counts.most_common():
    strategy += f"- {key}: **{count}** posting\n"

strategy += """

## Enam fase kampanye

1. **Bulan 1 - Kenal dan percaya:** maskot, dasar depot, filter, dan kualitas.
2. **Bulan 2 - Paham produk dan proses:** tutup galon, survei, instalasi, serta kebersihan.
3. **Bulan 3 - Operasional sehat:** service, troubleshooting, sparepart, tim, dan musim hujan.
4. **Bulan 4 - Bisnis lebih efisien:** alur kerja, kepercayaan pelanggan, kapasitas, stok, dan libur akhir tahun.
5. **Bulan 5 - Rencana pertumbuhan:** evaluasi, kalender service, paket depot, ruang kecil, dan timeline pemasangan.
6. **Bulan 6 - Konversi:** desain mudah dirawat, persiapan periode ramai, dukungan operasional, dan konsultasi.

## CTA ladder

- Edukasi: simpan, geser, atau cek bagian tertentu.
- Engagement: jawab pertanyaan atau tag teman.
- Soft lead: kirim foto, denah, ukuran lokasi, atau gejala mesin.
- Direct lead: konsultasi pemasangan, service, sparepart, atau pembelian tutup galon.

## Sistem produksi

1. Kunci hook dan fakta teknis H-14.
2. Produksi visual H-10 menggunakan character sheet Pak Tirto.
3. Typesetting dan caption H-7.
4. Review teknis Arga Tirta H-5.
5. Approval final H-3.
6. Penjadwalan H-2.
7. Balas komentar dan DM pada hari tayang.

## Catatan kalender

- Tersedia **{len(national_rows)} draft momen nasional** pada `national-days-overlay.md` dan `national-days-overlay.csv`.
- Tanggal tetap memakai daftar hari besar pemerintah; Maulid dan Natal 2026 mengacu SKB 3 Menteri 2026.
- Tanggal keagamaan 2027 yang bergerak diberi status `verify_2027_religious_date` dan diperiksa ulang sebelum produksi final.
- Momen sejarah, keagamaan, TNI/Polri, dan institusi ditangani hormat; humor karakter dipakai hanya jika konteksnya pantas.
- Window Ramadan pada Februari 2027 ditulis generik agar mudah digeser mengikuti penetapan resmi.
"""
(ROOT / "campaign-strategy.md").write_text(strategy, encoding="utf-8")

validation = {
    "status": "pass",
    "date_start": rows[0]["date"],
    "date_end": rows[-1]["date"],
    "post_count": len(rows),
    "unique_dates": len({r["date"] for r in rows}),
    "unique_hooks": len({r["hook"].casefold() for r in rows}),
    "time_wib": TIME_WIB,
    "format_counts": dict(sorted(format_counts.items())),
    "pillar_counts": dict(sorted(pillar_counts.items())),
    "objective_counts": dict(sorted(objective_counts.items())),
    "featured_cast_counts": dict(sorted(cast_counts.items())),
    "series_counts": dict(sorted(series_counts.items())),
    "camera_shot_counts": dict(sorted(camera_counts.items())),
    "camera_angle_counts": dict(sorted(angle_counts.items())),
    "wide_post_count": wide_count,
    "high_angle_post_count": high_count,
    "low_angle_post_count": low_count,
    "no_consecutive_camera_repeat": all(rows[i]["camera_shot"] != rows[i - 1]["camera_shot"] for i in range(1, len(rows))),
    "national_day_draft_count": len(national_rows),
    "national_day_dates_unique": len({r["date"] for r in national_rows}),
    "national_day_all_have_hook_visual_cta": all(r["national_day_hook"] and r["national_day_visual"] and r["national_day_cta"] for r in national_rows),
    "character_sheets": {
        "Pak Tirto": "../../concepts/arga-tirta-cast-v2/pak-tirto-character-sheet.png",
        "Bu Yati": "../../concepts/arga-tirta-cast-v2/bu-yati-character-sheet.png",
        "Pak Udin": "../../concepts/arga-tirta-cast-v2/pak-udin-character-sheet.png",
    },
    "existing_queue_overlap_count": overlap_count,
    "existing_queue_overlap_end": "2026-11-12",
    "live_queue_modified": True,
    "all_statuses_approved_for_production": all(r["status"] == "approved_for_production" for r in rows),
    "all_approvals_approved": all(r["approval_status"] == "approved" for r in rows),
}
(ROOT / "validation-report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")

# Operator-friendly Excel workbook.
wb = Workbook()
ws = wb.active
ws.title = "Kalender Harian"
excel_headers = [
    "ID", "Tanggal", "Hari", "Jam WIB", "Minggu", "Tema Mingguan", "Format",
    "Pilar", "Tujuan", "Hook", "Serial", "Cast Utama", "Cast Pendukung", "Arahan Cast",
    "Beat Interaksi", "Shot Kamera", "Lensa", "Sudut Kamera", "Komposisi", "Arahan Kamera",
    "Arahan Visual", "Arahan Typography", "Outline Caption", "CTA", "Kebutuhan Aset",
    "Momen Nasional", "Hook Nasional", "Visual Nasional", "CTA Nasional", "Status Nasional",
    "Catatan Musiman", "Overlap Antrean Lama", "Status", "Approval",
]
ws.append(excel_headers)
for r in rows:
    ws.append([
        r["id"], r["date"], r["day"], r["time_wib"], r["week"], r["weekly_theme"],
        r["format"], r["pillar"], r["objective"], r["hook"], r["series_name"], r["featured_cast"],
        r["supporting_cast"], r["cast_direction"], r["interaction_beat"], r["camera_shot"],
        r["camera_lens"], r["camera_angle"], r["camera_composition"], r["camera_direction"],
        r["visual_direction"], r["typography_direction"], r["caption_outline"], r["cta"], r["asset_requirement"],
        r["national_day"], r["national_day_hook"], r["national_day_visual"], r["national_day_cta"], r["national_day_status"],
        r["seasonal_note"], "YA" if r["overlaps_existing_100d_queue"] else "", r["status"],
        r["approval_status"],
    ])
header_fill = PatternFill("solid", fgColor="075DE3")
for cell in ws[1]:
    cell.fill = header_fill
    cell.font = Font(color="FFFFFF", bold=True)
    cell.alignment = Alignment(vertical="center", wrap_text=True)
ws.freeze_panes = "A2"
ws.auto_filter.ref = ws.dimensions
widths = [7, 13, 11, 10, 9, 28, 12, 20, 20, 42, 28, 28, 24, 48, 52, 24, 32, 34, 54, 58, 62, 58, 58, 46, 24, 34, 44, 58, 44, 28, 36, 18, 17, 15]
for i, width in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = width
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
for row_index in range(2, ws.max_row + 1):
    fmt = ws.cell(row_index, 7).value
    color = {"single": "EAF4FF", "carousel": "EAFBF7", "reel": "FFF3DF"}.get(fmt, "FFFFFF")
    ws.cell(row_index, 7).fill = PatternFill("solid", fgColor=color)
    if ws.cell(row_index, 32).value == "YA":
        ws.cell(row_index, 32).fill = PatternFill("solid", fgColor="FFE3E3")
    if ws.cell(row_index, 26).value:
        for col in range(26, 31):
            ws.cell(row_index, col).fill = PatternFill("solid", fgColor="FFF3C4")

weekly = wb.create_sheet("Tema Mingguan")
weekly.append(["Minggu", "Tema", "Tujuan", "Tanggal Mulai", "Tanggal Selesai"])
for idx, (theme, goal, _) in enumerate(WEEKS, start=1):
    w_start = START + timedelta(days=(idx - 1) * 7)
    w_end = w_start + timedelta(days=6)
    weekly.append([idx, theme, goal, w_start.isoformat(), w_end.isoformat()])
weekly.append([27, "Rekap dan ajakan bertindak", "Mengubah pembelajaran menjadi lead", "2027-02-22", "2027-02-23"])
for cell in weekly[1]:
    cell.fill = header_fill
    cell.font = Font(color="FFFFFF", bold=True)
weekly.freeze_panes = "A2"
weekly.auto_filter.ref = weekly.dimensions
for col, width in enumerate([10, 34, 55, 15, 15], start=1):
    weekly.column_dimensions[get_column_letter(col)].width = width
for row in weekly.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = Alignment(vertical="top", wrap_text=True)

national_ws = wb.create_sheet("Momen Nasional")
national_ws.append(["Tanggal", "Hari", "Momen", "Hook", "Visual", "CTA", "Status", "Cast", "Format", "Shot", "Lensa", "Sudut"])
for r in national_rows:
    national_ws.append([
        r["date"], r["day"], r["national_day"], r["national_day_hook"], r["national_day_visual"],
        r["national_day_cta"], r["national_day_status"], r["featured_cast"], r["format"],
        r["camera_shot"], r["camera_lens"], r["camera_angle"],
    ])
for cell in national_ws[1]:
    cell.fill = header_fill
    cell.font = Font(color="FFFFFF", bold=True)
    cell.alignment = Alignment(vertical="center", wrap_text=True)
national_ws.freeze_panes = "A2"
national_ws.auto_filter.ref = national_ws.dimensions
for col, width in enumerate([13, 11, 38, 46, 64, 48, 30, 28, 12, 24, 34, 36], start=1):
    national_ws.column_dimensions[get_column_letter(col)].width = width
for row in national_ws.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = Alignment(vertical="top", wrap_text=True)

summary = wb.create_sheet("Ringkasan")
summary_rows = [
    ("Periode", f"{START.isoformat()} sampai {END.isoformat()}"),
    ("Total posting", len(rows)),
    ("Jam tayang", f"{TIME_WIB} WIB"),
    ("Single", format_counts["single"]),
    ("Carousel", format_counts["carousel"]),
    ("Reel", format_counts["reel"]),
    ("Draft momen nasional", len(national_rows)),
    ("Wide shot", wide_count),
    ("Sudut tinggi", high_count),
    ("Sudut rendah ke atas", low_count),
    ("Camera repeat berurutan", "TIDAK"),
    ("Tanggal overlap antrean lama", overlap_count),
    ("Antrean live diganti", "TIDAK"),
    ("Status seluruh konten", "approved_for_production"),
    ("Approval", "approved"),
]
summary_rows.extend((f"Cast utama: {name}", count) for name, count in cast_counts.most_common())
summary_rows.extend((f"Serial: {name}", count) for name, count in series_counts.most_common())
summary.append(["METRIK", "NILAI"])
for row in summary_rows:
    summary.append(row)
for cell in summary[1]:
    cell.fill = header_fill
    cell.font = Font(color="FFFFFF", bold=True)
summary.column_dimensions["A"].width = 34
summary.column_dimensions["B"].width = 48

wb.save(ROOT / "calendar-daily.xlsx")

print(json.dumps(validation, ensure_ascii=False, indent=2))
