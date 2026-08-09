#!/usr/bin/env python3
"""Build the approved 100-day Arga Tirta Threads queue and real-photo assets."""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "arga-tirta-website-cinematic" / "img"
ASSET_ROOT = ROOT / "public" / "threads-assets"
PLAN_PATH = ROOT / "threads-content-plan.json"
START_DATE = date(2026, 8, 10)
WIB = timezone(timedelta(hours=7))
SITE = "https://argatirta.web.id"
WA = "https://wa.me/628128787299"


GALLERY_SEQUENCE = [
    "real-banner.webp",
    "real-01.webp",
    "real-02.webp",
    "real-03.webp",
    "real-05.webp",
    "real-08.webp",
]

PHOTO_DAYS = {3, 6, 10, 13, 17, 20}

GALLERY_STORIES = {
    "real-banner.webp": {
        "lead": "Foto ini menunjukkan unit depot Arga Tirta yang sudah selesai dirakit dan siap dikirim ke lokasi pelanggan.",
        "alt": "Unit depot air minum Arga Tirta selesai dirakit dan siap dikirim serta dipasang.",
        "topic": "Unit siap kirim",
        "lesson": "Sebelum unit berangkat, lokasi pelanggan juga harus benar-benar siap. Instalasi yang rapi dimulai dari ukuran ruang dan jalur masuk yang jelas, bukan dari perkiraan saat unit sudah tiba.",
        "checks": ["akses unit menuju lokasi", "ukuran ruang dan jarak servis", "kesiapan listrik, tandon, dan pipa"],
        "question": "Lokasi depot Anda sudah diukur sampai jalur masuk unitnya?",
    },
    "real-01.webp": {
        "lead": "Di foto ini pelanggan dan keluarganya berdiri di depan unit depot yang sudah terpasang dan menyala.",
        "alt": "Pelanggan dan keluarganya bersama unit depot Arga Tirta yang sudah terpasang.",
        "topic": "Unit siap beroperasi",
        "lesson": "Mesin menyala adalah awal operasional, bukan akhir pekerjaan. Pemilik perlu memahami kebiasaan harian yang menjaga hasil tetap konsisten setelah tim instalasi pulang.",
        "checks": ["SOP buka dan tutup", "jadwal sanitasi serta penggantian filter", "kontak dukungan saat muncul perubahan"],
        "question": "Siapa yang akan memegang checklist harian di depot Anda?",
    },
    "real-02.webp": {
        "lead": "Di foto ini saya sedang berjabat tangan dengan pelanggan saat serah terima unit Arga Tirta.",
        "alt": "Arga Tirta berjabat tangan dengan pelanggan saat serah terima unit depot.",
        "topic": "Serah terima pelanggan",
        "lesson": "Jabat tangan bukan sekadar foto penutup. Pada tahap ini pelanggan harus menerima penjelasan unit, cara operasi, jadwal perawatan, serta jalur komunikasi setelah pemasangan.",
        "checks": ["spesifikasi dan hasil pekerjaan", "pelatihan operator", "garansi serta kontak layanan"],
        "question": "Saat serah terima, bagian apa yang paling ingin Anda pahami lebih dulu?",
    },
    "real-03.webp": {
        "lead": "Foto ini memperlihatkan unit RO dan mineral yang sudah terpasang rapi di lokasi pelanggan.",
        "alt": "Unit depot RO dan mineral Arga Tirta terpasang rapi di lokasi pelanggan.",
        "topic": "Sistem RO dan mineral",
        "lesson": "Susunan unit terlihat sederhana dari depan, tetapi pemilihannya tetap harus mengikuti karakter air baku, target kapasitas, dan ruang untuk perawatan rutin.",
        "checks": ["hasil uji air baku", "target produksi harian", "akses penggantian media dan servis"],
        "question": "Target produksi depot Anda berapa galon per hari?",
    },
    "real-05.webp": {
        "lead": "Foto lapangan ini memperlihatkan ruang pengisian, lampu UV, housing, dan tabung filtrasi dalam satu alur kerja.",
        "alt": "Ruang pengisian dan rangkaian filtrasi depot air minum Arga Tirta.",
        "topic": "Alur filtrasi dan pengisian",
        "lesson": "Peralatan yang lengkap tetap bergantung pada kebiasaan operator. Tekanan, jadwal filter, kebersihan nozzle, dan sanitasi perlu dicatat agar masalah terlihat sebelum mengganggu pelanggan.",
        "checks": ["tekanan dan debit", "jadwal filter serta sanitasi", "kebersihan galon dan nozzle"],
        "question": "Bagian mana yang paling sering diperiksa operator setiap pagi?",
    },
    "real-08.webp": {
        "lead": "Di foto ini kami berdiri bersama pemilik depot dan banner usaha mereka setelah instalasi selesai.",
        "alt": "Tim Arga Tirta bersama pemilik depot dan banner usaha setelah instalasi selesai.",
        "topic": "Identitas usaha pelanggan",
        "lesson": "Depot bukan hanya soal mesin. Nama usaha, nomor yang mudah dihubungi, pelayanan, dan proses yang konsisten membuat pelanggan lokal lebih mudah mengingat dan mempercayainya.",
        "checks": ["nama serta kontak terbaca", "janji layanan yang realistis", "catatan pelanggan dan pembelian ulang"],
        "question": "Apa satu kalimat yang ingin diingat pelanggan dari depot Anda?",
    },
}


