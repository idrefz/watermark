import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import re

# Fungsi untuk mendapatkan alamat lengkap dari koordinat
def get_complete_address(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'address' in data:
            addr = data['address']
            address_lines = []
            
            # Bangunan dan jalan
            if addr.get('road'):
                address_lines.append(f"Jl. {addr['road']}")
            if addr.get('house_number'):
                address_lines[-1] += f" No. {addr['house_number']}"
            
            # Wilayah administratif
            if addr.get('village'):
                address_lines.append(f"Kel. {addr['village']}")
            elif addr.get('suburb'):
                address_lines.append(f"Kel. {addr['suburb']}")
            
            if addr.get('subdistrict'):
                address_lines.append(f"Kec. {addr['subdistrict']}")
            elif addr.get('county'):
                address_lines.append(f"Kec. {addr['county']}")
            
            if addr.get('city'):
                address_lines.append(f"Kota {addr['city']}")
            elif addr.get('town'):
                address_lines.append(f"Kota {addr['town']}")
            
            if addr.get('state'):
                address_lines.append(f"Prov. {addr['state']}")
            
            if addr.get('postcode'):
                address_lines.append(f"Kode Pos: {addr['postcode']}")
            
            address_lines.append("Indonesia")
            address_lines.append(f"Koordinat: {lat:.6f}, {lon:.6f}")
            
            return "\n".join(address_lines)
        return f"Koordinat: {lat}, {lon}"
    except Exception as e:
        st.error(f"Gagal mendapatkan alamat: {str(e)}")
        return f"Koordinat: {lat}, {lon}"

# Fungsi untuk mendapatkan peta static
def get_static_map(lat, lon, size="600x300", zoom=15):
    return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom={zoom}&size={size}&maptype=roadmap&markers=color:red%7C{lat},{lon}&key=YOUR_API_KEY"

# Fungsi untuk membuat watermark dengan style modern
def create_modern_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        draw = ImageDraw.Draw(img)
        
        # Ukuran watermark (40% dari tinggi gambar)
        wm_height = int(img.height * 0.4)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        
        # Background semi-transparan gelap
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,180))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Font settings (ukuran besar)
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 42)
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_medium = ImageFont.truetype("arial.ttf", 28)
        except:
            font_title = ImageFont.load_default()
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Posisi teks
        margin = 25
        text_x = margin
        text_y = img.height - wm_height + margin
        
        # Tulis alamat
        loc_lines = location.split('\n')[:7]  # Maksimal 7 baris
        
        for i, line in enumerate(loc_lines):
            if i == 0:
                draw.text((text_x, text_y), line, font=font_title, fill=(255,255,255))
                text_y += 50
            else:
                draw.text((text_x, text_y), line, font=font_medium, fill=(255,255,255))
                text_y += 35
        
        # Garis pemisah
        draw.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255), width=2)
        text_y += 20
        
        # Tanggal dan waktu
        date_time_text = f"{date_day_str}  {time_str}"
        draw.text((text_x, text_y), date_time_text, font=font_large, fill=(255,255,255))
        
        # Suhu
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_large)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_large, fill=(255,255,255))
        
        # Tambahkan peta jika ada
        if map_img:
            map_size = (250, 150)
            map_img = map_img.resize(map_size)
            
            # Background untuk peta
            map_bg = Image.new('RGB', (map_size[0]+10, map_size[1]+10), (40,40,40))
            img.paste(map_bg, (img.width - map_size[0] - margin - 5, img.height - wm_height + margin - 5))
            
            img.paste(map_img, (img.width - map_size[0] - margin, img.height - wm_height + margin))
        
        return img
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# Konfigurasi Streamlit
st.set_page_config(page_title="Watermark Tool Pro", layout="wide")
st.title("📷 Watermark Tool dengan Alamat & Peta")

# Sidebar untuk input
with st.sidebar:
    st.header("Pengaturan")
    
    # Input koordinat
    st.subheader("Koordinat GPS")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Latitude", "-6.1101")
    with col2:
        lon = st.text_input("Longitude", "106.1633")
    
    # Tombol untuk mendapatkan alamat otomatis
    if st.button("Dapatkan Alamat dari Koordinat"):
        if lat and lon:
            try:
                with st.spinner("Mengambil data alamat..."):
                    address = get_complete_address(lat, lon)
                    st.session_state.address = address
                    st.success("Alamat berhasil didapatkan!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Masukkan koordinat terlebih dahulu")
    
    # Text area untuk alamat
    location = st.text_area(
        "Alamat Lengkap", 
        st.session_state.get('address', "Jl. Contoh No. 123\nKel. Contoh\nKec. Contoh\nKota/Kab. Contoh\nProv. Contoh\nKode Pos: 12345\nIndonesia\nKoordinat: -6.1101, 106.1633"), 
        height=200
    )
    
    # Tanggal dan waktu
    st.subheader("Tanggal & Waktu")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Tanggal", datetime.date.today())
    with col2:
        time = st.time_input("Waktu", datetime.time(13, 5))
    
    # Format tanggal
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_str = days[date.weekday()]
    date_day_str = f"{date.strftime('%Y-%m-%d')} ({day_str[:3]})"
    time_str = time.strftime("%I:%M%p").lower()
    
    # Suhu
    st.subheader("Informasi Cuaca")
    col1, col2 = st.columns(2)
    with col1:
        temp_c = st.text_input("°C", "33")
    with col2:
        temp_f = st.text_input("°F", "91")
    
    # Toggle peta
    show_map = st.checkbox("Tampilkan Peta di Watermark", value=True)

# Upload gambar
uploaded_file = st.file_uploader("Unggah Foto Anda", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Baca gambar
    image = Image.open(uploaded_file)
    
    # Dapatkan peta
    map_img = None
    if show_map and lat and lon:
        try:
            # Ekstrak koordinat dari alamat jika ada
            coord_match = re.search(r"Koordinat:\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)", location)
            if coord_match:
                lat, lon = coord_match.groups()
            
            with st.spinner("Memuat peta..."):
                map_url = get_static_map(lat, lon)
                response = requests.get(map_url)
                map_img = Image.open(BytesIO(response.content))
        except Exception as e:
            st.warning(f"Gagal memuat peta: {str(e)}")
    
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
        st.image(image, caption="Foto Asli", use_column_width=True)
    with col2:
        st.image(watermarked_img, caption="Hasil Watermark", use_column_width=True)
        
        # Download
        buf = BytesIO()
        watermarked_img.save(buf, format="JPEG", quality=95)
        st.download_button(
            "Download Gambar",
            buf.getvalue(),
            "watermarked_pro.jpg",
            "image/jpeg"
        )

# Panduan penggunaan
with st.expander("Panduan Lengkap"):
    st.markdown("""
    **Fitur Utama:**
    1. Konversi otomatis koordinat → alamat lengkap
    2. Tampilan peta dalam watermark
    3. Font besar untuk keterbacaan
    4. Format alamat standar Indonesia
    
    **Cara Menggunakan:**
    1. Masukkan koordinat (latitude & longitude)
    2. Klik "Dapatkan Alamat dari Koordinat"
    3. Periksa dan edit alamat jika perlu
    4. Unggah foto
    5. Download hasil
    
    **Catatan:**
    - Untuk Google Maps API, ganti YOUR_API_KEY
    - Format koordinat: -6.1101, 106.1633
    - Alamat otomatis bergantung data OpenStreetMap
    """)
