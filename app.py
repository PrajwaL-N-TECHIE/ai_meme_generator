import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
import base64
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Meme Generator",
    page_icon="😂",
    layout="centered",
)

# --- Custom CSS for a polished look ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .st-emotion-cache-1v0mbdj > img {
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }
    .stButton>button {
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# --- Image Manipulation Function ---
def draw_text_on_image(image, top_text, bottom_text):
    """
    Draws top and bottom text on an image to create a meme.

    Args:
        image (PIL.Image): The base image.
        top_text (str): The text to draw on the top.
        bottom_text (str): The text to draw on the bottom.

    Returns:
        PIL.Image: The image with text drawn on it.
    """
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # A simple approach to font size based on image width
    font_size = int(width / 10)
    try:
        # Use a common, bold font. If not available, Pillow's default will be used.
        font = ImageFont.truetype("impact.ttf", font_size)
    except IOError:
        st.warning("Impact font not found. Using default font. For best results, install the 'Impact' font on your system.")
        font = ImageFont.load_default()

    # Function to draw text with a black outline
    def draw_text_with_outline(text, x, y):
        # Outline
        draw.text((x-2, y-2), text, font=font, fill="black")
        draw.text((x+2, y-2), text, font=font, fill="black")
        draw.text((x-2, y+2), text, font=font, fill="black")
        draw.text((x+2, y+2), text, font=font, fill="black")
        # Fill
        draw.text((x, y), text, font=font, fill="white")

    # Top text
    if top_text:
        top_text = top_text.upper()
        top_text_bbox = draw.textbbox((0, 0), top_text, font=font)
        top_text_width = top_text_bbox[2] - top_text_bbox[0]
        top_text_height = top_text_bbox[3] - top_text_bbox[1]
        x = (width - top_text_width) / 2
        y = 10
        draw_text_with_outline(top_text, x, y)

    # Bottom text
    if bottom_text:
        bottom_text = bottom_text.upper()
        bottom_text_bbox = draw.textbbox((0, 0), bottom_text, font=font)
        bottom_text_width = bottom_text_bbox[2] - bottom_text_bbox[0]
        bottom_text_height = bottom_text_bbox[3] - bottom_text_bbox[1]
        x = (width - bottom_text_width) / 2
        y = height - bottom_text_height - 10
        draw_text_with_outline(bottom_text, x, y)

    return image

# --- AI Caption Generation ---
@st.cache_data(show_spinner="✨ AI is thinking of a caption...")
def get_ai_caption(image_bytes, api_key):
    """
    Gets a funny meme caption from the Gemini Vision API.
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    prompt = "Analyze this image and generate a short, funny meme caption for it. Provide only the text for the caption, without any extra formatting or labels."
    
    # Convert image bytes to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
            ]
        }]
    }

    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        if "candidates" in result:
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            st.error("AI could not generate a caption. The response was malformed.")
            return ""
    except Exception as e:
        st.error(f"An error occurred while contacting the AI: {e}")
        return ""

# --- Main Application UI ---
st.title("😂 AI Meme Generator")
st.markdown("Create your own memes or let AI suggest a caption for you!")

# API Key Input
api_key = st.text_input("Enter your Google AI API Key to enable AI features", type="password")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read the uploaded image
    image = Image.open(uploaded_file).convert("RGB")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Image")
        st.image(image, use_column_width=True)

        # AI Suggestion Button
        if api_key:
            if st.button("✨ Suggest Caption with AI"):
                # Convert image to bytes for API call
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                img_bytes = buffered.getvalue()
                
                ai_caption = get_ai_caption(img_bytes, api_key)
                st.session_state.bottom_text = ai_caption # Put the caption in the bottom text field
        else:
            st.info("Enter an API key above to enable AI caption suggestions.")


    with col2:
        st.subheader("Create Your Meme")
        top_text = st.text_input("Top Text", key="top_text")
        bottom_text = st.text_input("Bottom Text", key="bottom_text")

        if top_text or bottom_text:
            meme_image = draw_text_on_image(image.copy(), top_text, bottom_text)
            st.image(meme_image, caption="Your Generated Meme", use_column_width=True)
            
            # Download button
            buf = BytesIO()
            meme_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="Download Meme",
                data=byte_im,
                file_name="meme.png",
                mime="image/png"
            )
else:
    st.info("Upload an image to get started.")

# --- Footer ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Powered by Streamlit & Google Gemini</p>", unsafe_allow_html=True)
