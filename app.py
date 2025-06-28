import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap

# Fungsi untuk membuat watermark dengan font besar
def create_large_font_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        draw = ImageDraw.Draw(img)
        
        # Hitung ukuran watermark (40% dari tinggi gambar untuk font besar)
        wm_height = int(img.height * 0.4)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        
        # Buat background semi-transparan gelap
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,180))  # Lebih gelap untuk kontras font
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Ukuran font yang lebih besar
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 42)  # Judul lebih besar
            font_large = ImageFont.truetype("arial.ttf", 36)    # Untuk waktu dan tanggal
            font_medium = ImageFont.truetype("arial.ttf", 28)   # Untuk alamat
            font_small = ImageFont.truetype("arial.ttf", 24)    # Untuk detail kecil
        except:
            # Fallback ke font default dengan ukuran besar
            font_title = ImageFont.load_default(size=42)
            font_large = ImageFont.load_default(size=36)
            font_medium = ImageFont.load_default(size=28)
            font_small = ImageFont.load_default(size=24)
        
        # Posisi teks
        margin = 25  # Margin lebih besar
        text_x = margin
        text_y = img.height - wm_height + margin
        
        # Tulis lokasi dengan format khusus
        loc_lines = location.split('\n')
        max_lines = 6  # Jumlah baris lebih sedikit karena font besar
        
        for i, line in enumerate(loc_lines[:max_lines]):
            if i == 0:
                draw.text((text_x, text_y), line, font=font_title, fill=(255,255,255))
                text_y += 50
            else:
                draw.text((text_x, text_y), line, font=font_medium, fill=(255,255,255))
                text_y += 35
        
        # Garis pemisah tebal
        draw.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255), width=2)
        text_y += 20
        
        # Info tanggal dan waktu
        date_time_text = f"{date_day_str}  {time_str}"
        draw.text((text_x, text_y), date_time_text, font=font_large, fill=(255,255,255))
        
        # Info suhu di kanan
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_large)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_large, fill=(255,255,255))
        text_y += 45
        
        # Tambahkan peta kecil jika ada (ukuran disesuaikan)
        if map_img:
            map_size = (min(250, img.width//2), min(150, wm_height//2))
            map_img = map_img.resize(map_size)
            
            # Background untuk peta
            map_bg = Image.new('RGB', (map_size[0]+10, map_size[1]+10), (50,50,50))
            img.paste(map_bg, (img.width - map_size[0] - margin - 5, img.height - wm_height + margin - 5))
            
            img.paste(map_img, (img.width - map_size[0] - margin, img.height - wm_height + margin))
        
        return img
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# Konfigurasi Streamlit
st.set_page_config(page_title="Watermark Font Besar", layout="wide")
st.title("📷 Watermark Tool dengan Font Besar")

# Sidebar untuk input
with st.sidebar:
    st.header("Pengaturan")
    
    # Input alamat
    location = st.text_area(
        "Alamat Lengkap", 
        "Jl. Contoh No. 123\nKel. Contoh\nKec. Contoh\nKota/Kab. Contoh\nProv. Contoh\nKode Pos: 12345\nIndonesia\nKoordinat: -6.1101, 106.1633", 
        height=150
    )
    
    # Tanggal dan waktu
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Tanggal", datetime.date.today())
    with col2:
        time = st.time_input("Waktu", datetime.time(13, 5))
    
    # Format tanggal dan hari
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
    
    # Toggle peta
    show_map = st.checkbox("Tampilkan Peta", value=False)

# Upload gambar
uploaded_file = st.file_uploader("Unggah Foto", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Baca gambar
    image = Image.open(uploaded_file)
    
    # Dapatkan peta (opsional)
    map_img = None
    if show_map:
        # Contoh: Gunakan koordinat dari alamat jika ada
        try:
            coord_part = [line for line in location.split('\n') if "Koordinat:" in line]
            if coord_part:
                coords = coord_part[0].split(":")[1].strip().split(",")
                lat, lon = coords[0].strip(), coords[1].strip()
                map_img = get_osm_map(lat, lon)
        except:
            st.warning("Tidak bisa memuat peta. Pastikan format koordinat benar.")
    
    # Buat watermark
    watermarked_img = create_large_font_watermark(
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
        st.image(watermarked_img, caption="Watermark Font Besar", use_column_width=True)
        
        # Download
        buf = BytesIO()
        watermarked_img.save(buf, format="JPEG", quality=95)
        st.download_button(
            "Download Gambar",
            buf.getvalue(),
            "watermarked_large_font.jpg",
            "image/jpeg"
        )

# Panduan
with st.expander("Panduan Penggunaan"):
    st.markdown("""
    **Fitur Font Besar:**
    - Ukuran font lebih besar untuk keterbacaan
    - Judul alamat: 42px
    - Alamat: 28px
    - Tanggal/waktu: 36px
    - Suhu: 36px
    
    **Tips:**
    - Untuk hasil terbaik, gunakan foto beresolusi tinggi
    - Alamat direkomendasikan maksimal 6-7 baris
    - Background gelap membantu kontras teks
    """)
