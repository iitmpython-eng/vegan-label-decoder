import streamlit as st
import google.generativeai as genai
import PIL.Image
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Vegan Agent India",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the "Modern Green" Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Header & Tabs */
    h1 { color: #2E8B57; font-weight: 700; text-align: center; font-size: 2.2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #f0f2f6; border-radius: 8px;
        padding: 10px 16px; color: #555; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E8B57 !important; color: white !important;
    }

    /* Input & Buttons */
    .stTextInput>div>div>input { border-radius: 10px; }
    .stButton>button {
        width: 100%; background-color: #2E8B57; color: white;
        border-radius: 10px; padding: 12px; font-weight: 600; border: none;
    }
    .stButton>button:hover { background-color: #3CB371; }
    
    /* Hide Streamlit Branding */
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
api_key = None
# Try to get key from Secrets (Best for deployment)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback for local testing or manual entry
    api_key = st.sidebar.text_input("Enter API Key", type="password")

if not api_key:
    st.warning("⚠️ Please add your Google API Key to Secrets to use the Agent.")
    st.stop()

# --- 3. KNOWLEDGE BASE (Strict Tool) ---
# Customized for Indian Market
ingredient_database = {
    # Non-Vegan (Red Flags)
    "casein": {"vegan": False, "source": "Milk"},
    "whey": {"vegan": False, "source": "Milk"},
    "gelatin": {"vegan": False, "source": "Animal Bones"},
    "isinglass": {"vegan": False, "source": "Fish"},
    "carmine": {"vegan": False, "source": "Insects (E120)"},
    "e120": {"vegan": False, "source": "Insects"},
    "shellac": {"vegan": False, "source": "Lac Bugs (E904)"},
    "lard": {"vegan": False, "source": "Pig Fat"},
    "ghee": {"vegan": False, "source": "Clarified Butter"},
    "paneer": {"vegan": False, "source": "Cottage Cheese"},
    "honey": {"vegan": False, "source": "Bees"},
    "milk solids": {"vegan": False, "source": "Dairy"},
    # Safe
    "agar": {"vegan": True, "source": "Seaweed"},
    "pectin": {"vegan": True, "source": "Fruit"},
    "maida": {"vegan": True, "source": "Refined Wheat Flour"},
    "dalda": {"vegan": True, "source": "Vegetable Oil (check Vitamin D source)"}
}

def check_ingredients_tool(ingredients_list: list):
    """Checks a list of ingredients against the local strict database."""
    results = []
    for item in ingredients_list:
        clean_item = item.lower().strip()
        for db_key, data in ingredient_database.items():
            if db_key in clean_item:
                results.append({
                    "ingredient": item,
                    "is_vegan": data['vegan'],
                    "source": data['source']
                })
                break
    return results

# --- 4. MODEL SETUP ---
genai.configure(api_key=api_key)

# Model 1: Local Expert (Vision + Database Tool)
local_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[check_ingredients_tool]
)

# Model 2: Web Agent (Google Search Tool)
# This model has access to the internet for "Research Mode"
search_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[{'google_search': {}}] 
)

# --- 5. THE SUPER APP UI ---
st.title("🌱 Vegan Agent India")

# Three Main Features
tab1, tab2, tab3 = st.tabs(["📸 Photo Scan", "⌨️ Quick Check", "🌐 Web Agent"])

# === TAB 1: PHOTO SCAN (Vision) ===
with tab1:
    st.markdown("### Scan Product Label")
    st.caption("Upload a photo of the ingredients list.")
    uploaded_file = st.file_uploader("Upload photo", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file:
        image = PIL.Image.open(uploaded_file)
        st.image(image, use_container_width=True)
        
        if st.button("🔍 Scan Ingredients", key="btn_scan"):
            with st.spinner('Reading label & checking database...'):
                try:
                    prompt = """
                    Act as a strict Vegan Scanner. 
                    1. Extract INGREDIENTS from image. 
                    2. Check against tools. 
                    3. If NON-VEGAN: Start with '❌ NOT VEGAN'. List items.
                    4. If SAFE: Start with '✅ LIKELY VEGAN'.
                    """
                    response = local_model.generate_content([prompt, image])
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

# === TAB 2: QUICK CHECK (Text Tool) ===
with tab2:
    st.markdown("### Instant Checker")
    st.caption("Type an ingredient (e.g., 'E120', 'Ghee', 'Casein').")
    
    user_text = st.text_input("Enter ingredient:", placeholder="Type here...")
    
    if st.button("Check Database", key="btn_text"):
        if user_text:
            with st.spinner('Checking strict database...'):
                prompt = f"""
                Check if '{user_text}' is vegan using the `check_ingredients_tool`.
                If found in DB, give the source.
                If not found, use general knowledge.
                Keep it under 2 sentences.
                """
                response = local_model.generate_content(prompt)
                st.success(response.text)

# === TAB 3: WEB AGENT (Google Search) ===
with tab3:
    st.markdown("### 🌐 Research Agent")
    st.caption("Ask about restaurants, recipes, or regional dishes.")
    
    st.markdown("**Try asking:**")
    st.markdown("- *'Is the McAloo Tikki vegan in India?'*")
    st.markdown("- *'Vegan restaurants in Patna'*")
    
    query = st.text_input("Ask the Web Agent:", placeholder="Search query...")
    
    if st.button("Search Web", key="btn_web"):
        if query:
            with st.spinner('Searching Google...'):
                try:
                    # The Search Model will "Google it" for you
                    response = search_model.generate_content(query)
                    st.markdown(response.text)
                    
                    # Show Sources if available
                    if response.candidates[0].grounding_metadata.grounding_chunks:
                        st.caption("🔍 Verified with Google Search")
                except Exception as e:
                    st.error(f"Search Error: {e}")