# topic | business risk | three concrete checks | question for the reader
RAW_TOPICS = """
Sumber air|Mesin mahal tidak menolong kalau karakter air bakunya tidak dipahami|asal air dan perubahan musim;bau warna dan endapan;hasil uji laboratorium terbaru|Sumber air di lokasi Anda sumur atau jaringan perpipaan?
Uji laboratorium|Mengandalkan rasa dan kejernihan saja membuat keputusan filter menjadi tebakan|parameter yang diuji;waktu pengambilan sampel;catatan perubahan hasil|Kapan terakhir sumber air Anda diuji?
TDS|Angka TDS sering dianggap sebagai vonis mutu padahal hanya satu petunjuk|ukur dengan alat terkalibrasi;bandingkan sebelum dan sesudah proses;baca bersama hasil uji lain|Selama ini Anda memakai TDS untuk keputusan apa?
Bau dan rasa|Keluhan pelanggan biasanya muncul lebih cepat daripada alarm mesin|cek sumber air;cek karbon aktif dan sanitasi;uji produk setelah mesin lama berhenti|Keluhan yang paling sering Anda dengar soal rasa atau bau apa?
Kekeruhan|Air tampak jernih belum tentu proses penyaringannya konsisten|lihat tren bukan satu angka;cek endapan tandon;cek tekanan antar tahap|Apakah Anda punya catatan perubahan kekeruhan?
pH|Memasang komponen tanpa memahami pH dapat memperpendek umur media|ukur air baku dan produk;cek alat ukur;catat perubahan musiman|Berapa pH air baku terakhir yang Anda ukur?
Risiko mikrobiologi|Masalah higienitas sering datang dari titik kecil setelah proses utama|jadwal sanitasi;penutup tandon dan jalur pipa;cara operator memegang tutup serta nozzle|Bagian mana yang paling sulit dijaga konsisten?
Tandon air baku|Tandon yang luput dibersihkan membuat beban filter terus naik|kondisi tutup;endapan dasar;jadwal kuras dan dokumentasi|Kapan tandon terakhir dikuras?
Prefilter|Prefilter yang terlalu jarang diganti membebani tahap berikutnya|warna dan tekanan;jam operasi;stok pengganti|Patokan penggantian Anda waktu atau kondisi?
Filter sedimen|Cartridge murah bisa menjadi mahal saat aliran turun di jam sibuk|mikron yang sesuai;beda tekanan;riwayat penggantian|Berapa lama cartridge bertahan di depot Anda?
Karbon aktif|Karbon aktif tidak bekerja optimal selamanya hanya karena air masih terlihat jernih|bau dan rasa;kapasitas media;prosedur bilas setelah penggantian|Apa tanda yang Anda pakai untuk mengganti karbon?
Media resin|Resin yang dibiarkan jenuh membuat hasil berubah pelan-pelan tanpa disadari|kondisi regenerasi;takaran bahan;hasil sebelum dan sesudah|Apakah regenerasi sudah dicatat setiap kali dilakukan?
Membran RO|Mengejar debit dengan tekanan yang salah bisa mempercepat penurunan membran|tekanan kerja;rasio produk dan buangan;tren kualitas produk|Apakah Anda mencatat debit produk setiap minggu?
Lampu UV|Lampu menyala bukan bukti intensitasnya masih cukup|umur lampu;selongsong kuarsa;jam operasi|Kapan lampu UV terakhir diganti?
Ozon|Ozon bukan alasan untuk melonggarkan kebersihan di tahap lain|dosis dan waktu kontak;jalur distribusi;perawatan generator|Apakah sistem ozon diperiksa terjadwal?
Housing stainless|Housing yang terlihat kokoh tetap perlu diperiksa seal dan kebersihannya|O-ring;ulir dan klem;prosedur buka pasang|Pernah ada rembesan setelah servis?
Pompa|Pompa yang dipilih hanya dari harga sering gagal memenuhi debit pada tekanan nyata|kurva pompa;tekanan operasi;suara dan panas|Pompa Anda paling sering bermasalah di bagian apa?
Pressure gauge|Tanpa angka tekanan operator baru sadar setelah aliran sudah turun|gauge sebelum dan sesudah filter;akurasi jarum;batas tindakan|Berapa tekanan normal sistem Anda?
Debit produksi|Kapasitas brosur tidak selalu sama dengan kapasitas di kondisi lapangan|debit per jam;waktu puncak;waktu tunggu pelanggan|Target galon per hari Anda berapa?
Umur membran|Membran tidak punya tanggal mati yang sama untuk semua sumber air|tren debit;tren kualitas;riwayat cleaning dan tekanan|Data apa yang Anda simpan sebelum mengganti membran?
Jadwal cartridge|Mengganti terlalu cepat boros tetapi terlambat juga menambah beban sistem|tanggal pasang;beda tekanan;kondisi visual|Sudah ada kartu servis untuk setiap housing?
Backwash|Backwash asal lama belum tentu membersihkan media dengan benar|arah aliran;debit backwash;air bilas sebelum produksi|Berapa lama SOP backwash Anda?
Sanitasi berkala|Depot terlihat bersih pada pagi hari belum menjamin jalurnya higienis sepanjang minggu|jadwal;larutan dan prosedur;verifikasi setelah sanitasi|Siapa yang menandatangani log sanitasi?
Pipa food grade|Pipa adalah jalur produk dan sering tidak terlihat oleh pelanggan|material;dead leg;kemudahan pembilasan|Ada jalur pipa yang sulit dikuras?
Seal dan kebocoran|Rembesan kecil bisa berubah menjadi downtime ketika depot sedang ramai|stok O-ring;torsi pemasangan;cek setelah tekanan naik|Seal ukuran apa yang paling sering habis?
Tutup galon|Tutup adalah titik sentuh terakhir sebelum produk dibawa pelanggan|penyimpanan tertutup;cara operator mengambil;kesesuaian ukuran leher|Berapa pemakaian tutup per hari?
Cuci galon|Galon pelanggan datang dengan kondisi yang sangat beragam|inspeksi awal;urutan cuci dan bilas;kriteria penolakan|Kondisi galon seperti apa yang Anda tolak?
Sikat galon|Sikat yang aus hanya memutar kotoran tanpa membersihkan dengan konsisten|kondisi bulu;jadwal ganti;penyimpanan setelah dipakai|Kapan sikat terakhir diganti?
Urutan bilas|Urutan yang berubah antar operator membuat hasil sulit dilacak|SOP tertulis;durasi tiap tahap;cek acak oleh penanggung jawab|Apakah semua operator memakai urutan yang sama?
Nozzle pengisian|Nozzle bersih dapat tercemar lagi karena tangan dan posisi penyimpanan|penutup nozzle;sanitasi;larangan menyentuh ujung|Di mana nozzle diletakkan setelah tutup toko?
Ruang produksi|Debu dan lalu lintas orang ikut memengaruhi titik pengisian|pemisahan area;aliran kerja;permukaan mudah dibersihkan|Area bersih dan area kotor sudah terpisah?
Pengendalian hama|Satu celah kecil cukup membuat kebersihan depot dipertanyakan|pintu dan ventilasi;drainase;catatan pemeriksaan|Ada titik yang sering dimasuki serangga?
Kebersihan tangan|Sarung tangan bukan pengganti kebiasaan cuci tangan yang benar|waktu cuci tangan;tempat sabun;larangan memegang uang lalu nozzle|Siapa yang mengisi galon saat kasir sedang sibuk?
SOP buka toko|Masalah pagi hari biasanya berasal dari langkah pembukaan yang dilewati|flush awal;cek tekanan;cek bau rasa dan kebocoran|Apa tiga cek pertama sebelum melayani pelanggan?
SOP tutup toko|Tutup toko yang rapi mempersingkat masalah pada pagi berikutnya|bilas jalur;bersihkan area;catat stok dan anomali|Apa yang wajib dicatat sebelum pulang?
Log perawatan|Ingatan operator tidak cukup untuk mesin yang dipakai setiap hari|tanggal tindakan;angka sebelum dan sesudah;nama pelaksana|Log Anda masih di kepala atau sudah tertulis?
Jadwal uji produk|Uji hanya saat ada keluhan membuat depot selalu terlambat bereaksi|kalender sampel;laboratorium;penyimpanan hasil|Sudah ada pengingat uji berikutnya?
Audit pemasok|Harga termurah tidak berguna kalau spesifikasi dan lead time berubah|konsistensi barang;dukungan teknis;garansi dan pengiriman|Apa syarat utama memilih pemasok?
Stok sparepart|Downtime satu hari bisa lebih mahal daripada menyimpan part kritis|daftar part kritis;minimum stok;lokasi penyimpanan|Part apa yang paling lama didapat di kota Anda?
Cadangan listrik|Mati listrik di jam ramai perlu skenario yang jelas|beban prioritas;prosedur berhenti aman;komunikasi pelanggan|Apa yang Anda lakukan saat listrik padam?
Pemilihan lokasi|Ramai kendaraan belum tentu ramai pelanggan galon|kepadatan rumah;akses parkir;kompetitor dan rute antar|Lokasi Anda dekat perumahan atau jalan utama?
Peta kompetitor|Meniru harga tetangga tanpa tahu layanan mereka membuat strategi kabur|jarak;harga dan layanan;jam ramai|Berapa depot aktif dalam radius terdekat?
Penetapan harga|Harga jual yang terlihat untung bisa menipu jika biaya kecil tercecer|biaya air dan listrik;media serta tutup;sewa tenaga dan penyusutan|Kapan harga terakhir dihitung ulang?
HPP per galon|Omzet bukan laba dan saldo kas bukan ukuran biaya per galon|biaya variabel;biaya tetap;volume realistis|Sudah tahu HPP satu galon hari ini?
Biaya listrik|Tagihan total perlu dipisahkan dari beban rumah atau usaha lain|meter terpisah;jam operasi;daya pompa dan UV|Listrik depot sudah terukur sendiri?
Air buangan RO|Air buangan yang tidak dihitung membuat biaya dan efisiensi tampak lebih bagus|volume produk;volume reject;pemanfaatan yang sesuai|Rasio produk dan buangan Anda berapa?
Biaya media filter|Media dianggap murah sampai beberapa tahap jatuh tempo bersamaan|umur pakai;biaya penggantian;dana cadangan bulanan|Berapa dana perawatan yang disisihkan per galon?
Biaya tenaga kerja|Menghitung gaji tanpa jam produktif membuat kapasitas sulit dibaca|jam ramai;jumlah operator;pekerjaan nonproduksi|Kapan operator paling kewalahan?
Biaya sewa|Sewa murah di lokasi sepi dapat lebih mahal daripada lokasi kecil yang tepat|sewa per bulan;potensi volume;akses pelanggan|Berapa galon minimum untuk menutup sewa?
Titik impas|Target balik modal sering terlalu optimistis karena memakai kapasitas mesin penuh|investasi riil;marjin per galon;volume bertahap|Dalam berapa bulan target balik modal Anda?
Arus kas|Usaha bisa mencatat laba tetapi tetap kehabisan uang untuk stok dan servis|jadwal tagihan;dana perawatan;stok minimum|Pengeluaran besar berikutnya jatuh kapan?
Stok tutup|Kehabisan tutup saat mesin sehat tetap menghentikan penjualan|pemakaian harian;lead time pemasok;buffer hari ramai|Stok sekarang cukup untuk berapa hari?
Stok segel|Segel kecil sering tidak dianggap kritis sampai kualitas kemasan dipertanyakan|jenis segel;pemakaian;tempat kering dan tertutup|Segel disimpan bersama barang apa?
Minimum inventory|Stok aman bukan angka tebakan tetapi hasil pemakaian dan lead time|rata-rata harian;variasi akhir pekan;lama kirim|Barang mana yang perlu reorder hari ini?
Lead time pemasok|Harga bagus kehilangan nilai kalau barang datang setelah stok habis|waktu kirim normal;waktu kirim terburuk;alternatif pemasok|Berapa hari pengiriman terlama yang pernah terjadi?
Membandingkan vendor|Bandingkan total dukungan bukan hanya angka pada invoice|spesifikasi;garansi;respon teknisi dan ketersediaan part|Vendor Anda membantu setelah penjualan?
Spesifikasi mesin|Membeli paket terbesar sebelum punya target pasar sering mengunci modal|kualitas air baku;target debit;ruang listrik dan servis|Kapasitas dipilih dari data atau rasa aman?
Hindari overbuy|Mesin berlebih tidak otomatis membuat pelanggan datang lebih cepat|tahap investasi;utilisasi;opsi upgrade|Fitur mana yang benar-benar dipakai setiap hari?
Target kapasitas|Target produksi harus mengikuti pola pelanggan bukan kapasitas di brosur|pelanggan aktif;galon per pelanggan;jam puncak|Target harian Anda berdasarkan data apa?
Jam puncak|Antrean yang hanya terjadi satu jam tetap menentukan pengalaman pelanggan|catat kedatangan;siapkan tutup dan area cuci;atur peran operator|Jam berapa depot paling ramai?
Kecepatan layanan|Cepat tanpa urutan kerja yang rapi meningkatkan peluang langkah terlewat|layout;urutan kerja;alat siap pakai|Berapa menit rata-rata satu transaksi?
Manajemen antrean|Pelanggan lebih sabar bila tahu urutan dan perkiraan waktu|nomor antrean;komunikasi;jalur galon masuk dan keluar|Antrean sering menumpuk di proses mana?
Paket langganan|Diskon langganan harus menjaga arus kas dan tidak membingungkan pelanggan|frekuensi;masa berlaku;catatan penukaran|Pelanggan rutin Anda rata-rata isi berapa kali sebulan?
Layanan antar|Gratis antar dapat menggerus marjin bila radius tidak dihitung|radius;minimum pesanan;rute dan waktu|Berapa biaya nyata satu perjalanan antar?
Menangani keluhan|Membantah lebih cepat daripada memeriksa hanya merusak kepercayaan|catat sampel;telusuri batch dan operator;tindak lanjut pelanggan|Keluhan terakhir selesai dalam berapa lama?
Edukasi pelanggan|Pelanggan yang paham cara menyimpan galon membantu menjaga mutu setelah pembelian|tempat teduh;galon bersih;penutup tidak dibuka sembarang|Apa pesan penyimpanan yang selalu disampaikan?
Transparansi proses|Kepercayaan tumbuh saat pelanggan bisa melihat kebiasaan baik bukan hanya slogan|jadwal servis;area kerja;hasil uji yang relevan|Bagian proses mana yang bisa Anda tunjukkan?
Kepercayaan|Harga menarik membawa transaksi pertama tetapi konsistensi membawa transaksi berikutnya|rasa konsisten;kebersihan terlihat;respon keluhan|Kenapa pelanggan lama tetap kembali?
Kebersihan yang terlihat|Area depan rapi tidak menutupi selang dan sudut yang kotor|lantai;selang dan nozzle;rak tutup dan alat|Sudut mana yang paling mudah terlewat?
Identitas merek|Logo tidak menggantikan janji layanan tetapi membantu pelanggan mengingatnya|nama yang konsisten;warna dan papan;pesan utama|Apa satu kalimat yang ingin diingat pelanggan?
Papan toko|Papan besar percuma bila orang lewat tidak paham layanan dalam tiga detik|nama layanan;jam buka;kontak terbaca|Dari seberang jalan tulisan apa yang masih terbaca?
Pencarian lokal|Pelanggan dekat sering mencari dari ponsel sebelum melihat papan toko|nama alamat dan jam;foto asli;respon ulasan|Profil lokasi Anda sudah lengkap?
Follow-up WhatsApp|Pesan yang berguna membangun hubungan sedangkan broadcast terus-menerus melelahkan|izin pelanggan;isi relevan;frekuensi wajar|Pelanggan ingin diingatkan soal apa?
Database pelanggan|Nomor pelanggan tanpa catatan perilaku hanya menjadi daftar panjang|nama dan area;frekuensi;izin komunikasi|Berapa pelanggan aktif 30 hari terakhir?
Program referal|Bonus referal harus mudah dipahami dan tetap masuk hitungan marjin|siapa yang berhak;cara pencatatan;batas periode|Hadiah apa yang relevan tanpa merusak harga?
Risiko promo|Diskon yang tidak punya tujuan melatih pelanggan menunggu harga murah|target promo;durasi;ukur pelanggan kembali|Promo terakhir menghasilkan pelanggan rutin?
Harga kompetitor|Menjadi paling murah bukan satu-satunya posisi yang bisa dipilih|mutu layanan;biaya sendiri;nilai tambahan|Pelanggan memilih Anda karena harga atau kebiasaan?
Uji rasa|Sampling yang rapi bisa membuka percakapan tanpa klaim berlebihan|gelas bersih;air dari produksi terbaru;catat tanggapan|Apa kata yang paling sering dipakai pelanggan soal rasa?
Retensi|Mengejar pelanggan baru sambil mengabaikan pelanggan lama membuat biaya promosi terus naik|frekuensi ulang;alasan hilang;tindak lanjut keluhan|Berapa persen pelanggan kembali bulan berikutnya?
Pembelian ulang|Penjualan harian lebih mudah diprediksi bila pola repeat tercatat|jumlah pelanggan aktif;jeda pembelian;perubahan musim|Jeda rata-rata antar pembelian berapa hari?
Cabang kedua|Cabang baru menggandakan masalah bila SOP cabang pertama belum stabil|angka laba;operator pengganti;kontrol kualitas|Cabang pertama bisa berjalan tanpa pemilik berapa hari?
Kemitraan|Nama besar tidak menghapus kewajiban memeriksa angka dan dukungan teknis|biaya awal;royalti dan bahan wajib;hak wilayah|Dokumen apa yang sudah Anda baca sampai detail?
Rekrut operator|Orang cepat belum tentu teliti dan orang ramah tetap perlu SOP|ketelitian;kebersihan;komunikasi pelanggan|Bagian tes kerja apa yang Anda gunakan?
Pelatihan operator|Sekali diajari pada hari pertama tidak cukup untuk proses berulang|demonstrasi;cek praktik;penyegaran|Kapan pelatihan terakhir dilakukan?
Akuntabilitas operator|SOP tanpa nama pelaksana membuat kesalahan sulit ditelusuri|paraf log;shift;serah terima|Siapa yang bertanggung jawab pada shift malam?
Kontrol kas|Selisih kecil berulang lebih berbahaya daripada satu kesalahan yang cepat ditemukan|harga tetap;struk atau catatan;rekonsiliasi harian|Kas dicocokkan dengan jumlah galon setiap hari?
Rekonsiliasi penjualan|Jumlah galon adalah data fisik yang harus bertemu dengan uang dan stok tutup|galon terjual;uang masuk;tutup terpakai|Selisih paling sering muncul di angka mana?
Perawatan preventif|Servis terjadwal biasanya lebih murah daripada berhenti mendadak di jam ramai|kalender;part kritis;catatan tren|Komponen apa yang mendekati jadwal servis?
Rencana downtime|Pelanggan menilai cara Anda berkomunikasi saat mesin berhenti|nomor teknisi;estimasi;informasi ke pelanggan|Siapa yang dihubungi pertama saat produksi berhenti?
Dugaan kontaminasi|Kecepatan menghentikan dan menelusuri proses lebih penting daripada mencari alasan|hentikan distribusi;pisahkan sampel;hubungi tenaga kompeten dan dokumentasikan|Apakah tim tahu keputusan pertama yang harus diambil?
Mesin berhenti mendadak|Panik muncul ketika tidak ada daftar cek sederhana|listrik dan proteksi;tekanan dan kebocoran;riwayat alarm|Ada checklist gangguan satu halaman?
Musim banjir|Perubahan kondisi sekitar dapat mengubah beban air baku|inspeksi sumber;frekuensi pemantauan;stok media|Apa yang berubah pada air baku saat hujan panjang?
Musim kemarau|Debit sumber dan konsentrasi zat terlarut dapat berubah tanpa pemberitahuan|debit;hasil pengukuran;jam operasi|Sumber pernah turun saat kemarau?
Perubahan sumber|Mengganti sumber air tanpa kajian membuat setelan lama belum tentu cocok|sampel baru;uji;review rangkaian filter|Pernah memakai sumber cadangan?
Kepatuhan higiene|Dokumen bukan hiasan dan kebiasaan harian tetap harus mengikuti ketentuan yang berlaku|izin dan persyaratan lokal;hasil pemeriksaan;SOP dan catatan|Dokumen mana yang perlu diperbarui?
Arsip usaha|Saat inspeksi atau masalah muncul Anda perlu data yang bisa ditemukan cepat|hasil uji;invoice dan garansi;log servis|Berapa menit mencari hasil uji terakhir?
Janji mutu|Kalimat promosi harus sesuai hal yang benar-benar dikendalikan setiap hari|proses;verifikasi;respon bila meleset|Janji apa yang berani Anda ukur?
Checklist investor|Modal mesin hanya satu bagian dari usaha depot|sumber air dan lokasi;biaya kerja dan cadangan;orang dan SOP|Data apa yang masih kosong sebelum mulai?
Hitung mundur buka|Pembukaan yang tergesa membuat masalah kecil muncul di depan pelanggan pertama|uji coba;stok;simulasi layanan|Berapa hari khusus untuk trial sebelum grand opening?
Evaluasi 30 hari|Bulan pertama seharusnya menghasilkan data bukan hanya rasa capek|volume harian;keluhan dan repeat;biaya aktual|Angka apa yang paling mengejutkan bulan ini?
""".strip()


