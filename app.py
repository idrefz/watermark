import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import math

def calculate_dynamic_font_size(img_height):
    """Menghitung ukuran font berdasarkan tinggi gambar"""
    base_size = img_height / 20  # Ukuran dasar relatif terhadap tinggi gambar
    return {
        'title': int(base_size * 1.8),  # Judul alamat
        'address': int(base_size * 1.2),  # Baris alamat
        'datetime': int(base_size * 1.5),  # Tanggal dan waktu
        'temp': int(base_size * 1.3)  # Suhu
    }

def get_osm_map(latitude, longitude, size=(400, 200)):
    """Mendapatkan peta dari OpenStreetMap"""
    try:
        url = f"https://static-maps.yandex.ru/1.x/?ll={longitude},{latitude}&z=15&size={size[0]},{size[1]}&l=map&pt={longitude},{latitude},pm2rdl"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        st.warning(f"Gagal memuat peta: {str(e)}")
        return None

def create_dynamic_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Hitung ukuran font dinamis
        font_sizes = calculate_dynamic_font_size(img.height)
        
        # Buat objek font
        try:
            font_title = ImageFont.truetype("arialbd.ttf", font_sizes['title'])
            font_address = ImageFont.truetype("arial.ttf", font_sizes['address'])
            font_datetime = ImageFont.truetype("arial.ttf", font_sizes['datetime'])
            font_temp = ImageFont.truetype("arial.ttf", font_sizes['temp'])
        except:
            # Fallback ke font default
            font_title = ImageFont.load_default()
            font_address = ImageFont.load_default()
            font_datetime = ImageFont.load_default()
            font_temp = ImageFont.load_default()
        
        draw = ImageDraw.Draw(img)
        
        # Hitung tinggi watermark secara dinamis
        wm_height = int(img.height * 0.35)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        
        # Buat background semi-transparan
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,160))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Posisi teks
        margin = int(img.width * 0.03)  # Margin relatif terhadap lebar gambar
        text_x = margin
        text_y = img.height - wm_height + margin
        
        # Tulis alamat
        loc_lines = location.split('\n')[:6]  # Maksimal 6 baris
        
        for i, line in enumerate(loc_lines):
            if i == 0:
                draw.text((text_x, text_y), line, font=font_title, fill=(255,255,255))
                text_y += int(font_sizes['title'] * 1.2)
            else:
                draw.text((text_x, text_y), line, font=font_address, fill=(255,255,255))
                text_y += int(font_sizes['address'] * 1.3)
        
        # Garis pemisah
        draw.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255), width=2)
        text_y += int(font_sizes['address'] * 0.8)
        
        # Tanggal dan waktu
        datetime_text = f"{date_day_str}  {time_str}"
        draw.text((text_x, text_y), datetime_text, font=font_datetime, fill=(255,255,255))
        
        # Suhu (kanan)
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_temp)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_temp, fill=(255,255,255))
        
        # Tambahkan peta jika ada
        if map_img:
            map_width = int(img.width * 0.3)  # Lebar peta 30% dari lebar gambar
            map_height = int(wm_height * 0.5)  # Tinggi peta 50% dari tinggi watermark
            map_img = map_img.resize((map_width, map_height))
            
            # Posisi peta (kanan atas area watermark)
            map_x = img.width - map_width - margin
            map_y = img.height - wm_height + margin
            
            # Background untuk peta
            map_bg = Image.new('RGB', (map_width + 10, map_height + 10), (40,40,40))
            img.paste(map_bg, (map_x - 5, map_y - 5))
            img.paste(map_img, (map_x, map_y))
        
        return img
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# UI Streamlit
st.set_page_config(page_title="Watermark Dinamis", layout="wide")
st.title("📷 Watermark Tool dengan Font Dinamis dan Peta")

with st.sidebar:
    st.header("Pengaturan")
    
    # Input alamat
    location = st.text_area(
        "Alamat Lengkap", 
        "Jl. Contoh No. 123\nKel. Contoh\nKec. Contoh\nKota/Kab. Contoh\nProv. Contoh\nKode Pos: 12345", 
        height=150
    )
    
    # Input koordinat untuk peta
    st.subheader("Koordinat Peta")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Latitude", "-6.1101")
    with col2:
        lon = st.text_input("Longitude", "106.1633")
    
    # Tanggal dan waktu
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Tanggal", datetime.date.today())
    with col2:
        time = st.time_input("Waktu", datetime.time(13, 5))
    
    # Format teks
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_str = days[date.weekday()]
    date_day_str = f"{date.strftime('%Y-%m-%d')} ({day_str[:3]})"
    time_str = time.strftime("%I:%M%p").lower()
    
    # Suhu
    col1, col2 = st.columns(2)
    with col1:
        temp_c = st.text_input("°C", "33")
    with col2:
        temp_f = st.text_input("°F", "91")
    
    show_map = st.checkbox("Tampilkan Peta", value=True)

# Upload gambar
uploaded_file = st.file_uploader("Unggah Foto", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # Dapatkan peta
    map_img = None
    if show_map and lat and lon:
        try:
            with st.spinner("Memuat peta..."):
                map_img = get_osm_map(lat, lon)
        except:
            st.warning("Gagal memuat peta. Periksa koordinat.")
    
    # Buat watermark
    watermarked_img = create_dynamic_watermark(
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
            "watermarked_dynamic.jpg",
            "image/jpeg"
        )

# Panduan
with st.expander("Panduan Penggunaan"):
    st.markdown("""
    **Fitur Dinamis:**
    - Ukuran font menyesuaikan dengan ukuran foto
    - Peta muncul di sudut kanan atas watermark
    - Layout otomatis menyesuaikan
    
    **Tips:**
    1. Untuk foto portrait, peta mungkin lebih kecil
    2. Koordinat harus valid untuk menampilkan peta
    3. Ukuran font minimal 16px untuk keterbacaan
    """)
