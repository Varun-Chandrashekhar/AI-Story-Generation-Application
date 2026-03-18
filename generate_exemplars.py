import sys
import os
from system.meta_controller import run_meta_controller

def generate_stories():
    # 1. Successful Story
    print("Generating Successful Story...")
    os.environ["ST_MODE"] = "headless" # fake for llm_utils
    
    # We need to ensure we can run it without streamlit breaking if we just call the functions directly. 
    # Let me bypass the UI elements in meta_controller by adding a simple mock.
    
    gt, final = run_meta_controller(yield_updates=False)
    with open("exemplar_success.txt", "w") as f:
        if gt:
            f.write("=== GROUND TRUTH ===\n" + gt.model_dump_json(indent=2) + "\n\n")
        f.write("=== NOVEL ===\n" + final)
        
    print("Saved to exemplar_success.txt")
    
if __name__ == "__main__":
    generate_stories()
