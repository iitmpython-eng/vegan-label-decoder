import streamlit as st
import google.generativeai as genai
import PIL.Image
import time

# --- 1. CONFIGURATION & AGENT UI ---
st.set_page_config(
    page_title="Vegan Label Decoder",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the "Modern Green" look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1 { color: #2E8B57; font-weight: 600; text-align: center; margin-bottom: 0px;}
    .stButton>button {
        width: 100%; background-color: #2E8B57; color: white;
        border-radius: 12px; padding: 10px 24px; border: none; font-weight: 600;
        margin-top: 10px;
    }
    .stButton>button:hover { background-color: #3CB371; color: white; }
    .stFileUploader { border: 1px dashed #2E8B57; border-radius: 12px; padding: 20px; }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (The Keys to the Brain) ---
api_key = None
# Try to get key from Secrets (Best for deployment)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback for local testing
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.warning("⚠️ Agent requires API Key to function. Please add it to Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. THE AGENT'S TOOLS (The Body) ---
# The Agent will "call" this function when it needs facts.
# It is better than the LLM guessing because it is deterministic.

ingredient_database = {
    # Non-Vegan (Red Flags)
    "casein": {"vegan": False, "source": "Milk Protein", "risk": "High"},
    "whey": {"vegan": False, "source": "Milk By-product", "risk": "High"},
    "lactose": {"vegan": False, "source": "Milk Sugar", "risk": "High"},
    "gelatin": {"vegan": False, "source": "Animal Collagen", "risk": "High"},
    "isinglass": {"vegan": False, "source": "Fish Bladder (Clarifier)", "risk": "Medium"},
    "carmine": {"vegan": False, "source": "Crushed Beetles (E120)", "risk": "High"},
    "cochineal": {"vegan": False, "source": "Crushed Beetles (E120)", "risk": "High"},
    "shellac": {"vegan": False, "source": "Lac Bugs (Glaze)", "risk": "High"},
    "lard": {"vegan": False, "source": "Pig Fat", "risk": "High"},
    "tallow": {"vegan": False, "source": "Beef Fat", "risk": "High"},
    "vitamin d3": {"vegan": False, "source": "Sheep Wool (Lanolin)", "risk": "Medium"},
    
    # Vegan (Safe List - prevents false alarms)
    "cocoa butter": {"vegan": True, "source": "Cacao Bean", "risk": "None"},
    "lactic acid": {"vegan": True, "source": "Fermented Sugar", "risk": "None"},
    "carnauba wax": {"vegan": True, "source": "Palm Leaves", "risk": "None"},
    "agar": {"vegan": True, "source": "Red Algae", "risk": "None"}
}

def check_ingredients_tool(extracted_ingredients: list):
    """
    Analyzes a list of ingredients against the strict vegan database.
    Returns structured data about any non-vegan items found.
    """
    results = []
    print(f"Agent is checking: {extracted_ingredients}") # Debug log
    
    for item in extracted_ingredients:
        # Normalize text for matching
        clean_item = item.lower().strip()
        
        # Fuzzy match attempt (checking if 'whey powder' contains 'whey')
        matched = False
        for db_key, data in ingredient_database.items():
            if db_key in clean_item:
                results.append({
                    "ingredient": item,
                    "is_vegan": data['vegan'],
                    "source": data['source'],
                    "risk": data['risk']
                })
                matched = True
                break
                
    return results

# Register the tool with the Agent
tools_list = [check_ingredients_tool]

# Initialize the Gemini Agent with the Tool
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', # Flash is fast and cheap for tools
    tools=tools_list
)

# --- 4. SESSION STATE (The Memory) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 5. THE MAIN INTERFACE ---
st.title("🌱 Vegan Decoder")
st.caption("Powered by Google Gemini Agents")

uploaded_file = st.file_uploader("Upload label photo", type=["jpg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    # Layout: Image on left, Results on right (Desktop) / Stacked (Mobile)
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = PIL.Image.open(uploaded_file)
        st.image(image, use_container_width=True, caption="Label Preview")

    with col2:
        if st.button("🔍 Scan Ingredients"):
            with st.spinner('Agent is reading & thinking...'):
                try:
                    # The "Agent Loop" happens here
                    # 1. Vision: Reads text from image
                    # 2. Reasoning: Decides to call 'check_ingredients_tool'
                    # 3. Execution: Runs Python code
                    # 4. Response: Generates final answer
                    
                    prompt = """
                    Act as a strict Vegan Verification Agent.
                    1. Analyze the image and extract the INGREDIENTS list.
                    2. IGNORE "May contain traces" warnings.
                    3. Call the `check_ingredients_tool` with the list of ingredients found.
                    4. Based on the tool output:
                       - If NON-VEGAN items found: Start with "❌ NOT VEGAN". List the items and their animal source.
                       - If SAFE: Start with "✅ LIKELY VEGAN".
                       - If UNCERTAIN (e.g. "Natural Flavors"): Start with "⚠️ CAUTION".
                    5. Be concise.
                    """
                    
                    response = model.generate_content([prompt, image])
                    result_text = response.text
                    
                    # UI Logic based on Agent's verdict
                    if "NOT VEGAN" in result_text:
                        st.error(result_text, icon="❌")
                    elif "LIKELY VEGAN" in result_text:
                        st.success(result_text, icon="✅")
                    else:
                        st.warning(result_text, icon="⚠️")
                        
                    # Save to history
                    st.session_state.history.insert(0, f"{time.strftime('%H:%M')} - {result_text[:50]}...")
                    
                except Exception as e:
                    st.error(f"Agent Error: {str(e)}")

# --- 6. HISTORY DRAWER ---
if st.session_state.history:
    with st.expander("🕒 Recent Scans"):
        for item in st.session_state.history[:5]:
            st.text(item)
