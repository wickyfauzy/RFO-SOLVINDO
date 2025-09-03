import streamlit as st
from datetime import datetime
from weasyprint import HTML
import tempfile
import os
import random
from jinja2 import Template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "template", "rfo_template.html")
LOGO_FOLDER = os.path.join(BASE_DIR, "uploaded_logo")
os.makedirs(LOGO_FOLDER, exist_ok=True)

st.set_page_config(page_title="RFO Generator", layout="centered")
st.title("📝 Reason For Outage (RFO) Generator")

# Upload logo perusahaan (opsional)
logo = st.file_uploader("Upload Logo Perusahaan (Opsional)", type=["png", "jpg", "jpeg"])

# Fungsi buat nomor tiket otomatis
def generate_ticket():
    now = datetime.now()
    kode_uniq = random.randint(100000, 99999999)  # 6-8 digit angka unik
    return f"TO/DIV/RE/{now.strftime('%Y-%m-%d')}/{kode_uniq}"

# Bagian 1: Data Pelanggan
st.subheader("Informasi Pelanggan")
id_pelanggan = st.text_input("ID Pelanggan")
nama_pelanggan = st.text_input("Nama Pelanggan")
nama_link = st.text_input("Nama Link")
alamat_link = st.text_area("Alamat Link")
jenis_layanan = st.text_input("Jenis Layanan")

st.markdown("---")

# Bagian 2: Tiket & Gangguan
st.subheader("Informasi Tiket & Gangguan")
nomor_tiket = st.text_input("Nomor Tiket", value=generate_ticket())
log_down = st.text_input("Log Down (format: YYYY-MM-DD HH:MM)")
log_up = st.text_input("Log Up (format: YYYY-MM-DD HH:MM)")
durasi_pending = st.text_input("Durasi Pending")
penyebab_pending = st.text_area("Penyebab Pending")
penyebab = st.text_area("Penyebab")
tindakan = st.text_area("Tindakan")

st.markdown("---")

# Footer info
st.subheader("Disusun oleh")
staff = st.text_input("Nama Staff Pembuat")
manager = st.text_input("Nama Manager")

if st.button("🧾 Generate PDF"):
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

    # Simpan logo permanen jika ada upload baru
    logo_path_saved = None
    if logo:
        ext = os.path.splitext(logo.name)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            st.error("Format logo harus PNG, JPG, atau JPEG")
            st.stop()
        logo_path_saved = os.path.join(LOGO_FOLDER, f"logo{ext}")
        with open(logo_path_saved, "wb") as f:
            f.write(logo.read())
    else:
        # Jika tidak upload, cek logo lama
        existing_logos = [f for f in os.listdir(LOGO_FOLDER) if f.startswith("logo.")]
        if existing_logos:
            logo_path_saved = os.path.join(LOGO_FOLDER, existing_logos[0])

    # Load template HTML
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_template = Template(f.read())

    logo_filename = os.path.basename(logo_path_saved) if logo_path_saved else None
    base_url_dir = LOGO_FOLDER if logo_path_saved else None

    html_rendered = html_template.render(
        id_pelanggan=id_pelanggan,
        nama_pelanggan=nama_pelanggan,
        nama_link=nama_link,
        alamat_link=alamat_link,
        jenis_layanan=jenis_layanan,
        nomor_tiket=nomor_tiket,
        log_down=log_down,
        log_up=log_up,
        durasi_pending=durasi_pending,
        penyebab_pending=penyebab_pending,
        penyebab=penyebab,
        tindakan=tindakan,
        staff=staff,
        manager=manager,
        mttr=mttr,
        sla=sla,
        logo_path=logo_filename
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_pdf:
        HTML(string=html_rendered, base_url=base_url_dir).write_pdf(f_pdf.name)
        with open(f_pdf.name, "rb") as file:
            st.download_button("📄 Download PDF", file, file_name="RFO_Report.pdf")