def parse_topics():
    rows = []
    for line in RAW_TOPICS.splitlines():
        topic, risk, checks, question = line.split("|")
        rows.append({"topic": topic, "risk": risk, "checks": checks.split(";"), "question": question})
    if len(rows) != 100:
        raise RuntimeError(f"Expected 100 topics, got {len(rows)}")
    return rows


def compact(text: str, limit: int = 500) -> str:
    text = "\n".join(part.strip() for part in text.strip().splitlines())
    if len(text) <= limit:
        return text
    shortened = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"
    return shortened


def cta_for(day_index: int, weekday: int, session: str) -> tuple[str, str]:
    if session != "PM" or weekday not in {0, 2, 3, 5, 6}:
        return "conversation", ""
    variants = {
        0: ("website", f"Kalau mau melihat layanan dan contoh unit Arga Tirta, cek {SITE}."),
        2: ("website", f"Detail layanan Arga Tirta ada di {SITE}."),
        3: ("whatsapp", f"Kalau ingin membahas kondisi lokasi Anda, tulis dulu kota, sumber air, dan target galon/hari ke {WA}."),
        5: ("whatsapp", f"Butuh daftar kebutuhan awal? Kirim kota, sumber air, dan target kapasitas ke {WA}."),
        6: ("mixed", f"Referensi layanan: {SITE}. Konsultasi awal: {WA}."),
    }
    return variants[weekday]


