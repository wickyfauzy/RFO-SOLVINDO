import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os
import random

st.set_page_config(page_title="RFO Generator", layout="centered")
st.title("📝 Reason For Outage (RFO) Generator")

# Fungsi buat nomor tiket otomatis
def generate_ticket():
    now = datetime.now()
    kode_uniq = random.randint(100000, 99999999)
    return f"TO/DIV/RE/{now.strftime('%Y-%m-%d')}/{kode_uniq}"

# Form input
st.subheader("Informasi Pelanggan")
id_pelanggan = st.text_input("ID Pelanggan")
nama_pelanggan = st.text_input("Nama Pelanggan")
nama_link = st.text_input("Nama Link")
alamat_link = st.text_area("Alamat Link")
jenis_layanan = st.text_input("Jenis Layanan")

st.markdown("---")

st.subheader("Informasi Tiket & Gangguan")
nomor_tiket = st.text_input("Nomor Tiket", value=generate_ticket())
log_down = st.text_input("Log Down (format: YYYY-MM-DD HH:MM)")
log_up = st.text_input("Log Up (format: YYYY-MM-DD HH:MM)")
durasi_pending = st.text_input("Durasi Pending")
penyebab_pending = st.text_area("Penyebab Pending")
penyebab = st.text_area("Penyebab")
tindakan = st.text_area("Tindakan")

st.markdown("---")

st.subheader("Logo Perusahaan (Opsional)")
logo_file = st.file_uploader("Upload Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

st.markdown("---")

st.subheader("Disusun oleh")
staff = st.text_input("Nama Staff Pembuat")
manager = st.text_input("Nama Manager")

# Fungsi buat PDF pakai ReportLab
def generate_pdf(output_path, data, logo=None):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Logo jika ada
    if logo:
        c.drawImage(logo, 50, height - 80, width=100, preserveAspectRatio=True)

    # Judul
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, height - 50, "Reason For Outage (RFO) Report")

    # Garis pemisah
    c.line(50, height - 90, width - 50, height - 90)

    c.setFont("Helvetica", 12)
    y = height - 120

    for section, values in data.items():
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, section)
        y -= 20
        c.setFont("Helvetica", 12)
        for key, value in values.items():
            c.drawString(70, y, f"{key}: {value}")
            y -= 18
        y -= 10

    c.save()

# Tombol Generate PDF
if st.button("🧾 Generate PDF"):
    try:
        fmt = "%Y-%m-%d %H:%M"
        start = datetime.strptime(log_down, fmt)
        end = datetime.strptime(log_up, fmt)
        durasi = end - start
        jam, sisa = divmod(durasi.seconds, 3600)
        menit = sisa // 60
        mttr = f"{jam} jam {menit} menit"

        # Hitung SLA (30 hari = 30*24*60*60 detik)
        total_bulan = 30 * 24 * 60 * 60
        sla = round((1 - durasi.total_seconds() / total_bulan) * 100, 2)
    except Exception:
        mttr = "Format Salah"
        sla = "Tidak dapat dihitung"

    # Data untuk PDF
    data = {
        "Informasi Pelanggan": {
            "ID Pelanggan": id_pelanggan,
            "Nama Pelanggan": nama_pelanggan,
            "Nama Link": nama_link,
            "Alamat Link": alamat_link,
            "Jenis Layanan": jenis_layanan
        },
        "Informasi Gangguan": {
            "Nomor Tiket": nomor_tiket,
            "Log Down": log_down,
            "Log Up": log_up,
            "Durasi Pending": durasi_pending,
            "Penyebab Pending": penyebab_pending,
            "Penyebab": penyebab,
            "Tindakan": tindakan,
            "MTTR": mttr,
            "SLA": f"{sla}%"
        },
        "Disusun oleh": {
            "Staff": staff,
            "Manager": manager
        }
    }

    # Simpan logo sementara jika ada
    logo_path = None
    if logo_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(logo_file.name)[1]) as tmp_logo:
            tmp_logo.write(logo_file.read())
            logo_path = tmp_logo.name

    # Generate PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_pdf:
        generate_pdf(f_pdf.name, data, logo=logo_path)
        with open(f_pdf.name, "rb") as file:
            st.download_button("📄 Download PDF", file, file_name="RFO_Report.pdf")
