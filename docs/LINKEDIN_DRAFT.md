# Draft LinkedIn Post — VIGIL

> Angka di draft ini sudah diverifikasi terhadap `weights/vigil_ppe.metrics.json`.
> Kalau kamu retrain model, **update angkanya** — jangan pakai angka lama.

---

## ✨ VERSI FINAL (pakai ini)

---

**[upload: `docs/demo.gif`]**

Saya menamai project ini **VIGIL** — dari Latin *vigilare*, "berjaga".

Karena itu persis apa yang dia lakukan: kamera yang tidak pernah tidur, langsung
menandai begitu ada pekerja yang tidak memakai helmeter.

---

Masalahnya kelihatan sepele — "deteksi orang yang pakai helm". Tapi begitu saya
mulai dikerjakan, ternyata tidak sesederhana itu.

**1. "Deteksi pakai helm" ≠ "deteksi tidak pakai helm"**

Saya butuh 11 kelas sekaligus: helmet, vest, gloves, boots, goggles — **dan**
versi negatifnya (`no_helmet`, `no_goggle`, …).

Melihat helmeter itu mudah. Menyimpulkan "tidak ada helmeter" jauh lebih sulit,
karena itu keputusan dari *ketiadaan*, bukan pengamatan langsung.

**2. Hardware-nya kecil**

Laptop RTX 3050 dengan **6 GB VRAM** — bukan 24 GB seperti kebanyakan demo
computer vision. Almost semua keputusan (batch size, precision, ukuran model)
dibatasi angka itu.

**3. Constraint yang tidak ada di most tutorial**

Disk C: saya penuh. Semua project — termasuk cache pip dan PyTorch — saya
pindahkan ke drive D:..app ini 100% on-device, tidak ada yang masuk cloud.

---

### Hasil

| Metrik | Nilai |
|---|---|
| **mAP@50** | **0.624** |
| Kecepatan | **84 FPS** real-time |
| Inference | 10.3 ms/frame |
| Waktu training | 25 menit (RTX 3050, 60 epoch) |
| Model size | 18 MB |

Saya train dua ukuran (YOLO11n & YOLO11s) lalu pilih yang **s** — mAP naik 5%
dengan biaya kecepatan cuma 3%.

---

### Bagian yang **tidak** berhasil

Kelas `no_helmet` cuma **mAP 0.40**. `no_boots` cuma **0.14**.

Saya tidak tutup-tutupi ini. Alasannya bukan kebetulan:

- "Tidak memakai" adalah kondisi **negatif** — harus disimpulkan dari ketiadaan
  objek, jauh lebih ambigu secara visual
- `no_boots` cuma punya **88 instance** di data training (paling langka dari 11 kelas)

Kalau saya cuma tunjukkan screenshot yang manis, project ini kelihatan jauh lebih
bagus. Tapi justru angka yang jujur yang bikin orang percaya sisinya.

---

### Yang bikin saya puas

Bukan mAP-nya — tapi karena saya **tahu batasnya**.

Saya bisa bilang ke rekan-rekan: *"untuk monitoring helm, model ini siap
produksi. Untuk deteksi ketiadaan footwear, belum."*

Itu lebih berguna daripada klaim muluk.

---

**Stack:** Python 3.12 · PyTorch 2.11 (CUDA 12.8) · Ultralytics YOLO11 ·
CustomTkinter · OpenCV

**Dataset:** Ultralytics Construction-PPE — 1.416 gambar, 11 kelas (AGPL-3.0)

**Repo:** https://github.com/Forsaken1453/VIGIL-AI

---

Pertanyaan yang ingin saya ajukan: bagaimana cara menaikkan performa kelas
negatif (`no_*`)?

Apakah *person-conditioned detection* (deteksi helmeter **hanya di dalam bbox
person**) lebih masuk akal daripada membuat kelas `no_helmet` terpisah? Secara
teori itu kelihatan lebih konsisten, tapi saya belum coba.

Pernahkah Anda menangani masalah serupa di domain Anda?

---

#ComputerVision #YOLO #MachineLearning #DeepLearning #ObjectDetection
#ConstructionTech #SafetyFirst #PyTorch #EdgeAI #ComputerVisionEngineering

---

## 📝 Variasi (pilih salah satu)

### Variasi B — Pendek & punchy

**[upload: `docs/demo.gif`]**

Dari "AI bisa deteksi helmeter" ke "ini seberapa akuratnya, dan ini di mana
gagal".

Saya selesai bikin **VIGIL** — detektor APD konstruksi real-time, dilatih dari
nol di laptop RTX 3050 6GB.

📊 mAP@50 **0.624** · ⚡ **84 FPS** · ⏱️ training 25 menit

Yang paling menarik justru bukan skornya.

Kelas `no_helmet` cuma **0.40 mAP**. Model ini sangat jago bilang "ada
helmeter" — tapi jauh lebih buruk bilang "tidak ada helmeter".

Kenapa? Karena "tidak ada" itu **keputusan**, bukan **pengamatan**.

Repo: https://github.com/Forsaken1453/VIGIL-AI

Pernahkah Anda faced masalah serupa?

---

### Variasi C — Technical / data-driven

Saya mengukur where YOLO11 actually breaks di domain PPE detection.

Setup: YOLO11s, 1.416 gambar (Ultralytics Construction-PPE), 60 epoch,
RTX 3050 6GB, 640px, FP16.

**Overall:** mAP@50 0.624 · P 0.628 · R 0.624

**Per-kelas (mAP@50):**

| Kelas | mAP@50 |
|---|---|
| Person | 0.918 |
| gloves | 0.852 |
| goggles | 0.840 |
| vest | 0.839 |
| boots | 0.817 |
| helmet | 0.783 |
| none | 0.548 |
| **no_helmet** | **0.399** |
| no_goggle | 0.396 |
| no_gloves | 0.329 |
| **no_boots** | **0.142** |

Polanya jelas: kelas *presence* (helmet, vest, gloves) kuat 0.78–0.92. Kelas
*absence* (no_helmet, no_boots) anjlok di 0.14–0.40.

Wajar — "ada X" bisa diamati langsung, "tidak ada X" harus disimpulkan dari
ketiadaan. Dan no_boots cuma punya 88 instance di train.

Pertanyaan terbuka: apakah *hierarchical detection* (person → crop → deteksi APD
di dalamnya) akan menutup gap ini? Saya belum mengujinya.

Repo + kode lengkap: https://github.com/Forsaken1453/VIGIL-AI

---

## ✅ Checklist sebelum posting

- [x] Repo GitHub publik sudah di-push
- [x] GIF demo dibuat (`docs/demo.gif`, 2.5 MB)
- [x] Screenshot GUI dengan deteksi aktif + FPS terlihat
- [x] Angka draft cocok dengan `weights/vigil_ppe.metrics.json`
- [ ] **Upload GIF ke post** (bukan hanya link repo)
- [ ] **Paste URL repo** di baris Repo
- [ ] **Pilih 1 variasi** di atas (jangan post lebih dari 1)

## 📌 Tips

- **Post hari kerja** (Sen–Kam), **08.00–10.00** — jam paling rekrutor aktif
- **Hook 3 baris pertama** yang muncul sebelum "…see more" harus bikin penasaran
- **Balas komentar dalam 1 jam pertama** — engagement di jam pertama menentukan
  apakah post ini akan viral atau mati
- Kalau ada yang nanya "kenapa mAP-nya cuma 0.62?", **jawaban jujur justru
  magnet** — itu konten follow-up yang bagus sendiri