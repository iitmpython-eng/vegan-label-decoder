import streamlit as st

st.title("🕵️ Key Detective")

# Check if the secret exists
if "GOOGLE_API_KEY" in st.secrets:
    st.success("✅ SUCCESS: The app found the key in Secrets!")
    
    # Check if the key looks valid (simple check)
    key = st.secrets["GOOGLE_API_KEY"]
    if key.startswith("AIza"):
        st.write("Looks like a valid Google Key (starts with AIza).")
    else:
        st.error(f"⚠️ Key found, but it looks wrong. It starts with: '{key[:4]}...'")
        
else:
    st.error("❌ FAILURE: The app cannot find 'GOOGLE_API_KEY' in Secrets.")
    st.info("Check your spelling in the Secrets box. It must be GOOGLE_API_KEY")

st.write("---")
st.write("Once you see the ✅ SUCCESS message, paste your real Vegan App code back.")

