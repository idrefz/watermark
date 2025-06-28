import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import piexif
from piexif._exceptions import InvalidImageDataError
import os

# Fungsi untuk membuat watermark
def create_watermark(image, time_str, date_str, day_str, location, name, map_url=None):
    img = image.copy()
    
    # Konversi ke RGB jika mode gambar lain (e.g., RGBA, P)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Hitung posisi watermark (di bagian bawah)
    watermark_height = 250 if map_url else 150
    watermark_position = (0, img.height - watermark_height, img.width, img.height)
    
    # Buat background semi-transparan
    overlay = Image.new('RGBA', img.size, (255,255,255,0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.rectangle(watermark_position, fill=(255,255,255,180))
    
    # Gabungkan overlay dengan gambar utama
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Gunakan font default atau custom font jika ada
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Tulis teks watermark
    text_x = 20
    text_y = img.height - watermark_height + 20
    
    # Waktu besar
    draw.text((text_x, text_y), time_str, font=font_large, fill=(0, 0, 0))
    text_y += 50
    
    # Tanggal dan hari
    date_day_text = f"{date_str}\n{day_str}"
    draw.text((text_x, text_y), date_day_text, font=font_medium, fill=(0, 0, 0))
    text_y += 60
    
    # Lokasi (dengan wrap text jika panjang)
    lines = textwrap.wrap(location, width=40)
    for line in lines:
        draw.text((text_x, text_y), line, font=font_small, fill=(0, 0, 0))
        text_y += 25
    
    # Nama pengguna
    draw.text((text_x, text_y), name, font=font_medium, fill=(0, 0, 0))
    
    # Tambahkan peta jika ada
    if map_url:
        try:
            response = requests.get(map_url)
            map_img = Image.open(BytesIO(response.content))
            map_img = map_img.resize((250, 150))
            img.paste(map_img, (img.width - 270, img.height - 170))
        except:
            st.warning("Gagal memuat peta")
    
    return img

# Fungsi untuk mendapatkan URL peta dari koordinat
def get_map_url(latitude, longitude, api_key=None):
    if api_key:
        # Jika menggunakan Google Maps API
        return f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom=15&size=400x200&maptype=roadmap&markers=color:red%7C{latitude},{longitude}&key={api_key}"
    else:
        # OpenStreetMap tanpa API key
        return f"https://www.openstreetmap.org/export/embed.html?bbox={float(longitude)-0.01},{float(latitude)-0.01},{float(longitude)+0.01},{float(latitude)+0.01}&layer=mapnik&marker={latitude},{longitude}"

# Fungsi untuk mengupdate metadata EXIF
def update_exif_metadata(image, datetime_original, latitude, longitude):
    """Update EXIF metadata with new datetime and GPS coordinates"""
    try:
        # Cek apakah gambar sudah memiliki EXIF data
        exif_dict = piexif.load(image.info.get('exif', b''))
        
        # Format tanggal/waktu untuk EXIF (YYYY:MM:DD HH:MM:SS)
        exif_datetime = datetime_original.strftime("%Y:%m:%d %H:%M:%S")
        
        # Update DateTimeOriginal
        exif_dict['0th'][piexif.ImageIFD.DateTime] = exif_datetime
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_datetime
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = exif_datetime
        
        # Tambahkan GPS info jika koordinat valid
        if latitude and longitude:
            lat_deg = abs(float(latitude))
            lon_deg = abs(float(longitude))
            
            lat_ref = 'N' if float(latitude) >= 0 else 'S'
            lon_ref = 'E' if float(longitude) >= 0 else 'W'
            
            # Konversi ke format EXIF (degrees, minutes, seconds)
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = [
                (int(lat_deg), 1),
                (int((lat_deg % 1) * 60), 1),
                (int((((lat_deg % 1) * 60) % 1) * 60 * 100), 100)
            ]
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = [
                (int(lon_deg), 1),
                (int((lon_deg % 1) * 60), 1),
                (int((((lon_deg % 1) * 60) % 1) * 60 * 100), 100)
            ]
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = lon_ref
            exif_dict['GPS'][piexif.GPSIFD.GPSVersionID] = (2, 2, 0, 0)
        
        # Konversi kembali ke bytes EXIF
        exif_bytes = piexif.dump(exif_dict)
        return exif_bytes
    
    except (InvalidImageDataError, ValueError) as e:
        st.warning(f"Tidak bisa memodifikasi metadata EXIF: {str(e)}")
        return None

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Watermark Photo Tool", layout="wide")
st.title("🖼️ Watermark Photo Tool with Geotagging")

# Sidebar untuk input
with st.sidebar:
    st.header("Pengaturan Watermark")
    
    # Input waktu
    time_input = st.time_input("Waktu", value=datetime.time(7, 48))
    time_str = time_input.strftime("%H:%M")
    
    # Input tanggal
    date_input = st.date_input("Tanggal", value=datetime.date.today())
    date_str = date_input.strftime("%d-%m-%Y")
    
    # Gabungkan tanggal dan waktu untuk EXIF
    datetime_combined = datetime.datetime.combine(date_input, time_input)
    
    # Hari dalam bahasa Indonesia
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_str = days[date_input.weekday()]
    
    # Input lokasi
    location = st.text_input("Lokasi", "Jalan Raya Serang - Jakarta No.KM95.Ciruas,Banten")
    
    # Input koordinat untuk peta dan geotagging
    st.subheader("Koordinat untuk Geotagging")
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.text_input("Latitude", "-6.2088")
    with col2:
        longitude = st.text_input("Longitude", "106.8456")
    
    # Nama pengguna
    name = st.text_input("Masukkan nama Anda", "Nama Pengguna")
    
    # Toggle peta
    show_map = st.checkbox("Tampilkan peta", value=True)
    
    # Toggle geotagging
    enable_geotag = st.checkbox("Aktifkan Geotagging", value=True)

# Upload gambar
uploaded_file = st.file_uploader("Upload foto Anda", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Baca gambar
    image = Image.open(uploaded_file)
    
    # Tampilkan gambar asli
    st.subheader("Preview")
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Gambar Asli", use_column_width=True)
    
    # Generate map URL jika koordinat valid
    map_url = None
    if show_map and latitude and longitude:
        try:
            # Ganti dengan API key Anda jika menggunakan Google Maps
            map_url = get_map_url(latitude, longitude, api_key=None)
        except:
            st.error("Koordinat tidak valid")
    
    # Buat watermark
    watermarked_img = create_watermark(
        image, 
        time_str, 
        date_str, 
        day_str, 
        location, 
        name,
        map_url
    )
    
    # Update metadata EXIF jika diaktifkan
    exif_bytes = None
    if enable_geotag:
        exif_bytes = update_exif_metadata(
            image=uploaded_file,
            datetime_original=datetime_combined,
            latitude=latitude if latitude and longitude else None,
            longitude=longitude if latitude and longitude else None
        )
    
    # Tampilkan hasil
    with col2:
        st.image(watermarked_img, caption="Gambar dengan Watermark", use_column_width=True)
        
        # Download button
        buf = BytesIO()
        
        # Simpan dengan metadata EXIF jika ada
        if exif_bytes:
            watermarked_img.save(buf, format="JPEG", quality=95, exif=exif_bytes)
        else:
            watermarked_img.save(buf, format="JPEG", quality=95)
            
        byte_im = buf.getvalue()
        
        st.download_button(
            label="Download Gambar",
            data=byte_im,
            file_name="watermarked_image.jpg",
            mime="image/jpeg"
        )

# Petunjuk penggunaan
with st.expander("Petunjuk Penggunaan"):
    st.markdown("""
    1. **Upload foto** Anda melalui area upload
    2. Atur **waktu, tanggal, dan lokasi** di sidebar
    3. Masukkan **nama Anda**
    4. Untuk geotagging:
       - Masukkan **koordinat latitude dan longitude**
       - Pastikan "Aktifkan Geotagging" dicentang
    5. Hasil akan muncul di sebelah kanan
    6. Klik **Download Gambar** untuk menyimpan dengan metadata baru
    """)
    st.markdown("""
    **Catatan Geotagging:**
    - Metadata EXIF akan diperbarui dengan:
      - Tanggal/waktu baru
      - Koordinat GPS (jika diberikan)
    - Fitur ini bekerja untuk format JPEG
    - Beberapa aplikasi mungkin perlu refresh untuk melihat metadata baru
    """)

# Catatan tentang Google Maps API
st.info("""
Untuk peta yang lebih baik, Anda bisa menggunakan Google Maps API dengan:
1. Dapatkan API key dari Google Cloud Platform
2. Tambahkan ke kode di fungsi `get_map_url()`
""")