import streamlit as st
import google.generativeai as genai
import PIL.Image

# --- 1. CONFIGURATION & MODERN UI ---
st.set_page_config(
    page_title="Vegan Label Decoder",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize History in Session State if it doesn't exist
if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []

# Custom CSS for the "Modern Look"
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1 { color: #2E8B57; font-weight: 600; text-align: center; }
    .stButton>button {
        width: 100%; background-color: #2E8B57; color: white;
        border-radius: 12px; padding: 10px 24px; border: none; font-weight: 600;
    }
    .stButton>button:hover { background-color: #3CB371; color: white; }
    .stFileUploader { border: 1px dashed #2E8B57; border-radius: 12px; padding: 20px; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 2. API KEY SETUP ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Google API Key", type="password")

if not api_key:
    st.warning("⚠️ Please enter your API Key in the sidebar or Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. EXPANDED DATABASE (The Knowledge Base) ---
# Added E-numbers and common tricky ingredients
ingredient_knowledge_base = {
    # Dairy & Eggs
    "casein": {"vegan": False, "source": "Milk"},
    "whey": {"vegan": False, "source": "Milk"},
    "lactose": {"vegan": False, "source": "Milk"},
    "albumen": {"vegan": False, "source": "Egg"},
    "ghee": {"vegan": False, "source": "Butter fat"},
    
    # Animal Fats & Tissues
    "gelatin": {"vegan": False, "source": "Animal collagen (E441)"},
    "lard": {"vegan": False, "source": "Pig fat"},
    "tallow": {"vegan": False, "source": "Beef fat"},
    "suet": {"vegan": False, "source": "Animal fat"},
    "isinglass": {"vegan": False, "source": "Fish bladder (in beer/wine)"},
    "lanolin": {"vegan": False, "source": "Sheep wool grease (E913)"},
    
    # Insects
    "carmine": {"vegan": False, "source": "Crushed beetles (E120)"},
    "cochineal": {"vegan": False, "source": "Crushed beetles (E120)"},
    "shellac": {"vegan": False, "source": "Lac bugs (E904)"},
    "beeswax": {"vegan": False, "source": "Bees (E901)"},
    "honey": {"vegan": False, "source": "Bees"},
    
    # Common E-Numbers (Non-Vegan)
    "e120": {"vegan": False, "source": "Carmine (Insects)"},
    "e441": {"vegan": False, "source": "Gelatin"},
    "e542": {"vegan": False, "source": "Bone Phosphate"},
    "e901": {"vegan": False, "source": "Beeswax"},
    "e904": {"vegan": False, "source": "Shellac"},
    "e913": {"vegan": False, "source": "Lanolin"},
    "e966": {"vegan": False, "source": "Lactitol (Milk)"},
    
    # Vegan Safe (For false positives)
    "cocoa butter": {"vegan": True, "source": "Cacao bean"},
    "lactic acid": {"vegan": True, "source": "Fermented sugar (usually vegan)"},
    "pectin": {"vegan": True, "source": "Fruit skin"},
    "agar": {"vegan": True, "source": "Seaweed"}
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
             # Don't list everything, just unknowns
             pass 
    return results

model = genai.GenerativeModel('gemini-1.5-flash', tools=[check_ingredient_database])

# --- 4. THE UI LOGIC ---
st.title("🌱 Vegan Decoder")
st.markdown("<p style='text-align: center; color: #666;'>Snap a photo. Know what's inside.</p>", unsafe_allow_html=True)
st.write("") 

uploaded_file = st.file_uploader("Upload label photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        image = PIL.Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Your Snap")
        
        if st.button("🔍 Scan Ingredients"):
            with st.spinner('Checking database...'):
                try:
                    # Optimized Prompt for Speed (Less words = Faster)
                    prompt = """
                    Act as a strict Vegan Scanner.
                    1. Extract INGREDIENTS text from image.
                    2. Check against `check_ingredient_database` tool.
                    3. If NON-VEGAN found: Start response with "❌ NOT VEGAN" and list the item + source.
                    4. If safe: Start with "✅ LIKELY VEGAN".
                    5. Keep response under 30 words.
                    """
                    
                    response = model.generate_content([prompt, image])
                    text_result = response.text
                    
                    # Save to History
                    # We save a tuple: (Image object, Result text)
                    st.session_state.scan_history.insert(0, {"name": uploaded_file.name, "result": text_result})
                    # Keep only last 3
                    if len(st.session_state.scan_history) > 3:
                        st.session_state.scan_history.pop()

                    # Display Current Result
                    if "NOT VEGAN" in text_result:
                        st.error(text_result, icon="❌")
                    elif "LIKELY VEGAN" in text_result:
                        st.success(text_result, icon="✅")
                    else:
                        st.info(text_result, icon="ℹ️")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 5. HISTORY SECTION ---
if st.session_state.scan_history:
    st.markdown("---")
    st.subheader("🕒 Recent Scans")
    
    for item in st.session_state.scan_history:
        with st.container():
            # Simple card style for history
            st.text(f"📄 {item['name']}")
            if "NOT VEGAN" in item['result']:
                st.error(item['result'])
            else:
                st.success(item['result'])
