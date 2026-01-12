import streamlit as st
import google.generativeai as genai
import PIL.Image

# --- 1. App Configuration ---
st.set_page_config(page_title="Vegan Label Decoder", page_icon="🌱")

st.title("🌱 Vegan Label Decoder")
st.write("Upload a photo of an ingredient label to check if it's vegan.")

# --- 2. API Key Setup (Smart Handling) ---
# Try to get the key from Streamlit Secrets (for the deployed app)
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback: Ask in sidebar if not in secrets
    api_key = st.sidebar.text_input("Enter Google API Key", type="password")

if not api_key:
    st.warning("Please add your Google API Key in Streamlit Secrets or the sidebar to continue.")
    st.stop()

# Configure Gemini
genai.configure(api_key=api_key)

# --- 3. The Knowledge Base (Tool) ---
ingredient_knowledge_base = {
    "casein": {"vegan": False, "source": "Milk protein"},
    "whey": {"vegan": False, "source": "Milk by-product"},
    "carmine": {"vegan": False, "source": "Crushed insects (E120)"},
    "gelatin": {"vegan": False, "source": "Animal collagen"},
    "honey": {"vegan": False, "source": "Bees"},
    "guar gum": {"vegan": True, "source": "Cluster bean"},
    "soy lecithin": {"vegan": True, "source": "Soybeans"},
    "lard": {"vegan": False, "source": "Pig fat"}
}

def check_ingredient_database(ingredients: list):
    """
    Look up a list of ingredients to determine if they are vegan.
    """
    results = []
    for item in ingredients:
        key = item.lower().strip()
        found = False
        # Simple partial match search
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

# --- 4. Initialize Model ---
tools_list = [check_ingredient_database]
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', 
    tools=tools_list
)

# --- 5. The UI Logic ---
uploaded_file = st.file_uploader("Choose a label image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the image
    image = PIL.Image.open(uploaded_file)
    st.image(image, caption='Uploaded Label', use_container_width=True)

    if st.button("🔍 Analyze Ingredients"):
        with st.spinner('Agent is reading the label...'):
            try:
                prompt = """
                You are an expert Vegan Decoder Agent.
                1. Analyze the image to identify the INGREDIENTS list text.
                2. Extract the specific ingredient names into a list.
                3. Use the `check_ingredient_database` tool to verify them.
                4. Final Output:
                   - If NON-VEGAN ingredients are found: Start with "❌ NOT VEGAN". List the specific culprits.
                   - If everything looks safe: Start with "✅ LIKELY VEGAN".
                   - If uncertain: Start with "⚠️ CAUTION".
                """
                
                response = model.generate_content([prompt, image])
                
                st.markdown("### Agent Verdict")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")