def mini_days() -> set[int]:
    # 28 evenly distributed long-form sessions across 100 days.
    return {round(1 + step * 99 / 27) for step in range(28)}


def make_morning(day_no: int, topic: dict, is_thread: bool):
    checks = topic["checks"]
    hooks = [
        f"Kalau mau buka depot isi ulang, jangan mulai dari katalog mesin dulu. Mulai dari {topic['topic'].lower()}.",
        f"Ada yang sedang menyiapkan bisnis isi ulang? Satu hal ini sering baru dipikirkan setelah uang keluar: {topic['topic'].lower()}.",
        f"Kesalahan mahal di depot sering bukan mesin rusak. Masalahnya: {topic['risk'].lower()}.",
        f"Admin mau tanya: di depot Anda, siapa yang benar-benar mencatat soal {topic['topic'].lower()}?",
    ]
    root = compact(f"{hooks[(day_no - 1) % len(hooks)]}\n\n{topic['risk']}.\n\n{topic['question']}")
    if not is_thread:
        body = compact(
            f"{root}\n\nTiga hal yang perlu dicek: 1) {checks[0]}, 2) {checks[1]}, 3) {checks[2]}. "
            "Kalau angkanya belum ada, jangan buru-buru menyimpulkan. Catat kondisi hari ini lalu bandingkan setelah tindakan."
        )
        return body, []

    replies = [
        compact(f"1/3 Mulai dari data dasar. Catat {checks[0]}. Jangan hanya menulis 'normal'; pakai angka, tanggal, foto, atau kondisi yang bisa dibandingkan."),
        compact(f"2/3 Setelah itu cek {checks[1]}. Tujuannya bukan mencari alat paling mahal, tetapi menemukan tahap mana yang berubah dan kapan perubahan mulai terjadi."),
        compact(f"3/3 Terakhir, pastikan {checks[2]}. Dari tiga catatan itu keputusan belanja, servis, atau perubahan SOP jadi lebih masuk akal. {topic['question']}"),
    ]
    return root, replies


