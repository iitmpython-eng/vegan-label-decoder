import streamlit as st
import google.generativeai as genai
import PIL.Image

# --- 1. DIRECT KEY SETUP (Temporary) ---
# Paste your key inside the quotes below. 
# WARNING: Do not keep this here forever! It is just for testing.
api_key = "AIzaSy_PASTE_YOUR_FULL_KEY_HERE" 

st.set_page_config(page_title="Vegan Label Decoder", page_icon="🌱")

if api_key == "AIzaSy_PASTE_YOUR_FULL_KEY_HERE":
    st.error("❌ You forgot to paste your actual key in the code!")
    st.stop()

# Configure Gemini
try:
    genai.configure(api_key=api_key)
    # Test the key immediately
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Reply with 'System Operational'")
    st.success(f"✅ Key is Working! AI says: {response.text}")
except Exception as e:
    st.error(f"❌ Key is Invalid: {e}")
    st.stop()

# --- 2. THE APP LOGIC ---
st.title("🌱 Vegan Decoder (Direct Mode)")
uploaded_file = st.file_uploader("Upload label", type=["jpg", "png"])

if uploaded_file:
    image = PIL.Image.open(uploaded_file)
    st.image(image, caption="Your Snap", width=300)
    
    if st.button("Scan Now"):
        prompt = "Is this vegan? Answer yes/no and why."
        response = model.generate_content([prompt, image])
        st.write(response.text)
