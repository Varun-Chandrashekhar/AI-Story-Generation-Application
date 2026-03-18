import streamlit as st
import os

# Page config must be first
st.set_page_config(page_title="Suspense Generation - CS7634", layout="wide", page_icon="🕵️‍♂️")

# Custom CSS for modern design and typography (from web_application_development rules)
st.title("Blueberry Gorilla Suspense Generator")
st.subheader("AI Storytelling Phase 1 • CS7634")

# API Key Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    user_api_key = st.text_input("OpenAI API Key (Optional if set in Env)", type="password")
    if user_api_key:
        os.environ["OPENAI_API_KEY"] = user_api_key
        st.success("API Key loaded into environment.")
        
    st.markdown("---")
    st.markdown("### Architecture Components")
    st.markdown("- **Crime Creator:** Synthesizes Ground Truth.")
    st.markdown("- **Investigation Generator:** Creates raw scene outcomes.")
    st.markdown("- **State Tracker:** Checks consistency of clues across loops.")
    st.markdown("- **Meta-Controller:** Enforces 15+ plot point loop.")
    st.markdown("- **Narrator:** Translates scenes into fluent prose.")

from system.meta_controller import run_meta_controller

tab1, tab2 = st.tabs(["📝 Generate Novel", "🔍 View Hidden Story DB"])

with tab1:
    st.write("Click the button below to initialize the **Meta-Controller** and begin generating the mystery. The system will first establish the ground truth (Crime Story) and then iteratively build the investigation scenes (Solving Story), ensuring suspense is added at each of the 15+ plot points.")
    
    if st.button("Generate Mystery Novel 📖"):
        with st.spinner("Meta-Controller is directing the story components..."):
            ground_truth, final_story = run_meta_controller(yield_updates=True)
            
            if ground_truth and final_story:
                st.session_state["ground_truth"] = ground_truth.model_dump_json(indent=2)
                st.success("Generation Complete!")
                
                st.markdown("### The Final Novel")
                st.write(final_story)

with tab2:
    if "ground_truth" in st.session_state:
        st.write("Behind the scenes, the **Crime Creator** generated these constraints. The **Meta-Controller** ensured the **Investigation Generator** adhered to them.")
        st.code(st.session_state["ground_truth"], language="json")
    else:
        st.info("The Hidden Story DB will be populated here after you generate a novel.")
