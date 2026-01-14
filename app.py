import streamlit as st
import google.generativeai as genai
import PIL.Image

st.set_page_config(page_title="Vegan Agent", page_icon="🌱")

# API Key Setup
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Google API Key", type="password")

if not api_key:
    st.warning("⚠️ Enter API Key to start.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🌱 Vegan Agent India")
st.write("Upload a photo to check if it's vegan.")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png"])
if uploaded_file and st.button("Check Now"):
    with st.spinner('Analyzing...'):
        try:
            image = PIL.Image.open(uploaded_file)
            st.image(image, width=300)
            response = model.generate_content(["Is this vegan? Answer Yes/No.", image])
            st.success(response.text)
        except Exception as e:
            st.error(f"Error: {e}")
