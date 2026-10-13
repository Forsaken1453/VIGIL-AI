# Isi Form "Tambahkan Proyek" LinkedIn — VIGIL

Semuanya sudah diverifikasi **tidak kepotong**. Salin-paste langsung.

---

## 📝 NAMA PROYEK — kolom atas

Batas: 255 karakter · Dipakai: **69**

```
VIGIL - Real-Time Construction Safety Helmet & APD Detection (YOLO11)
```

> Jangan pakai emoji di nama — LinkedIn Projects menampilkannya polos di grid,
> dan emoji terlihat kurang profesional di konteks portofolio formal.

---

## 📄 DESKRIPSI — kolom kedua

Batas: 2.000 karakter · Dipakai: **1.385** ✅

```
Real-time construction safety detection yang berjalan penuh di laptop - tidak ada cloud, tidak ada API. Saya melatih model dari nol untuk mengenali 11 kelas alat pelindung diri (APD), sekaligus menandai pekerja yang TIDAK menggunakan APD.

APA YANG MEMBUAT INI SULIT: mendeteksi "ada helmeter" itu mudah, tetapi mendeteksi "tidak ada helmeter" jauh lebih sulit - itu keputusan dari ketiadaan objek, bukan pengamatan langsung. Di hasil training saya, kelas HELM mencapai 0.78 mAP, tapi kelas TANPA HELM hanya 0.40. Saya menutup ini secara jujur di README, bukan disembunyikan.

HASIL (NVIDIA RTX 3050 6 GB VRAM, dataset 1.416 gambar, 60 epoch):
- mAP@50: 0.624 (Precision 0.628 / Recall 0.624)
- 84 FPS real-time, inference 10 ms/frame (FP16)
- Waktu training: 25 menit
- Ukuran model: 18 MB

YANG SAYA KERJAKAN SENDIRI:
- Fine-tune YOLO11 pada domain APD konstruksi
- Bangun GUI desktop (CustomTkinter): preview webcam live, HUD FPS, event log
- Rekam hasil deteksi ke MP4 + event log JSONL
- Auto-pilih kamera: cek brightness tiap kamera, lewati yang tertutup
- 81 unit test + GitHub Actions CI (Python 3.11 & 3.12) + ruff lint bersih

STACK:
Python 3.12 | PyTorch 2.11 (CUDA 12.8) | Ultralytics YOLO11 | CustomTkinter | OpenCV

DATASET: Ultralytics Construction-PPE (1.416 gambar, AGPL-3.0), dipakai sesuai lisensinya.

Model, kode sumber, dan grafik training terbuka untuk ditinjau.
```

> **Kenapa deskripsi ini efektif:** 4 blok yang masing-masing menjawab pertanyaan berbeda —
> *apa* itu (baris 1–2) · *mengapa sulit* (paragraf 2) · *buktinya* (hasil) · *kualitas
> engineering* (test + CI). Rekrutor technical mencari angka dan bukti, bukan deskripsi
> marketing.

---

## 🏷️ KEAHLIAN — pilih 5, jangan lebih

Maksimal 5. **LinkedIn juga menampilkannya di bagian Keahlian profilmu**, jadi
pilih yang benar-benar kamu kuasai — jangan hanya yang terlihat keren.

| # | Keahlian | Alasan |
|---|---|---|
| 1 | **Computer Vision** |-domain inti project ini |
| 2 | **Object Detection** | teknik spesifik yang dikuasai |
| 3 | **YOLO** | tools yang dipakai |
| 4 | **Python** | bahasa |
| 5 | **PyTorch** | framework |

> ⚠️ Pilih yang **benar-benar bisa kamu jawab** kalau ditanya saat interview.
> LinkedIn Projects bisa dipakai sebagai bahan diskusi technical. Kalau pilih
> "Deep Learning" tapi belum paham loss function, itu bumerang.

---

## 🖼️ MEDIA — scroll ke bawah

Maksimal 50 item. LinkIn menyediakan **4 jenis**: gambar · dokumen · situs web ·
presentasi.

### Yang wajib diisi (3)

| Jenis | File | Kenapa |
|---|---|---|
| **Gambar** | `docs\linkedin_project_card.jpg` | Thumbnail utama yang tampil di grid |
| **Gambar** | `docs\detections_grid.jpg` | Bukti output di test set |
| **Gambar** | `docs\gui_screenshot.jpg` | Bukti aplikasinya jalan |

### Yang sangat disarankan (2)

| Jenis | File | Kenapa |
|---|---|---|
| **Situs web** | `https://github.com/Forsaken1453/VIGIL-AI` | Langsung bisa diklik & dijalankan |
| **Gambar** | `docs\confusion_matrix.png` | Menyidlih yang不懂 AI, sangat cepat dinilai kompeten |

### Kalau mau nilai tambah (opsional)

| Jenis | File |
|---|---|
| **Dokumen** | Upload `README.md` sebagai PDF (`docs\README.pdf`) |
| **Gambar** | `docs\training_curves.png` |
| **Gambar** | `docs\pr_curve.png` |
| **Gambar** | `docs\f1_curve.png` |

> **Catatan:** kolom URL terpisah di bagian atas form (yang terlihat di screenshot
> kamu) adalah untuk **link proyek**. Link GitHub juga bisa dipasang lewat
> Media → Situs web. Kalau ada keduanya yang sama, tidak masalah.

---

## ✅ Checklist Sebelum Klik "Simpan"

- [ ] Nama proyek terisi (69/255)
- [ ] Deskripsi terisi (1.385/2.000) — cek angka di pojok kanan bawah
- [ ] **5 keahlian** dipilih
- [ ] Minimal 1 gambar terupload
- [ ] Card `linkedin_project_card.jpg` sebagai gambar utama
- [ ] Preview card tidak ter-crop
- [ ] Klik **Simpan**

---

## ⚠️ Dua kesalahan yang sering terjadi

**1. Deskripsi terlalu pakai singkatan**

"AIP, ML, CV" tidak langsung menjelaskan apa yang kamu kerjakan kepada
orang yang memindai profil dengan cepat. Tulis lengkapnya di kalimat pertama.

**2. Terlalu banyak angka tanpa konteks**

Angka saja tidak berarti apa-apa. "84 FPS" tanpa menyebut "di RTX 3050 6 GB"
bisa terdengar seperti marketing. Sebutkan hardware-nya.

---

## 🎯 Setelah Simpan

Tambahkan juga ke **Featured** lewat post (bukan dari form ini):

1. Upload post dengan `docs\demo.gif` (2.5 MB)
2. Buka post → **⋯** → **"Add to featured"**

Caption lengkap ada di `docs\LINKEDIN_DRAFT.md`.