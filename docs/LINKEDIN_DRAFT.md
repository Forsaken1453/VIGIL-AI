# Draft LinkedIn Post

## Versi 2 — Problem → Solution → Result (paling direkomendasikan)

> **Judul:** Saya membangun AI untuk memantau pemakaian helm di lokasi konstruksi — lalu mengukur hasilnya dengan jujur, termasuk bagian yang belum berhasil

---

Masalah ini kelihatan sederhana: "deteksi orang yang pakai helm". Tapi begitu
saya mulai dikerjakan, ternyata tidak sesederhana itu.

**1. Bukan "model AI" generik.** Saya butuh deteksi 11 kelas sekaligus —
helmet, vest, gloves, boots, goggles — **dan** versi negatifnya
(`no_helmet`, `no_goggle`, …). Mendeteksi "ada helmeter" itu mudah.
Mendeteksi "tidak ada helmeter" jauh lebih sulit.

**2. Hardware terbatas.** Laptop RTX 3050 **6 GB VRAM** — bukan 24 GB seperti
kebanyakan post computer vision. Semua keputusan (batch size, precision,
model size) dibatasi oleh angka itu.

**3. Disk C: penuh.** Seluruh project dipindah ke drive D:, termasuk cache
pip dan torch, supaya tidak ada yang kena.

### Hasil (RTX 3050 6GB, 1.416 gambar, 60 epoch)

| | |
|---|---|
| **mAP@50** | **0.624** |
| Kecepatan | **84 FPS** real-time |
| Inference | 10.3 ms/frame |
| Waktu training | 25 menit |

### Bagian yang **tidak** berhasil — dan saya tidak mau disembunyikan

Kelas `no_helmet` hanya **mAP 0.40**, dan `no_boots` hanya **0.14**.

Alasannya bukan kebetulan: "tidak memakai" adalah kondisi *negatif*. Model
harus menyimpulkannya dari *ketiadaan* objek — jauh lebih ambigu secara visual
daripada melihat helmeter secara langsung. Ditambah `no_boots` cuma punya 88
instance di data training.

Kalau saya hanya menampilkan screenshot yang manis, project ini akan terlihat
jauh lebih baik. Tapi angka yang jujur justru yang bikin orang percaya sisinya.

### Yang membuat saya puas

Bukan mAP-nya. Tapi karena saya **tahu batasnya**. Saya bisa bilang ke rekan
rekan: "untuk monitoring helm, model ini siap produksi. Untuk deteksi
ketiadaan footwear, belum." Itu lebih berguna daripada klaim muluk.

---

**Stack:** Python 3.12 · PyTorch 2.11 (CUDA 12.8) · Ultralytics YOLO11 ·
CustomTkinter · OpenCV
**Dataset:** Ultralytics Construction-PPE (1.416 gambar, AGPL-3.0)
**Repo:** [link]

Diskusi yang welcome — terutama: bagaimana cara menaikkan performa kelas
negatif (`no_*`)? Apakah contrastive conditioning atau hierarchical detection
lebih masuk akal di sini?

---

## Ide caption singkat (alternatif)

**From "AI can detect helmets" to "here's exactly how well, and here's where it
breaks."**

Saya baru saja menyelesaikan HelmetGuard AI — detektor APD konstruksi real-time
yang dilatih dari nol di laptop RTX 3050 6GB saya.

📊 mAP@50 0.624 · ⚡ 84 FPS · ⏱️ training 25 menit

Yang paling menarik justru bukan skornya — tapi kelas `no_helmet` yang cuma
0.40 mAP. Model ini sangat jago bilang "ada helmeter", tapi jauh lebih buruk
bilang "tidak ada helmeter".

Mengapa? Karena "tidak ada" itu keputusan, bukan pengamatan.

Ada yang pernah menangani masalah serupa di domain Anda?

---

## Checklist sebelum posting

- [ ] Repo GitHub publik sudah di-push (tanpa `.venv`, `data/`, `runs/`, `*.pt` besar)
- [ ] `docs/demo_custom_model.jpg` sudah jadi GIF pendek (30–60 detik)
- [ ] Screenshot GUI dengan deteksi aktif + FPS terlihat
- [ ] Tabel metrik cocok dengan `runs/*/metrics.json`
- [ ] Tambahkan hashtag: `#ComputerVision #YOLO #MachineLearning #DeepLearning
      #ObjectDetection #ConstructionTech #SafetyFirst #PyTorch`