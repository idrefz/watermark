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
        lat_num = float(latitude)
        lon_num = float(longitude)
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_num}&lon={lon_num}&addressdetails=1"
        headers = {'User-Agent': 'WatermarkApp/1.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'address' in data:
            address = data.get('address', {})
            address_lines = []

            if address.get('building'):
                address_lines.append(f"Gedung {address['building']}")
            if address.get('road'):
                address_lines.append(f"Jl. {address['road']}")

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

def create_complete_watermark(image, time_str, date_day_str, location, temp_c="33°C", temp_f="91°F", map_img=None):
    try:
        img = image.copy()
        if img.mode != 'RGB':
            img = img.convert('RGB')

        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw_overlay = ImageDraw.Draw(overlay)
        wm_height = int(img.height * 0.35)
        wm_position = (0, img.height - wm_height, img.width, img.height)
        draw_overlay.rectangle(wm_position, fill=(0,0,0,160))

        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_medium = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 24)
            font_bold = ImageFont.truetype("arialbd.ttf", 40)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()

        margin = 20
        text_x = margin
        text_y = img.height - wm_height + margin

        loc_lines = location.split('\n')[:8]
        for i, line in enumerate(loc_lines):
            if i == 0 and line.strip():
                draw_overlay.text((text_x, text_y), line, font=font_bold, fill=(255,255,255))
                text_y += 50
            elif line.strip():
                draw_overlay.text((text_x, text_y), line, font=font_small, fill=(255,255,255))
                text_y += 28

        if loc_lines:
            draw_overlay.line((text_x, text_y+5, img.width - margin, text_y+5), fill=(255,255,255,150), width=2)
            text_y += 20

        draw_overlay.text((text_x, text_y), f"{date_day_str}  {time_str}", font=font_medium, fill=(255,255,255))
        temp_text = f"{temp_c} / {temp_f}"
        temp_width = draw_overlay.textlength(temp_text, font=font_medium)
        draw_overlay.text((img.width - margin - temp_width, text_y), temp_text, font=font_medium, fill=(255,255,255))

        if map_img:
            map_size = (min(220, img.width//3), min(130, wm_height//2))
            map_img = map_img.resize(map_size)
            map_x = img.width - map_size[0] - margin
            map_y = img.height - wm_height + margin

            map_bg = Image.new('RGB', (map_size[0]+10, map_size[1]+10), (40,40,40))
            overlay.paste(map_bg, (map_x-5, map_y-5))
            overlay.paste(map_img, (map_x, map_y))

        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        return img

    except Exception as e:
        st.error(f"Error membuat watermark: {str(e)}")
        return image
