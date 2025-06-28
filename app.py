import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import re

# ======================== FUNGSI: ALAMAT ========================
def get_complete_address(lat, lon):
    try:
        lat_num = float(lat)
        lon_num = float(lon)
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_num}&lon={lon_num}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()

        if 'address' in data:
            addr = data['address']
            address_lines = []

            if addr.get('road'):
                line = f"Jl. {addr['road']}"
                if addr.get('house_number'):
                    line += f" No. {addr['house_number']}"
                address_lines.append(line)

            if addr.get('village') or addr.get('suburb'):
                address_lines.append(f"Kel. {addr.get('village') or addr.get('suburb')}")

            if addr.get('subdistrict') or addr.get('county'):
                address_lines.append(f"Kec. {addr.get('subdistrict') or addr.get('county')}")

            if addr.get('city') or addr.get('town'):
                address_lines.append(f"Kota {addr.get('city') or addr.get('town')}")

            if addr.get('state'):
                address_lines.append(f"Prov. {addr['state']}")

            if addr.get('postcode'):
                address_lines.append(f"Kode Pos: {addr['postcode']}")

            address_lines.append("Indonesia")
            address_lines.append(f"Koordinat: {lat_num:.6f}, {lon_num:.6f}")

            return "\n".join(address_lines)
        return f"Koordinat: {lat}, {lon}"
    except:
        return "Koordinat tidak valid atau gagal mengambil data."

# ======================== FUNGSI: PETA ========================
def get_static_map(lat, lon, size="600x300", zoom=15):
    return f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z={zoom}&size={size}&l=map&pt={lon},{lat},pm2rdl"

# ======================== FUNGSI: WATERMARK ========================
def create_modern_watermark(image, time_str, date_day_str, location,
                            temp_c="33°C", temp_f="91°F",
                            map_img=None, logo_img=None, logo_position="Kanan Bawah"):
    try:
        img = image.copy().convert('RGB')
        draw = ImageDraw.Draw(img)

        wm_height = int(img.height * 0.4)
        wm_position = (0, img.height - wm_height, img.width, img.height)

        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,180))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arialbd.ttf", 42)
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_medium = ImageFont.truetype("arial.ttf", 28)
        except:
            font_title = font_large = font_medium = ImageFont.load_default()

        margin = 25
        text_x = margin
        text_y = img.height - wm_height + margin
        loc_lines = location.strip().split('\n')[:7]

        for i, line in enumerate(loc_lines):
            font = font_title if i == 0 else font_medium
            draw.text((text_x, text_y), line, font=font, fill=(255,255,255))
            text_y += 50 if i == 0 else 35

        draw.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255), width=2)
        text_y += 20

        draw.text((text_x, text_y), f"{date_day_str}  {time_str}", font=font_large, fill=(255,255,255))

        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw.textlength(temp_text, font=font_large)
        draw.text((img.width - margin - temp_width, text_y), temp_text, font=font_large, fill=(255,255,255))

        if map_img:
            response = requests.get(map_img)
            map_image = Image.open(BytesIO(response.content)).resize((250, 150))
            map_bg = Image.new('RGB', (260, 160), (40,40,40))
            img.paste(map_bg, (img.width - 260 - margin, img.height - wm_height + margin - 5))
            img.paste(map_image, (img.width - 250 - margin, img.height - wm_height + margin))

        # Tambahkan logo branding
        if logo_img:
            logo = Image.open(logo_img).convert("RGBA")
            max_logo_width = int(img.width * 0.2)
            w_percent = (max_logo_width / float(logo.size[0]))
            h_size = int((float(logo.size[1]) * float(w_percent)))
            logo = logo.resize((max_logo_width, h_size), Image.ANTIALIAS)

            pos_map = {
                "Kiri Bawah": (margin, img.height - logo.height - margin),
                "Kanan Bawah": (img.width - logo.width - margin, img.height - logo.height - margin),
                "Kiri Atas": (margin, margin),
                "Kanan Atas": (img.width - logo.width - margin, margin)
            }
            position = pos_map.get(logo_position, (margin, margin))
            img.paste(logo, position, mask=logo)

        return img
    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image

# ======================== STREAMLIT UI ========================
st.set_page_config(page_title="Watermark Tool Pro", layout="wide")
st.title("📷 Watermark Foto Lokasi + Logo")

with st.sidebar:
    st.header("Pengaturan Koordinat")
    lat = st.text_input("Latitude", "-6.1101")
    lon = st.text_input("Longitude", "106.1633")

    if st.button("Dapatkan Alamat dari Koordinat"):
        with st.spinner("Mengambil data alamat..."):
            address = get_complete_address(lat, lon)
            if address.startswith("Error"):
                st.error(address)
            else:
                st.session_state.address = address
                st.success("Alamat berhasil didapatkan!")

    location = st.text_area("Alamat Lengkap", st.session_state.get("address", ""), height=180)

    st.header("Tanggal & Waktu")
    date = st.date_input("Tanggal", datetime.date.today())
    time = st.time_input("Waktu", datetime.datetime.now().time())
    day_str = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][date.weekday()]
    date_day_str = f"{date.strftime('%Y-%m-%d')} ({day_str[:3]})"
    time_str = time.strftime("%H:%M")

    st.header("Info Cuaca")
    temp_c = st.text_input("Temperatur (°C)", "33")
    temp_f = st.text_input("Temperatur (°F)", "91")
    show_map = st.checkbox("Tampilkan Peta", True)

    st.subheader("Logo Branding (Opsional)")
    uploaded_logo = st.file_uploader("Unggah Logo (PNG)", type=["png"])
    position_option = st.selectbox("Posisi Watermark", ["Kiri Bawah", "Kanan Bawah", "Kiri Atas", "Kanan Atas"])

uploaded_file = st.file_uploader("📤 Unggah Foto", type=["jpg", "jpeg", "png"])
if uploaded_file:
    try:
        image = Image.open(uploaded_file)
        map_img_url = None

        if show_map:
            coord_match = re.search(r"Koordinat:\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)", location)
            if coord_match:
                lat, lon = coord_match.groups()
                map_img_url = get_static_map(lat, lon)

        watermarked_img = create_modern_watermark(
            image=image,
            time_str=time_str,
            date_day_str=date_day_str,
            location=location,
            temp_c=f"{temp_c}°C",
            temp_f=f"{temp_f}°F",
            map_img=map_img_url,
            logo_img=uploaded_logo,
            logo_position=position_option
        )

        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="📷 Foto Asli", use_column_width=True)
        with col2:
            st.image(watermarked_img, caption="✅ Hasil Watermark", use_column_width=True)
            buf = BytesIO()
            watermarked_img.save(buf, format="JPEG", quality=95)
            st.download_button("⬇️ Download Gambar", buf.getvalue(), "watermarked.jpg", "image/jpeg")

    except Exception as e:
        st.error(f"Gagal memproses gambar: {str(e)}")

with st.expander("❓ Panduan Penggunaan"):
    st.markdown("""
    1. Masukkan koordinat → klik **Dapatkan Alamat**
    2. Pilih tanggal, waktu, suhu
    3. (Opsional) Unggah logo PNG dan atur posisinya
    4. Upload foto → watermark akan muncul
    5. Klik **Download** untuk menyimpan hasil
    """)
