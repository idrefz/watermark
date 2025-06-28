import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import piexif
from piexif._exceptions import InvalidImageDataError

# Fungsi untuk mendapatkan alamat lengkap dari koordinat
def get_complete_address(latitude, longitude):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&addressdetails=1"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if 'address' in data:
            address = data.get('address', {})
            
            # Format alamat lengkap
            address_lines = []
            
            # Bagian jalan dan bangunan
            if address.get('road'):
                address_lines.append(f"Jl. {address['road']}")
            if address.get('building'):
                address_lines.append(f"Gedung {address['building']}")
            
            # Bagian wilayah administratif
            if address.get('village'):
                address_lines.append(f"Kel. {address['village']}")
            elif address.get('suburb'):
                address_lines.append(f"Kel. {address['suburb']}")
            
            if address.get('subdistrict') or address.get('county'):
                address_lines.append(f"Kec. {address.get('subdistrict', address.get('county', ''))}")
            
            if address.get('city'):
                address_lines.append(f"Kota {address['city']}")
            elif address.get('state_district'):
                address_lines.append(address['state_district'])
            
            if address.get('province'):
                address_lines.append(f"Prov. {address['province']}")
            
            if address.get('postcode'):
                address_lines.append(f"Kode Pos: {address['postcode']}")
            
            if address.get('country'):
                address_lines.append(address['country'])
            
            # Tambahkan koordinat sebagai referensi
            address_lines.append(f"Koordinat: {latitude:.6f}, {longitude:.6f}")
            
            return "\n".join(address_lines)
        return f"Koordinat: {latitude}, {longitude}"
    except Exception as e:
        st.warning(f"Gagal mendapatkan alamat: {str(e)}")
        return f"Koordinat: {latitude}, {longitude}"

# Fungsi untuk mendapatkan peta dari OpenStreetMap
def get_osm_map(latitude, longitude, zoom=16, size=(600, 300)):
    try:
        url = f"https://static-maps.yandex.ru/1.x/?ll={longitude},{latitude}&z={zoom}&size={size[0]},{size[1]}&l=map&pt={longitude},{latitude},pm2rdl"
        response = requests.get(url)
        return Image.open(BytesIO(response.content))
    except Exception as e:
        st.warning(f"Gagal memuat peta: {str(e)}")
        return None

