import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import datetime
import requests
from io import BytesIO
import textwrap

# Style Configuration
WATERMARK_BG_COLOR = (0, 0, 0, 160)  # Semi-transparent black
TEXT_COLOR = (255, 255, 255)         # White
LINE_COLOR = (255, 255, 255, 200)    # Semi-transparent white
MAP_BG_COLOR = (40, 40, 40)          # Dark gray for map background

def get_optimal_font_sizes(img_height):
    """Calculate font sizes based on image height"""
    base_size = max(16, img_height // 25)  # Minimum 16px
    return {
        'title': int(base_size * 1.6),
        'address': int(base_size * 1.1),
        'datetime': int(base_size * 1.4),
        'temperature': int(base_size * 1.3)
    }

def get_osm_map(latitude, longitude, width=400, height=200, zoom=15):
    """Get map from OpenStreetMap with error handling"""
    try:
        url = f"https://maps.geoapify.com/v1/staticmap?style=osm-carto&width={width}&height={height}&center=lonlat:{longitude},{latitude}&zoom={zoom}&marker=lonlat:{longitude},{latitude};color:%23ff0000;size:medium"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        st.warning(f"Map loading failed: {str(e)}")
        return None

def create_professional_watermark(original_img, time_str, date_day_str, location, temp_c="33", temp_f="91", map_img=None):
    """Create watermark with professional layout"""
    try:
        img = original_img.copy().convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Calculate sizes
        img_width, img_height = img.size
        font_sizes = get_optimal_font_sizes(img_height)
        wm_height = int(img_height * 0.35)
        margin = int(img_width * 0.03)
        
        # Create watermark background
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle((0, img_height - wm_height, img_width, img_height), fill=WATERMARK_BG_COLOR)
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Load fonts (with fallback)
        try:
            font_title = ImageFont.truetype("arialbd.ttf", font_sizes['title'])
            font_address = ImageFont.truetype("arial.ttf", font_sizes['address'])
            font_datetime = ImageFont.truetype("arial.ttf", font_sizes['datetime'])
            font_temp = ImageFont.truetype("arial.ttf", font_sizes['temperature'])
        except:
            font_title = ImageFont.load_default()
            font_address = ImageFont.load_default()
            font_datetime = ImageFont.load_default()
            font_temp = ImageFont.load_default()
        
        # Position tracking
        text_x = margin
        text_y = img_height - wm_height + margin
        
        # Draw address lines
        loc_lines = [line.strip() for line in location.split('\n') if line.strip()][:6]  # Max 6 lines
        
        if loc_lines:
            # First line as title
            draw.text((text_x, text_y), loc_lines[0], font=font_title, fill=TEXT_COLOR)
            text_y += int(font_sizes['title'] * 1.3)
            
            # Subsequent lines
            for line in loc_lines[1:]:
                draw.text((text_x, text_y), line, font=font_address, fill=TEXT_COLOR)
                text_y += int(font_sizes['address'] * 1.2)
        
        # Separator line
        draw.line((text_x, text_y + 5, img_width - margin, text_y + 5), fill=LINE_COLOR, width=1)
        text_y += int(font_sizes['address'] * 0.8)
        
        # Date and time
        datetime_text = f"{date_day_str} {time_str}"
        draw.text((text_x, text_y), datetime_text, font=font_datetime, fill=TEXT_COLOR)
        
        # Temperature
        temp_text = f"{temp_c}°C / {temp_f}°F"
        temp_width = draw.textlength(temp_text, font=font_temp)
        draw.text((img_width - margin - temp_width, text_y), temp_text, font=font_temp, fill=TEXT_COLOR)
        
        # Add map if available
        if map_img:
            map_width = min(int(img_width * 0.3), 300)  # Max 300px
            map_height = min(int(wm_height * 0.6), 200) # Max 200px
            map_img = map_img.resize((map_width, map_height))
            
            map_x = img_width - map_width - margin
            map_y = img_height - wm_height + margin
            
            # Map background
            map_bg = Image.new('RGB', (map_width + 10, map_height + 10), MAP_BG_COLOR)
            img.paste(map_bg, (map_x - 5, map_y - 5))
            img.paste(map_img, (map_x, map_y))
        
        return img
    
    except Exception as e:
        st.error(f"Watermark creation error: {str(e)}")
        return original_img

# Streamlit UI
st.set_page_config(page_title="Professional Watermark Tool", layout="wide", page_icon="📷")
st.title("📷 Professional Watermark Tool")

with st.sidebar:
    st.header("Settings", divider="gray")
    
    # Location Input
    location = st.text_area(
        "Full Address",
        "Jl. Contoh No. 123\nKelurahan Contoh\nKecamatan Contoh\nKota/Kabupaten Contoh\nProvinsi Contoh\nKode Pos 12345",
        height=150,
        help="Enter complete address information"
    )
    
    # Map Coordinates
    with st.expander("Map Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            lat = st.text_input("Latitude", "-6.2088", help="Example: -6.2088")
        with col2:
            lon = st.text_input("Longitude", "106.8456", help="Example: 106.8456")
        
        show_map = st.checkbox("Show Map", value=True, help="Display map on watermark")
    
    # Date & Time
    with st.expander("Date & Time", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.date.today())
        with col2:
            time = st.time_input("Time", datetime.time(13, 30))
    
    # Temperature
    with st.expander("Temperature", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            temp_c = st.text_input("°C", "33")
        with col2:
            temp_f = st.text_input("°F", "91")
    
    # Format strings
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_str = days[date.weekday()][:3]
    date_day_str = f"{date.strftime('%Y-%m-%d')} ({day_str})"
    time_str = time.strftime("%I:%M%p").lower()

# File Upload
uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], accept_multiple_files=False)

if uploaded_file:
    try:
        original_img = Image.open(uploaded_file)
        
        # Get map image
        map_image = None
        if show_map and lat and lon:
            with st.spinner("Loading map..."):
                map_image = get_osm_map(lat, lon)
        
        # Create watermark
        with st.spinner("Applying watermark..."):
            watermarked_img = create_professional_watermark(
                original_img,
                time_str=time_str,
                date_day_str=date_day_str,
                location=location,
                temp_c=temp_c,
                temp_f=temp_f,
                map_img=map_image
            )
        
        # Display results
        col1, col2 = st.columns(2)
        with col1:
            st.image(original_img, caption="Original Image", use_column_width=True)
        with col2:
            st.image(watermarked_img, caption="Watermarked Image", use_column_width=True)
            
            # Download button
            buf = BytesIO()
            watermarked_img.save(buf, format="JPEG", quality=95)
            st.download_button(
                "Download Watermarked Image",
                buf.getvalue(),
                "professional_watermark.jpg",
                "image/jpeg",
                type="primary"
            )
    
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")

# Instructions
with st.expander("Usage Guide", expanded=False):
    st.markdown("""
    **Professional Watermark Features:**
    - Clean, readable text with optimal sizing
    - Responsive layout adapts to image size
    - Integrated map from coordinates
    - Professional color scheme
    
    **Tips for Best Results:**
    1. Use high-quality images (min. 1200px width recommended)
    2. Keep address concise (4-6 lines ideal)
    3. Verify coordinates for accurate map display
    4. For portrait images, consider reducing text lines
    
    **Map Notes:**
    - Uses OpenStreetMap via Geoapify
    - Free tier allows 3000 requests/day
    - Attribution not required but appreciated
    """)
