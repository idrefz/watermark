import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO

# Fungsi: Ambil alamat dari koordinat
def get_complete_address(latitude, longitude):
    try:
        lat_num = float(latitude)
        lon_num = float(longitude)
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_num}&lon={lon_num}&addressdetails=1"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'address' in data:
            addr = data['address']
            lines = []
            if addr.get('road'):
                lines.append(f"Jl. {addr['road']}")
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
            lines.append(f"Koordinat: {lat_num:.6f}, {lon_num:.6f}")
            return "\n".join(lines)
        return f"Koordinat: {latitude}, {longitude}"
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi: Ambil gambar peta dari Yandex Maps
def get_osm_map(latitude, longitude, zoom=16, size=(600, 300)):
    try:
        lat_num = float(latitude)
        lon_num = float(longitude)
        url = f"https://static-maps.yandex.ru/1.x/?ll={lon_num},{lat_num}&z={zoom}&size={size[0]},{size[1]}&l=map&pt={lon_num},{lat_num},pm2rdl"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        st.warning(f"Gagal memuat peta: {str(e)}")
        return None

# Fungsi: Membuat watermark pada gambar
def create_watermark(image, time_str, date_str, location, temp_c, temp_f, map_img=None):
    img = image.copy().convert('RGB')
    wm_height = int(img.height * 0.35)

    # Buat overlay untuk watermark
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.rectangle((0, img.height - wm_height, img.width, img.height), fill=(0, 0, 0, 160))

    # Font
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 36)
        font_text = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 22)
    except:
        font_bold = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    margin = 30
    text_x = margin
    text_y = img.height - wm_height + margin

    # Teks lokasi
    for i, line in enumerate(location.split('\n')):
        font = font_bold if i == 0 else font_small
        draw_overlay.text((text_x, text_y), line, font=font, fill=(255, 255, 255))
        text_y += 32

    # Garis pembatas
    draw_overlay.line((text_x, text_y, img.width - margin, text_y), fill=(255, 255, 255), width=2)
    text_y += 15

    # Tanggal & Waktu
    draw_overlay.text((text_x, text_y), f"{date_str}  {time_str}", font=font_text, fill=(255, 255, 255))

    # Suhu
    temp = f"{temp_c} / {temp_f}"
    temp_width = draw_overlay.textlength(temp, font=font_text)
    draw_overlay.text((img.width - margin - temp_width, text_y), temp, font=font_text, fill=(255, 255, 255))

    # Peta
    if map_img:
        map_size = (220, 130)
        map_img = map_img.resize(map_size)
        map_x = img.width - map_size[0] - margin
        map_y = img.height - wm_height + margin
        overlay.paste(map_img, (map_x, map_y))

    # Gabungkan overlay ke gambar
    final = Image.alpha_composite(img.convert('RGBA'), overlay)
    return final.convert('RGB')

# ========== Streamlit App ==========
st.set_page_config(page_title="Watermark Tool", layout="wide")
st.title("📍 Aplikasi Watermark Foto Otomatis")

with st.sidebar:
    st.header("Pengaturan")
    lat = st.text_input("Latitude", "-6.1101")
    lon = st.text_input("Longitude", "106.1633")

    if st.button("📍 Ambil Alamat"):
        address = get_complete_address(lat, lon)
        if not address.startswith("Error:"):
            st.session_state['address'] = address
        else:
            st.error(address)

    lokasi = st.text_area("Alamat Lengkap", st.session_state.get('address', ""), height=180)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        tanggal = st.date_input("Tanggal", datetime.date.today())
    with col2:
        waktu = st.time_input("Waktu", datetime.datetime.now().time())

    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    hari_str = hari[tanggal.weekday()]
    tanggal_str = f"{tanggal.strftime('%Y-%m-%d')} ({hari_str[:3]})"
    waktu_str = waktu.strftime("%H:%M")

    suhu_c = st.text_input("Suhu °C", "33")
    suhu_f = st.text_input("Suhu °F", "91")

    show_map = st.checkbox("Tampilkan Peta", value=True)

# ========== Upload Gambar ==========
uploaded_file = st.file_uploader("Unggah Foto", type=["jpg", "jpeg", "png"])
if uploaded_file:
    img = Image.open(uploaded_file)
    peta_img = get_osm_map(lat, lon) if show_map else None

    result = create_watermark(
        image=img,
        time_str=waktu_str,
        date_str=tanggal_str,
        location=lokasi,
        temp_c=f"{suhu_c}°C",
        temp_f=f"{suhu_f}°F",
        map_img=peta_img
    )

    col1, col2 = st.columns(2)
    with col1:
        st.image(img, caption="Foto Asli", use_column_width=True)
    with col2:
        st.image(result, caption="Foto dengan Watermark", use_column_width=True)

        buf = BytesIO()
        result.save(buf, format="JPEG", quality=95)
        st.download_button("⬇️ Download Hasil", buf.getvalue(), "watermarked.jpg", "image/jpeg")
