import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
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
nomor_tiket = st.text_input("Nomor Tiket (otomatis jika kosong)", placeholder="Biarkan kosong untuk generate otomatis")
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

# Fungsi buat PDF mirip template final
def generate_pdf(output_path, data, logo=None):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    style_center = ParagraphStyle(name="Center", alignment=TA_CENTER, fontSize=18, spaceAfter=10, leading=22)
    style_footer = ParagraphStyle(name="Footer", fontSize=10, alignment=TA_CENTER, italic=True)

    # Header dengan logo proporsional
    if logo:
        img = Image(logo)
        img.drawWidth = 180  # Set lebar tetap 180 px
        img.drawHeight = img.imageHeight * (img.drawWidth / img.imageWidth)  # Tinggi proporsional
        img.hAlign = "LEFT"
        elements.append(img)

    elements.append(Paragraph("<b>Reason For Outage (RFO)</b>", style_center))

    # Garis hitam tebal di bawah header
    elements.append(Spacer(1, 4))
    line = Table([[""]], colWidths=[500])
    line.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 2, colors.black)]))
    elements.append(line)
    elements.append(Spacer(1, 10))

    # Tabel data
    table_data = []
    for section, values in data.items():
        table_data.append([Paragraph(f"<b>{section}</b>", styles["Normal"]), ""])
        for key, value in values.items():
            table_data.append([Paragraph(f"<b>{key}</b>", styles["Normal"]), f": {value}"])
        table_data.append(["", ""])

    table = Table(table_data, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    # Garis hitam di atas footer
    line_footer = Table([[""]], colWidths=[500])
    line_footer.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, -1), 2, colors.black)]))
    elements.append(line_footer)
    elements.append(Spacer(1, 20))

    # Footer tanda tangan
    footer_data = [
        ["Dibuat", "Diketahui"],
        ["", ""],
        ["", ""],
        [staff, manager],
        [Paragraph("Network Operating Center", style_footer),
         Paragraph("Manager Networking Operating Center", style_footer)]
    ]

    footer_table = Table(footer_data, colWidths=[250, 250])
    footer_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
    ]))

    elements.append(footer_table)
    doc.build(elements)

# Tombol Generate PDF
if st.button("🧾 Generate PDF"):
    ticket_number = nomor_tiket.strip() if nomor_tiket.strip() else generate_ticket()

    try:
        fmt = "%Y-%m-%d %H:%M"
        start = datetime.strptime(log_down, fmt)
        end = datetime.strptime(log_up, fmt)
        durasi = end - start
        jam, sisa = divmod(durasi.seconds, 3600)
        menit = sisa // 60
        mttr = f"{jam} jam {menit} menit"

        total_bulan = 30 * 24 * 60 * 60
        sla = round((1 - durasi.total_seconds() / total_bulan) * 100, 2)
    except Exception:
        mttr = "Format Salah"
        sla = "Tidak dapat dihitung"

    data = {
        "Informasi Pelanggan": {
            "ID Pelanggan": id_pelanggan,
            "Nama Pelanggan": nama_pelanggan,
            "Nama Link": nama_link,
            "Alamat Link": alamat_link,
            "Jenis Layanan": jenis_layanan
        },
        "Informasi Gangguan": {
            "Nomor Tiket": ticket_number,
            "Log Down": log_down,
            "Log Up": log_up,
            "Durasi Pending": durasi_pending,
            "Penyebab Pending": penyebab_pending,
            "Penyebab": penyebab,
            "Tindakan": tindakan,
            "MTTR": mttr,
            "SLA": f"{sla}%"
        }
    }

    # Logo: pakai upload atau default
    logo_path = None
    if logo_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(logo_file.name)[1]) as tmp_logo:
            tmp_logo.write(logo_file.read())
            logo_path = tmp_logo.name
    else:
        default_logo = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(default_logo):
            logo_path = default_logo

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_pdf:
        generate_pdf(f_pdf.name, data, logo=logo_path)
        with open(f_pdf.name, "rb") as file:
            st.download_button("📄 Download PDF", file, file_name="RFO_Report.pdf")
