# Panduan LinkedIn — Project Section & Featured Post

## ⚠️ Dua tempat berbeda, jangan dicampur

| | **Projects** (di profil) | **Featured** (di profil) |
|---|---|---|
| Tujuan | Tampilkan karya per-project | Tampilkan post/tautan pilihan |
| Isi | Nama, URL, deskripsi, gambar | Post atau artikel |
| Tampil | Grid di profil | Baris "Featured" di profil |
| Audiens | Rekrutor yang scroll cepat | Orang yang baca feed |

**Isi keduanya.** Featured untuk post (= orang bersafar), Projects untuk portofolio (= yang Sedang memilih kamu).

---

## 1️⃣ PROJECTS — yang baru saja dibuat

### Cara menambahkan

**Profil → klik ikon "+" di sidebar → "Add project"**

Isi form:

| Field | Isi |
|---|---|
| **Project name** | `VIGIL — Real-Time Construction APD Detection` |
| **Project URL** | `https://github.com/Forsaken1453/VIGIL-AI` |
| **Associated members** | Tambahkan akun kamu (opsional, tapi Isi) |
| **Description** | Lihat di bawah |
| **Image** | `docs\linkedin_project_card.jpg` |

### Deskripsi (copy-paste)

> **Real-time safety helmet & APD detection dengan YOLO11 — dilatih dari nol di laptop RTX 3050 6 GB, jalan 100% on-device.**
>
> Saya membangun VIGIL untuk mendeteksi HELM dan APD lengkap (11 kelas: helmet, vest, gloves, boots, goggles) sekaligus menandai pekerja yang TIDAK memakai APD.
>
> **Yang membuat ini tidak sesederhana kelihatannya:** mendeteksi "ada helmeter" itu mudah, tetapi mendeteksi "tidak ada helmeter" jauh lebih sulit — itu keputusan dari ketiadaan objek, bukan pengamatan langsung. Di hasilnya, kelas HELM 0.78 mAP, tapi kelas TANPA HELM hanya 0.40.
>
> **Hasil (RTX 3050 6 GB, 1.416 gambar, 60 epoch):**
> mAP@50 0.624 · 84 FPS · inference 10 ms · training 25 menit · model 18 MB
>
> **Stack:** Python 3.12, PyTorch 2.11 (CUDA 12.8), Ultralytics YOLO11, CustomTkinter, OpenCV
> **Engineering:** 81 unit test · GitHub Actions CI (Python 3.11 + 3.12) · ruff clean
> **Dataset:** Ultralytics Construction-PPE (AGPL-3.0)
>
> Model, kode, dan grafik training terbuka untuk ditinjau.

*(±1.450 karakter — masih jauh di bawah batas 3.000 karakter)*

### Gambar

**File:** `docs\linkedin_project_card.jpg` (1200×627, 96 KB)

> ⚠️ **Perhatian:** LinkedIn **auto-crop** gambar project dengan rasio berbeda. Kalau card-nya terpotong atau teks-nya kepotong, buka preview sebelum menyimpan dan sesuaikan.

---

## 2️⃣ FEATURED — untuk post / tautan

### Yang ditampilkan

| Item | Alasan |
|---|---|
| **Post dengan GIF** | Umpan LinkedIn, tempat orang ditemukan |
| **Featured** | Menautkan post itu ke profil |

### Cara menambahkan Featured

1. Buka post-nya
2. **⋯ (tiga titik)** → **"Add to featured"**

---

## 3️⃣ POST — pilih SATU variasi

Draft lengkap: `docs\LINKEDIN_DRAFT.md`

Upload: `docs\demo.gif` (2.5 MB)

### Specifications gambar post (2026)

| Jenis | Ukuran | Rasio | Maks |
|---|---|---|---|
| **Single image** | 1200 × 627 | 1.91:1 | 5 MB |
| **Multiple images** | 1080 × 1080 | 1:1 | 10 MB |
| **Document/Carousel** | 1080 × 1080 | 1:1 | 100 MB |

GIF ikut "image" → maks 5 MB. `demo.gif` = 2.5 MB ✅ aman.

---

## 4️⃣ Urutan Eksekusi

| # | Langkah | Waktu |
|---|---|---|
| 1 | Tambah **Project** (pakai card + deskripsi di atas) | 5 mnt |
| 2 | Upload **post** dengan `demo.gif` | 10 mnt |
| 3 | **Add to featured** | 1 mnt |
| 4 | Balas komentar 1 jam pertama | — |

---

## 5️⃣ Kenapa Featured penting

Banyak orang **tidak scroll sampai Featured**. Kalau Featured kosong, project kamu bisa terlihat bagus di post tapi **tidak ditemukan** saat rekrutor cek profil.

Featured = penanda "ini karya saya, klik."

---

## 💡 Pertanyaan yang biasanya muncul & jawabannya

**"mAP-nya cuma 0.62? Kenapa rendah?"**

> Karena dataset-nya cuma 1.416 gambar dengan 11 kelas yang saling berkaitan. Untuk task deteksi APD, 0.62 sebenarnya wajar — terutama di kelas negatif yang mengimplikasikan ketiadaan objek. Yang lebih penting dari angka tunggal adalah konsistensinya: kelas HELM 0.78, kelas TANPA HELM 0.40, dan hampir tidak ada false positive di kelas yang lebih tinggi.

**"Bisa jalan di laptop saya?"**

> Bisa, asal ada GPU NVIDIA minimal 6 GB VRAM. Kebutuhan minimum: Python 3.10+, CUDA 12.8. Model-nya hanya 18 MB dan inference-nya 10 ms per frame.

---

## ✅ Checklist

- [ ] Profile photo & banner LinkedIn sudah profesional
- [ ] **Project** ditambahkan (card + deskripsi)
- [ ] **Post** terupload dengan GIF
- [ ] **Featured** ditambahkan
- [ ] Deskripsi project mengukur limit karakter (tidak exceed)
- [ ] Gambar tidak ter-crop