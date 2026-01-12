import streamlit as st
import google.generativeai as genai
import PIL.Image

# --- 1. CONFIGURATION & MODERN UI SETUP ---
st.set_page_config(
    page_title="Vegan Label Decoder",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the "Modern Look"
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Style the main title */
    h1 {
        color: #2E8B57; /* SeaGreen */
        font-weight: 600;
        text-align: center;
    }

    /* Style the buttons */
    .stButton>button {
        width: 100%;
        background-color: #2E8B57;
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #3CB371;
        color: white;
    }

    /* Hide the default Streamlit menu/footer for a cleaner app look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Add a subtle card effect to the uploader */
    .stFileUploader {
        border: 1px dashed #2E8B57;
        border-radius: 12px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. API KEY SETUP ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Google API Key", type="password")

if not api_key:
    st.warning("⚠️ Please enter your API Key in the sidebar or Secrets to start.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. DATABASE (TOOL) ---
ingredient_knowledge_base = {
    "casein": {"vegan": False, "source": "Milk protein"},
    "whey": {"vegan": False, "source": "Milk by-product"},
    "carmine": {"vegan": False, "source": "Crushed insects (E120)"},
    "gelatin": {"vegan": False, "source": "Animal collagen"},
    "honey": {"vegan": False, "source": "Bees"},
    "lard": {"vegan": False, "source": "Pig fat"}
}

def check_ingredient_database(ingredients: list):
    results = []
    for item in ingredients:
        key = item.lower().strip()
        found = False
        for db_key, data in ingredient_knowledge_base.items():
            if db_key in key:
                results.append({
                    "ingredient": item,
                    "is_vegan": data['vegan'],
                    "source": data['source']
                })
                found = True
                break
        if not found:
             results.append({"ingredient": item, "status": "Unknown/Safe"})
    return results

model = genai.GenerativeModel('gemini-1.5-flash', tools=[check_ingredient_database])

# --- 4. THE MAIN UI ---
st.title("🌱 Vegan Decoder")
st.markdown("<p style='text-align: center; color: #666;'>Snap a photo. Know what's inside.</p>", unsafe_allow_html=True)
st.write("") # Spacer

uploaded_file = st.file_uploader("Upload label photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    # Use columns to center the image on desktop
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        image = PIL.Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Your Snap")
        
        # Analyze Button
        if st.button("🔍 Scan Ingredients"):
            with st.spinner(' analyzing...'):
                try:
                    prompt = """
                    You are a strict Vegan Decoder.
                    1. Extract INGREDIENTS from the image.
                    2. Check them against your database.
                    3. Output format:
                       - If NOT VEGAN: Start with '❌ NON-VEGAN DETECTED'. List the non-vegan items clearly.
                       - If VEGAN: Start with '✅ LIKELY VEGAN'.
                       - Keep the description short and friendly.
                    """
                    response = model.generate_content([prompt, image])
                    
                    # Modern Result Card
                    if "NOT VEGAN" in response.text:
                        st.error(response.text, icon="❌")
                    elif "LIKELY VEGAN" in response.text:
                        st.success(response.text, icon="✅")
                    else:
                        st.info(response.text, icon="ℹ️")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
