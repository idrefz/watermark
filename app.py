import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import piexif
from piexif._exceptions import InvalidImageDataError

# Fungsi untuk mendapatkan alamat lengkap dengan penanganan error
def get_complete_address(latitude, longitude):
    try:
        # Pastikan latitude dan longitude adalah angka
        lat_num = float(latitude)
        lon_num = float(longitude)
        
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_num}&lon={lon_num}&addressdetails=1"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Akan raise error untuk status code 4xx/5xx
        data = response.json()
        
        if 'address' in data:
            address = data.get('address', {})
            address_lines = []
            
            # Bangunan dan jalan
            if address.get('building'):
                address_lines.append(f"Gedung {address['building']}")
            if address.get('road'):
                address_lines.append(f"Jl. {address['road']}")
            
            # Area administratif
            if address.get('village'):
                address_lines.append(f"Kel. {address['village']}")
            elif address.get('suburb'):
                address_lines.append(f"Kel. {address['suburb']}")
            
            if address.get('subdistrict'):
                address_lines.append(f"Kec. {address['subdistrict']}")
            elif address.get('county'):
                address_lines.append(f"Kec. {address['county']}")
            
            if address.get('city'):
                address_lines.append(f"Kota {address['city']}")
            elif address.get('town'):
                address_lines.append(f"Kota {address['town']}")
            
            if address.get('state'):
                address_lines.append(f"Prov. {address['state']}")
            
            if address.get('postcode'):
                address_lines.append(f"Kode Pos: {address['postcode']}")
            
            if address.get('country'):
                address_lines.append(address['country'])
            
            # Format koordinat dengan pengecekan numerik
            try:
                coord_text = f"Koordinat: {lat_num:.6f}, {lon_num:.6f}"
                address_lines.append(coord_text)
            except:
                address_lines.append(f"Koordinat: {latitude}, {longitude}")
            
            return "\n".join([line for line in address_lines if line.strip()])
        
        return f"Koordinat: {latitude}, {longitude}"
    
    except ValueError as e:
        return f"Error: Koordinat tidak valid - {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"Error: Gagal mendapatkan alamat - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi untuk mendapatkan peta dengan penanganan error
def get_osm_map(latitude, longitude, zoom=16, size=(600, 300)):
    try:
        # Pastikan koordinat numerik
        lat_num = float(latitude)
        lon_num = float(longitude)
        
        url = f"https://static-maps.yandex.ru/1.x/?ll={lon_num},{lat_num}&z={zoom}&size={size[0]},{size[1]}&l=map&pt={lon_num},{lat_num},pm2rdl"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        st.warning(f"Gagal memuat peta: {str(e)}")
        return None

# Fungsi utama untuk membuat watermark
def create_complete_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        draw = ImageDraw.Draw(img)
        wm_height = int(img.height * 0.25)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        
        # Background watermark
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,160))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Font settings
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_medium = ImageFont.truetype("arial.ttf", 22)
            font_small = ImageFont.truetype("arial.ttf", 16)
            font_bold = ImageFont.truetype("arialbd.ttf", 26)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        
        # Position elements
        margin = 20
        text_x = margin
        text_y = img.height - wm_height + margin
        
        # Location text
        loc_lines = location.split('\n')[:8]  # Limit to 8 lines
        
        for i, line in enumerate(loc_lines):
            if i == 0 and line.strip():
                draw.text((text_x, text_y), line, font=font_bold, fill=(255,255,255))
                text_y += 35
            elif line.strip():
                draw.text((text_x, text_y), line, font=font_small, fill=(255,255,255))
                text_y += 20
        
        # Separator line
        if loc_lines:
            draw.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255,150), width=1)
            text_y += 15
        
        # Date and time
        date_time_text = f"{date_day_str}  {time_str}"
        draw.text((text_x, text_y), date_time_text, font=font_medium, fill=(255,255,255))
        
        # Temperature
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_medium)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_medium, fill=(255,255,255))
        
        # Map image
        if map_img:
            map_size = (min(220, img.width//3), min(130, wm_height//2))
            map_img = map_img.resize(map_size)
            map_x = img.width - map_size[0] - margin
            map_y = img.height - wm_height + margin
            
            map_bg = Image.new('RGB', (map_size[0]+10, map_size[1]+10), (40,40,40))
            img.paste(map_bg, (map_x-5, map_y-5))
            img.paste(map_img, (map_x, map_y))
        
        return img
    
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# Konfigurasi Streamlit
st.set_page_config(page_title="Watermark Tool", layout="wide")
st.title("📷 Watermark Tool dengan Alamat Lengkap")

with st.sidebar:
    st.header("Pengaturan")
    
    # Input koordinat dengan validasi
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Latitude", "-6.1101", help="Contoh: -6.1101")
    with col2:
        lon = st.text_input("Longitude", "106.1633", help="Contoh: 106.1633")
    
    # Tombol dengan penanganan error
    if st.button("Dapatkan Alamat Lengkap"):
        if not lat or not lon:
            st.warning("Harap masukkan latitude dan longitude")
        else:
            try:
                with st.spinner("Mengambil data alamat..."):
                    address = get_complete_address(lat, lon)
                    if address.startswith("Error:"):
                        st.error(address)
                    else:
                        st.session_state.address = address
                        st.success("Alamat berhasil didapatkan!")
            except Exception as e:
                st.error(f"Terjadi error: {str(e)}")
    
    # Text area untuk alamat
    location = st.text_area(
        "Alamat Lengkap", 
        st.session_state.get('address', "Jl. Contoh No. 123\nKel. Contoh\nKec. Contoh\nKota/Kab. Contoh\nProv. Contoh\nKode Pos: 12345\nIndonesia\nKoordinat: -6.1101, 106.1633"), 
        height=200
    )
    
    st.header("Informasi Tambahan")
    
    # Tanggal dan waktu
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Tanggal", datetime.date.today())
    with col2:
        time = st.time_input("Waktu", datetime.time(13, 5))
    
    # Format tanggal
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_str = days[date.weekday()]
    date_day_str = f"{date.strftime('%Y-%m-%d')} ({day_str[:3]})"
    time_str = time.strftime("%I:%M%p").replace("AM", "am").replace("PM", "pm")
    
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
    try:
        image = Image.open(uploaded_file)
        
        # Dapatkan peta
        map_img = None
        if show_map and lat and lon:
            with st.spinner("Memuat peta..."):
                map_img = get_osm_map(lat, lon)
        
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
    
    except Exception as e:
        st.error(f"Error memproses gambar: {str(e)}")

# Panduan
with st.expander("Panduan Penggunaan"):
    st.markdown("""
    **Cara Menggunakan:**
    1. Masukkan koordinat (contoh: -6.1101, 106.1633)
    2. Klik "Dapatkan Alamat Lengkap"
    3. Periksa dan edit alamat jika perlu
    4. Unggah foto
    5. Download hasil
    
    **Format Koordinat:**
    - Latitude: -90.000000 sampai 90.000000
    - Longitude: -180.000000 sampai 180.000000
    
    **Tips:**
    - Untuk alamat lebih akurat, gunakan koordinat lengkap (6 digit desimal)
    - Edit manual alamat jika ada yang kurang sesuai
    """)
