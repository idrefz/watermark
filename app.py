import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap
import piexif
from piexif._exceptions import InvalidImageDataError

# Fungsi untuk membuat watermark
def create_watermark(image, time_str, date_str, day_str, location, name, map_url=None):
    """Create watermarked image with all required parameters"""
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        draw = ImageDraw.Draw(img)
        watermark_height = 250 if map_url else 150
        watermark_position = (0, img.height - watermark_height, img.width, img.height)
        
        # Create semi-transparent overlay
        overlay = Image.new('RGBA', img.size, (255,255,255,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(watermark_position, fill=(255,255,255,180))
        
        # Combine images
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Set fonts
        try:
            font_large = ImageFont.truetype("arial.ttf", 40)
            font_medium = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Position watermark text
        text_x = 20
        text_y = img.height - watermark_height + 20
        
        # Add all watermark elements
        draw.text((text_x, text_y), time_str, font=font_large, fill=(0, 0, 0))
        text_y += 50
        
        date_day_text = f"{date_str}\n{day_str}"
        draw.text((text_x, text_y), date_day_text, font=font_medium, fill=(0, 0, 0))
        text_y += 60
        
        # Add wrapped location text
        for line in textwrap.wrap(location, width=40):
            draw.text((text_x, text_y), line, font=font_small, fill=(0, 0, 0))
            text_y += 25
        
        # Add user name
        draw.text((text_x, text_y), name, font=font_medium, fill=(0, 0, 0))
        
        # Add map if provided
        if map_url:
            try:
                response = requests.get(map_url)
                map_img = Image.open(BytesIO(response.content))
                map_img = map_img.resize((250, 150))
                img.paste(map_img, (img.width - 270, img.height - 170))
            except Exception as e:
                st.warning(f"Failed to load map: {str(e)}")
        
        return img
        
    except Exception as e:
        st.error(f"Error creating watermark: {str(e)}")
        return image

# Fungsi untuk update metadata EXIF
def update_exif_metadata(image_file, datetime_original, latitude=None, longitude=None):
    """Update EXIF metadata with new datetime and GPS coordinates"""
    try:
        # Initialize empty EXIF dict
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
        
        # Handle different input types
        if hasattr(image_file, 'getvalue'):  # Streamlit UploadedFile object
            try:
                exif_dict = piexif.load(image_file.getvalue())
            except:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
        elif hasattr(image_file, 'info'):  # PIL Image object
            try:
                exif_dict = piexif.load(image_file.info.get('exif', b''))
            except:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
        
        # Format datetime for EXIF
        exif_datetime = datetime_original.strftime("%Y:%m:%d %H:%M:%S")
        
        # Update DateTime fields
        exif_dict['0th'][piexif.ImageIFD.DateTime] = exif_datetime
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_datetime
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = exif_datetime
        
        # Add GPS info if valid coordinates provided
        if latitude is not None and longitude is not None:
            try:
                lat_deg = abs(float(latitude))
                lon_deg = abs(float(longitude))
                
                lat_ref = 'N' if float(latitude) >= 0 else 'S'
                lon_ref = 'E' if float(longitude) >= 0 else 'W'
                
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
            except ValueError:
                st.warning("Invalid GPS coordinates provided")
        
        return piexif.dump(exif_dict)
    
    except Exception as e:
        st.warning(f"Could not update EXIF metadata: {str(e)}")
        return None

# Fungsi untuk mendapatkan URL peta
def get_map_url(latitude, longitude, api_key=None):
    if api_key:
        return f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom=15&size=400x200&maptype=roadmap&markers=color:red%7C{latitude},{longitude}&key={api_key}"
    else:
        return f"https://www.openstreetmap.org/export/embed.html?bbox={float(longitude)-0.01},{float(latitude)-0.01},{float(longitude)+0.01},{float(latitude)+0.01}&layer=mapnik&marker={latitude},{longitude}"

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
    try:
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
                map_url = get_map_url(latitude, longitude)
            except:
                st.error("Koordinat tidak valid")
        
        # Buat watermark dengan semua parameter yang diperlukan
        watermarked_img = create_watermark(
            image=image,
            time_str=time_str,
            date_str=date_str,
            day_str=day_str,
            location=location,
            name=name,
            map_url=map_url if show_map else None
        )
        
        # Update metadata EXIF jika diaktifkan
        exif_bytes = None
        if enable_geotag:
            uploaded_file.seek(0)  # Reset file pointer
            exif_bytes = update_exif_metadata(
                image_file=uploaded_file,
                datetime_original=datetime_combined,
                latitude=latitude if latitude and longitude else None,
                longitude=longitude if latitude and longitude else None
            )
        
        # Tampilkan hasil
        with col2:
            st.image(watermarked_img, caption="Gambar dengan Watermark", use_column_width=True)
            
            # Download button
            buf = BytesIO()
            watermarked_img.save(
                buf,
                format="JPEG",
                quality=95,
                exif=exif_bytes if exif_bytes else watermarked_img.info.get('exif')
            )
            byte_im = buf.getvalue()
            
            st.download_button(
                label="Download Gambar",
                data=byte_im,
                file_name="watermarked_image.jpg",
                mime="image/jpeg"
            )
    
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")

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

# Catatan tentang Google Maps API
st.info("""
Untuk peta yang lebih baik, Anda bisa menggunakan Google Maps API dengan:
1. Dapatkan API key dari Google Cloud Platform
2. Tambahkan ke kode di fungsi `get_map_url()`
""")
