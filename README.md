# SPK Hibrida AHP–TOPSIS untuk Penentuan Posisi dan Rekomendasi Latihan Pemain Futsal

Sistem Pendukung Pengambilan Keputusan berbasis web untuk menentukan posisi terbaik pemain futsal
dan memberi rekomendasi training menuju posisi yang diinginkan.

## Menjalankan

**Cara termudah (Windows):** klik dua kali **`Jalankan Aplikasi.bat`**.
Browser terbuka otomatis di http://localhost:5000. Biarkan jendela hitam tetap terbuka selama aplikasi dipakai;
tutup jendela itu untuk menghentikan aplikasi. Saat pertama kali, file ini memasang library yang dibutuhkan (perlu internet).

Syarat: Python 3 terpasang dengan opsi *Add python.exe to PATH* (https://www.python.org/downloads/).

Untuk mengembalikan semua data ke kondisi awal, klik dua kali **`Reset Data Awal.bat`** (data lama dicadangkan otomatis).

Cara manual lewat terminal:

```bash
pip install -r requirements.txt
python app.py
```

## Akun uji coba

| Role | Username | Password |
|---|---|---|
| Super Admin (akses pelatih + approval akun & ubah password) | `superadmin` | `superadmin123` |
| Pelatih (kelola pemain, kriteria, perhitungan, log) | `pelatih` | `pelatih123` |
| Pemain (hanya lihat data & hasil sendiri) | kode pemain huruf kecil, mis. `al1`, `mx5` | `pemain123` |

Halaman pertama (`/`) adalah beranda publik berisi informasi umum, dengan tombol Login dan Buat akun.
Akun yang didaftarkan sendiri berstatus *menunggu* sampai disetujui Super Admin di menu **Akun**.
Password disimpan sebagai hash; Super Admin dapat menetapkan password baru (ditampilkan sekali), bukan membaca password lama.

## Metode

Model: **hibrida AHP–TOPSIS dengan analisis gap berbobot**. Penjelasan bagian standar, penyesuaian, dan tambahan
ada di halaman Panduan → *Kerangka metodologi*.

1. **Hierarki AHP** — Tujuan: posisi terbaik → Kriteria: 11 skill (bisa CRUD) → Alternatif: Goalkeeper, Fixo/Anchor, Ala/Flank, Pivot.
2. **Bobot AHP** — pelatih mengisi skor kebutuhan 1–9 per kriteria per posisi (High = 9, Medium = 5, Low = 1).
   Matriks perbandingan per posisi bisa **diisi manual oleh pelatih** (skala Saaty, AHP klasik; menu Perhitungan AHP →
   *Isi matriks manual*, dengan bobot & CR langsung) atau **otomatis**: `d = sᵢ − sⱼ`, `aᵢⱼ = d + 1` (d ≥ 0) atau `1/(1 − d)` (d < 0), dibatasi 1–9.
   Bobot = rata-rata baris matriks ternormalisasi; dihitung λmax, CI = (λmax − n)/(n − 1), CR = CI/RI (valid jika CR < 0,1).
3. **TOPSIS (penentu rekomendasi)** — satu perhitungan per pemain: alternatif = 4 posisi,
   matriks keputusan `x_pj` = bobot AHP kriteria j pada posisi p, bobot kriteria `w_j = s_j / Σs` (profil skill pemain),
   semua kriteria benefit. Normalisasi vektor → matriks terbobot → A⁺/A⁻ → D⁺/D⁻ → Cᵢ = D⁻/(D⁺ + D⁻).
   Posisi dengan Cᵢ tertinggi = posisi paling sesuai. Sebagai **pembanding**, TOPSIS per posisi dengan alternatif = pemain aktif
   tetap tersedia untuk melihat pemain terbaik di tiap posisi.
4. **Gap skill** — target = skor kebutuhan posisi dikonversi ke 1–10 (`round(s/9 × 10)`), gap = max(0, target − skill),
   skor prioritas = gap × bobot AHP posisi target. Diurutkan → prioritas upgrade → dipetakan ke training kriteria.

## Fitur

- Dashboard Cᵢ semua pemain × posisi, status konsistensi AHP, aktivitas terbaru.
- Analisis pemain: ranking posisi, grafik radar, gap & prioritas, rekomendasi training, export CSV/Excel, simpan hasil.
- Halaman terpisah **Perhitungan AHP** (hierarki, matriks, normalisasi, bobot, (Aw)/w, λmax, CI, CR) dan
  **Perhitungan TOPSIS** (X, R, V, A⁺, A⁻, D⁺, D⁻, Cᵢ, rank), masing-masing dengan **export PDF & Excel**
  berisi langkah lengkap untuk keempat posisi (PDF A4 landscape, kode kriteria C1…Cn + keterangan).
- **Data Master**: Data Pemain, Posisi (tambah/ubah/hapus, minimal 2), Kriteria & Skor Kebutuhan, dan Rekomendasi Training (beberapa latihan per kriteria dengan durasi & level).
- Manajemen pemain: tambah, ubah (termasuk posisi alternatif), arsip/pulihkan — tidak ada hapus.
- Hasil perhitungan disimpan sebagai snapshot; log kategori input, perhitungan, rekomendasi, akses (export CSV).
- Tiga role: Super Admin, Pelatih, Pemain; pendaftaran mandiri dengan approval; pemain hanya melihat data, hasil, dan riwayat miliknya.
- Menu atas tetap terlihat (sticky) saat halaman di-scroll.

- Halaman **Panduan** (menu `? Panduan`) berisi fungsi & cara pakai setiap halaman, menyesuaikan role; tombol membuka bagian halaman yang sedang aktif.

## Data dummy

16 pemain: GK1–GK2, AN1–AN3, AL1–AL3, PV1–PV2, dan 6 pemain multi-posisi MX1–MX6
(Anchor/Flank, Flank/Pivot, Kiper-libero, Anchor/Pivot, Universal, Flank/Anchor). Nilai skill dapat diubah pelatih.

## Struktur

- `app.py` — route, autentikasi, role, export, log
- `sppk.py` — perhitungan AHP, TOPSIS, gap
- `db.py` — skema SQLite & seed
- `templates/` — tampilan (Bootstrap + Chart.js)