def make_evening(day_no: int, topic: dict, cta: str, has_photo: bool):
    checks = topic["checks"]
    lead = "Foto lapangan hari ini mengingatkan kami: " if has_photo else "Catatan admin malam ini: "
    text = (
        f"{lead}{topic['risk']}.\n\n"
        f"Sebelum mengambil keputusan, cek: 1) {checks[0]}; 2) {checks[1]}; 3) {checks[2]}. "
        "Satu data kecil yang dicatat rutin lebih berguna daripada tebakan panjang saat masalah sudah terjadi.\n\n"
        f"{topic['question']}"
    )
    if cta:
        text += f"\n\n{cta}"
    return compact(text)


def make_photo_evening(topic: dict, cta: str, source_name: str):
    story = GALLERY_STORIES[source_name]
    checks = story["checks"]
    text = (
        f"{story['lead']}\n\n"
        f"{story['lesson']}\n\n"
        f"Checklist: 1) {checks[0]}; 2) {checks[1]}; 3) {checks[2]}.\n\n"
        f"{story['question']}"
    )
    if cta and len(text) + len(cta) + 2 <= 500:
        text += f"\n\n{cta}"
    return compact(text)


def make_assets():
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    sources = [SOURCE_ROOT / name for name in GALLERY_STORIES]
    missing = [str(p) for p in sources if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing real-photo sources: " + ", ".join(missing))
    outputs = {}
    for src in sources:
        with Image.open(src) as original:
            image = original.convert("RGB")
            out = ASSET_ROOT / f"gallery-{src.stem}.jpg"
            image.save(out, "JPEG", quality=94, optimize=True, progressive=True)
            outputs[src.name] = out
    return outputs


def build_plan():
    published_state = {}
    if PLAN_PATH.exists():
        existing = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        for item in existing.get("items", []):
            if item.get("status") == "published":
                published_state[item["id"]] = {
                    key: value
                    for key, value in item.items()
                    if key.startswith("published_")
                    or key in {"status", "threads_media_id", "threads_url"}
                }

    topics = parse_topics()
    photos = make_assets()
    thread_days = mini_days()
    photo_index = 0
    queue = []

    for day_no, topic in enumerate(topics, start=1):
        current = START_DATE + timedelta(days=day_no - 1)
        weekday = current.weekday()
        is_thread = day_no in thread_days
        morning, replies = make_morning(day_no, topic, is_thread)
        morning_at = datetime.combine(current, time(8, 17), WIB)
        morning_item = {
            "id": f"AT-THR-D{day_no:03d}-AM",
            "day": day_no,
            "date": current.isoformat(),
            "time_wib": "08:17",
            "scheduled_at": morning_at.isoformat(),
            "session": "AM",
            "topic": topic["topic"],
            "format": "mini_thread" if is_thread else "standalone",
            "media_type": "TEXT",
            "text": morning,
            "replies": replies,
            "cta_type": "conversation",
            "status": "queued_auto",
            "approval_status": "approved",
        }
        if morning_item["id"] in published_state:
            morning_item.update(published_state[morning_item["id"]])
        queue.append(morning_item)

        has_photo = day_no in PHOTO_DAYS
        cta_type, cta = cta_for(day_no, weekday, "PM")
        source_name = GALLERY_SEQUENCE[photo_index] if has_photo else None
        evening = (
            make_photo_evening(topic, cta, source_name)
            if has_photo
            else make_evening(day_no, topic, cta, False)
        )
        evening_at = datetime.combine(current, time(19, 17), WIB)
        item = {
            "id": f"AT-THR-D{day_no:03d}-PM",
            "day": day_no,
            "date": current.isoformat(),
            "time_wib": "19:17",
            "scheduled_at": evening_at.isoformat(),
            "session": "PM",
            "topic": GALLERY_STORIES[source_name]["topic"] if has_photo else topic["topic"],
            "format": "standalone",
            "media_type": "IMAGE" if has_photo else "TEXT",
            "text": evening,
            "replies": [],
            "cta_type": cta_type,
            "status": "queued_auto",
            "approval_status": "approved",
        }
        if has_photo:
            asset = photos[source_name]
            story = GALLERY_STORIES[source_name]
            item["asset"] = asset.relative_to(ROOT / "public").as_posix()
            item["alt_text"] = story["alt"]
            item["source_asset"] = source_name
            item["asset_original"] = True
            item["gallery_reference"] = f"{SITE}/#galeri"
            photo_index += 1
        if item["id"] in published_state:
            item.update(published_state[item["id"]])
        queue.append(item)

    payload = {
        "campaign": "Arga Tirta Threads 100 Hari",
        "timezone": "Asia/Jakarta",
        "start_date": START_DATE.isoformat(),
        "schedule": ["08:17", "19:17"],
        "website": SITE,
        "whatsapp": WA,
        "editorial_status": "approved",
        "items": queue,
    }
    PLAN_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "items": len(queue),
        "thread_sessions": sum(item["format"] == "mini_thread" for item in queue),
        "reply_posts": sum(len(item["replies"]) for item in queue),
        "photo_posts": sum(item["media_type"] == "IMAGE" for item in queue),
        "cta_posts": sum(item["cta_type"] != "conversation" for item in queue),
        "plan": str(PLAN_PATH),
    }, indent=2))


if __name__ == "__main__":
    build_plan()
