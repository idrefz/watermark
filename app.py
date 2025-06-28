import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import socket
from requests.exceptions import RequestException, Timeout, ConnectionError
import re

# Fungsi untuk mendapatkan alamat dari koordinat dengan penanganan error lengkap
def get_complete_address(latitude, longitude):
    try:
        # Validasi dan format koordinat
        lat_num = float(latitude)
        lon_num = float(longitude)
        coord_text = f"Koordinat: {lat_num:.6f}, {lon_num:.6f}"
        
        # Cek koneksi internet
        try:
            socket.create_connection(("nominatim.openstreetmap.org", 80), timeout=5)
            
            # Request ke Nominatim API
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_num}&lon={lon_num}&addressdetails=1"
            headers = {'User-Agent': 'WatermarkApp/1.0'}
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'address' in data:
                    addr = data['address']
                    lines = []
                    
                    # Bangunan dan jalan
                    if addr.get('road'):
                        road = f"Jl. {addr['road']}"
                        if addr.get('house_number'):
                            road += f" No. {addr['house_number']}"
                        lines.append(road)
                    
                    # Wilayah administratif
                    if addr.get('village'):
                        lines.append(f"Kel. {addr['village']}")
                    elif addr.get('suburb'):
                        lines.append(f"Kel. {addr['suburb']}")
                    
                    if addr.get('subdistrict'):
                        lines.append(f"Kec. {addr['subdistrict']}")
                    elif addr.get('county'):
                        lines.append(f"Kec. {addr['county']}")
                    
                    if addr.get('city'):
                        lines.append(f"Kota {addr['city']}")
                    elif addr.get('town'):
                        lines.append(f"Kota {addr['town']}")
                    
                    if addr.get('state'):
                        lines.append(f"Prov. {addr['state']}")
                    
                    if addr.get('postcode'):
                        lines.append(f"Kode Pos: {addr['postcode']}")
                    
                    lines.append("Indonesia")
                    lines.append(coord_text)
                    return "\n".join(lines)
                
            except Timeout:
                return f"{coord_text}\n(Timeout saat mengambil alamat)"
            except ConnectionError:
                return f"{coord_text}\n(Tidak ada koneksi internet)"
            except RequestException as e:
                return f"{coord_text}\n(Error API: {str(e)})"
            
        except (socket.gaierror, OSError):
            return f"{coord_text}\n(Tidak ada koneksi internet)"
            
    except ValueError:
        return "Error: Format koordinat tidak valid (gunakan titik sebagai desimal)"
    except Exception as e:
        return f"Error tak terduga: {str(e)}"
    
    return coord_text

# Fungsi untuk mendapatkan peta static dengan penanganan error
def get_static_map(latitude, longitude, zoom=16, size=(600, 300)):
    try:
        lat_num = float(latitude)
        lon_num = float(longitude)
        
        # Gunakan Yandex Static Maps sebagai alternatif gratis
        url = f"https://static-maps.yandex.ru/1.x/?ll={lon_num},{lat_num}&z={zoom}&size={size[0]},{size[1]}&l=map&pt={lon_num},{lat_num},pm2rdl"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Timeout:
            st.warning("Timeout saat memuat peta")
            return None
        except ConnectionError:
            st.warning("Tidak dapat terhubung ke server peta")
            return None
        except RequestException as e:
            st.warning(f"Gagal memuat peta: {str(e)}")
            return None
            
    except ValueError:
        st.warning("Koordinat tidak valid untuk peta")
        return None
    except Exception as e:
        st.warning(f"Error saat memproses peta: {str(e)}")
        return None

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
            font_title = ImageFont.truetype("arialbd.ttf", 42)  # Judul
            font_large = ImageFont.truetype("arial.ttf", 36)    # Tanggal/waktu
            font_medium = ImageFont.truetype("arial.ttf", 28)   # Alamat
        except:
            # Fallback ke font default
            font_title = ImageFont.load_default()
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Posisi teks
        margin = 25
        text_x = margin
        text_y = img.height - wm_height + margin
        
        # Tulis alamat (maksimal 7 baris)
        loc_lines = location.split('\n')[:7]
        
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
            try:
                map_size = (250, 150)
                map_img = map_img.resize(map_size)
                
                # Background untuk peta
                map_bg = Image.new('RGB', (map_size[0]+10, map_size[1]+10), (40,40,40))
                img.paste(map_bg, (img.width - map_size[0] - margin - 5, img.height - wm_height + margin - 5))
                img.paste(map_img, (img.width - map_size[0] - margin, img.height - wm_height + margin))
            except:
                pass
        
        return img
    
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# ========== Streamlit UI ==========
st.set_page_config(page_title="Watermark Tool Pro", layout="wide")
st.title("📷 Watermark Tool dengan Alamat & Peta")

with st.sidebar:
    st.header("Pengaturan")
    
    # Input koordinat
    st.subheader("Koordinat GPS")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Latitude", "-6.1101", help="Contoh: -6.1101")
    with col2:
        lon = st.text_input("Longitude", "106.1633", help="Contoh: 106.1633")
    
    # Tombol untuk mendapatkan alamat
    if st.button("📍 Dapatkan Alamat dari Koordinat"):
        if lat and lon:
            with st.spinner("Mengambil data alamat..."):
                address = get_complete_address(lat, lon)
                if address.startswith("Error:"):
                    st.error(address)
                else:
                    st.session_state.address = address
                    st.success("Alamat berhasil didapatkan!")
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
    show_map = st.checkbox("🗺️ Tampilkan Peta di Watermark", value=True)

# Upload gambar
uploaded_file = st.file_uploader("📤 Unggah Foto Anda", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        
        # Dapatkan peta
        map_img = None
        if show_map and lat and lon:
            # Coba ekstrak koordinat dari alamat jika ada
            coord_match = re.search(r"Koordinat:\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)", location)
            if coord_match:
                lat, lon = coord_match.groups()
            
            with st.spinner("Memuat peta..."):
                map_img = get_static_map(lat, lon)
                if not map_img:
                    st.warning("Tidak dapat menampilkan peta")
        
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
                "⬇️ Download Gambar",
                buf.getvalue(),
                "watermarked_pro.jpg",
                "image/jpeg"
            )
    
    except Exception as e:
        st.error(f"Error memproses gambar: {str(e)}")

# Panduan penggunaan
with st.expander("ℹ️ Panduan Lengkap"):
    st.markdown("""
    **Fitur Utama:**
    - Konversi otomatis koordinat → alamat lengkap
    - Tampilan peta dalam watermark
    - Font besar untuk keterbacaan
    - Format alamat standar Indonesia
    
    **Cara Menggunakan:**
    1. Masukkan koordinat (contoh: -6.1101, 106.1633)
    2. Klik "Dapatkan Alamat dari Koordinat"
    3. Periksa dan edit alamat jika perlu
    4. Unggah foto
    5. Download hasil
    
    **Pemecahan Masalah:**
    - Jika gagal mendapatkan alamat:
      - Cek koneksi internet
      - Pastikan koordinat valid
      - Coba lagi beberapa saat kemudian
    - Jika peta tidak muncul:
      - Cek koneksi internet
      - Koordinat mungkin diluar cakupan peta
    """)