# Fungsi untuk membuat watermark dengan alamat lengkap
def create_complete_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        draw = ImageDraw.Draw(img)
        
        # Hitung ukuran watermark (35% dari tinggi gambar untuk alamat panjang)
        wm_height = int(img.height * 0.35)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        
        # Buat background semi-transparan gelap
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,160))  # Sedikit lebih transparan
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Gunakan font (default atau custom)
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_medium = ImageFont.truetype("arial.ttf", 22)  # Lebih kecil untuk alamat panjang
            font_small = ImageFont.truetype("arial.ttf", 16)
            font_bold = ImageFont.truetype("arialbd.ttf", 26)  # Lebih kecil untuk judul
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
        max_lines = 8  # Batasi jumlah baris alamat
        
        for i, line in enumerate(loc_lines[:max_lines]):
            if i == 0:
                draw.text((text_x, text_y), line, font=font_bold, fill=(255,255,255))
                text_y += 35
            else:
                draw.text((text_x, text_y), line, font=font_small, fill=(255,255,255))
                text_y += 20
        
        # Garis pemisah tipis
        draw.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255,150), width=1)
        text_y += 15
        
        # Info tanggal dan waktu
        date_time_text = f"{date_day_str}  {time_str}"
        draw.text((text_x, text_y), date_time_text, font=font_medium, fill=(255,255,255))
        
        # Info suhu di kanan
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_medium)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_medium, fill=(255,255,255))
        text_y += 35
        
        # Tambahkan peta kecil jika ada (ukuran disesuaikan)
        if map_img:
            map_size = (min(220, img.width//3), min(130, wm_height//2))
            map_img = map_img.resize(map_size)
            
            # Hitung posisi peta agar tidak menimpa teks
            map_x = img.width - map_size[0] - margin
            map_y = img.height - wm_height + margin
            
            # Tambahkan background untuk peta
            map_bg = Image.new('RGB', (map_size[0]+10, map_size[1]+10), (40,40,40))
            img.paste(map_bg, (map_x-5, map_y-5))
            
            img.paste(map_img, (map_x, map_y))
        
        return img
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# Konfigurasi Streamlit
st.set_page_config(page_title="Watermark Alamat Lengkap", layout="wide")
st.title("📷 Watermark Tool dengan Alamat Lengkap")

# Sidebar untuk input
with st.sidebar:
    st.header("Pengaturan Alamat")
    
    # Input koordinat
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Latitude", "-6.1101")
    with col2:
        lon = st.text_input("Longitude", "106.1633")
    
    # Dapatkan alamat lengkap otomatis
    if st.button("Dapatkan Alamat Lengkap"):
        with st.spinner("Mengambil data alamat..."):
            if lat and lon:
                try:
                    address = get_complete_address(lat, lon)
                    st.session_state.address = address
                    st.success("Alamat berhasil didapatkan!")
                except:
                    st.error("Gagal mendapatkan alamat")
            else:
                st.warning("Masukkan koordinat terlebih dahulu")
    
    # Text area yang lebih besar untuk alamat lengkap
    location = st.text_area(
        "Alamat Lengkap", 
        st.session_state.get('address', "Jl. Contoh No. 123\nKel. Contoh\nKec. Contoh\nKota Contoh\nProv. Contoh\nKode Pos: 12345\nIndonesia"), 
        height=200
    )
    
    st.header("Informasi Tambahan")
    
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
    time_str = time.strftime("%I:%M%p").lower().replace("am", "AM").replace("pm", "PM")
    
    # Suhu
    col1, col2 = st.columns(2)
    with col1:
        temp_c = st.text_input("Suhu °C", "33")
    with col2:
        temp_f = st.text_input("Suhu °F", "91")
    
    # Toggle peta
    show_map = st.checkbox("Tampilkan Peta", value=True)

# Upload gambar
uploaded_file = st.file_uploader("Unggah Foto Anda", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Baca gambar
    image = Image.open(uploaded_file)
    
    # Dapatkan peta
    map_img = None
    if show_map and lat and lon:
        with st.spinner("Memuat peta..."):
            map_img = get_osm_map(lat, lon, size=(500, 250))
    
    # Buat watermark
    watermarked_img = create_complete_watermark(
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
            "watermarked.jpg",
            "image/jpeg"
        )

# Petunjuk penggunaan
with st.expander("Panduan Lengkap"):
    st.markdown("""
    **Cara Menggunakan:**
    1. Unggah foto Anda
    2. Masukkan koordinat (latitude & longitude)
    3. Klik "Dapatkan Alamat Lengkap" untuk mengisi otomatis
    4. Sesuaikan alamat jika diperlukan
    5. Atur tanggal, waktu, dan suhu
    6. Download gambar hasil
    
    **Fitur Alamat Lengkap:**
    - Menampilkan jalan, gedung/bangunan
    - Wilayah administratif (kelurahan, kecamatan)
    - Kota/kabupaten dan provinsi
    - Kode pos
    - Koordinat GPS
    
    **Catatan:**
    - Untuk hasil terbaik, gunakan foto landscape
    - Alamat otomatis bergantung pada data OpenStreetMap
    - Ukuran watermark akan menyesuaikan panjang alamat
    """)

# Catatan tentang OpenStreetMap
st.info("""
**Informasi OpenStreetMap:**
- Layanan gratis dan terbuka
- Data alamat mungkin bervariasi tergantung wilayah
- Untuk penggunaan intensif (>1 request/detik), harap gunakan server sendiri
- Attribution: © OpenStreetMap contributors
""")
