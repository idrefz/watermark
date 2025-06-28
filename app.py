import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import piexif
from piexif._exceptions import InvalidImageDataError

# Fungsi untuk mendapatkan alamat dari koordinat
def get_address_from_coords(latitude, longitude):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'address' in data:
            address = data.get('address', {})
            elements = [
                address.get('road', ''),
                address.get('village', address.get('town', address.get('city', ''))),
                address.get('county', ''),
                address.get('state', ''),
                address.get('postcode', ''),
                address.get('country', '')
            ]
            return "\n".join([elem for elem in elements if elem])
        return f"{latitude}, {longitude}"
    except:
        return f"{latitude}, {longitude}"

# Fungsi untuk mendapatkan peta dari OpenStreetMap
def get_osm_map(latitude, longitude, zoom=15, size=(600, 300)):
    """Mendapatkan peta dari OpenStreetMap"""
    try:
        # Gunakan StaticMapAPI dari OSM
        url = f"https://static-maps.yandex.ru/1.x/?ll={longitude},{latitude}&z={zoom}&size={size[0]},{size[1]}&l=map&pt={longitude},{latitude},pm2rdl"
        response = requests.get(url)
        return Image.open(BytesIO(response.content))
    except Exception as e:
        st.warning(f"Gagal memuat peta: {str(e)}")
        return None

# Fungsi untuk membuat watermark modern
def create_modern_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        draw = ImageDraw.Draw(img)
        
        # Hitung ukuran watermark (30% dari tinggi gambar)
        wm_height = int(img.height * 0.3)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        
        # Buat background semi-transparan gelap
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,150))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Gunakan font (default atau custom)
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_medium = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
            font_bold = ImageFont.truetype("arialbd.ttf", 28)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        
        # Posisi teks
        margin = 20
        text_x = margin
        text_y = img.height - wm_height + margin
        
        # Tulis lokasi dengan format khusus
        loc_lines = location.split('\n')
        for i, line in enumerate(loc_lines):
            if i == 0:
                draw.text((text_x, text_y), line, font=font_bold, fill=(255,255,255))
                text_y += 40
            else:
                draw.text((text_x, text_y), line, font=font_small, fill=(255,255,255))
                text_y += 25
        
        # Garis pemisah
        draw.line((text_x, text_y, img.width - margin, text_y), fill=(255,255,255), width=1)
        text_y += 15
        
        # Info tanggal dan waktu
        draw.text((text_x, text_y), date_day_str, font=font_medium, fill=(255,255,255))
        time_width = draw.textlength(time_str, font=font_large)
        draw.text((img.width - margin - time_width, text_y), time_str, font=font_large, fill=(255,255,255))
        text_y += 40
        
        # Info suhu
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_medium)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_medium, fill=(255,255,255))
        
        # Tambahkan peta kecil jika ada
        if map_img:
            map_size = (200, 120)
            map_img = map_img.resize(map_size)
            img.paste(map_img, (img.width - map_size[0] - margin, img.height - wm_height + margin))
        
        return img
    except Exception as e:
        st.error(f"Error creating watermark: {str(e)}")
        return image

# Konfigurasi Streamlit
st.set_page_config(page_title="Modern Watermark Tool", layout="wide")
st.title("📷 Watermark Tool dengan OpenStreetMap")

# Sidebar untuk input
with st.sidebar:
    st.header("Pengaturan")
    
    # Input koordinat
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Latitude", "-6.1101")
    with col2:
        lon = st.text_input("Longitude", "106.1633")
    
    # Dapatkan alamat otomatis
    if st.button("Dapatkan Alamat Otomatis"):
        with st.spinner("Mengambil alamat..."):
            address = get_address_from_coords(lat, lon)
            st.session_state.address = address
    
    location = st.text_area("Lokasi", st.session_state.get('address', "Jl. Contoh No. 123\nKecamatan Contoh\nKota Contoh\nBanten\nIndonesia"), height=150)
    
    # Tanggal dan waktu
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Tanggal", datetime.date.today())
    with col2:
        time = st.time_input("Waktu", datetime.time(13, 5))
    
    # Format tanggal dan hari
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_str = days[date.weekday()]
    date_day_str = f"{date.strftime('%Y-%m-%d')}({day_str[:3]})"
    time_str = time.strftime("%I:%M%p").lower().replace("am", "AM").replace("pm", "PM")
    
    # Suhu
    col1, col2 = st.columns(2)
    with col1:
        temp_c = st.text_input("°C", "33")
    with col2:
        temp_f = st.text_input("°F", "91")
    
    # Toggle peta
    show_map = st.checkbox("Tampilkan Peta", value=True)

# Upload gambar
uploaded_file = st.file_uploader("Unggah Foto", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Baca gambar
    image = Image.open(uploaded_file)
    
    # Dapatkan peta
    map_img = None
    if show_map and lat and lon:
        with st.spinner("Memuat peta..."):
            map_img = get_osm_map(lat, lon, size=(400, 200))
    
    # Buat watermark
    watermarked_img = create_modern_watermark(
        image=image,
        time_str=time_str,
        date_day_str=date_day_str,
        location=location,
        temp_c=f"{temp_c}°C",
        temp_f=f"{temp_f}°F",
        map_img=map_img
    )
    
    # Tampilkan hasil
    col1, col2 = st.columns(2)
    with col1:
        st.image(image, caption="Original", use_column_width=True)
    with col2:
        st.image(watermarked_img, caption="Hasil Watermark", use_column_width=True)
        
        # Download
        buf = BytesIO()
        watermarked_img.save(buf, format="JPEG", quality=95)
        st.download_button(
            "Download Gambar",
            buf.getvalue(),
            "watermarked.jpg",
            "image/jpeg"
        )

# Petunjuk penggunaan
with st.expander("Cara Menggunakan"):
    st.markdown("""
    1. Unggah foto Anda
    2. Masukkan koordinat atau klik "Dapatkan Alamat Otomatis"
    3. Sesuaikan teks lokasi jika perlu
    4. Atur tanggal dan waktu
    5. Masukkan suhu (opsional)
    6. Download gambar hasil
    """)

# Catatan tentang OpenStreetMap
st.info("""
**Menggunakan OpenStreetMap:**
- Layanan gratis tanpa API key
- Untuk penggunaan intensif, harap gunakan server tile Anda sendiri
- Batas 1 request per detik
- Attribution diperlukan untuk penggunaan komersial
""")
