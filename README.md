# CS7636 Phase 1: AI Storytelling

**Team Name:** Blueberry Gorilla
**Team Members:** Rugved Rajendra, Varun Chandrashekhar, Keshav Garg
**Template:** Suspense Generation
**System Name:** Detective's Dilemma Simulator

## System Overview
This project uses an AI "Meta-Controller" to dynamically direct a Large Language Model to write a Suspenseful Crime Mystery. Following our architecture, the system:
1. Generates a "Ground Truth" consisting of the real killer, motives, and timeline. 
2. Actively runs an investigation loop for a minimum of 15 plot points, injecting obstacles to ensure suspense while validating logic against the ground truth.
3. Translates the completed scene outcomes into a fluent mystery novel explicitly numbering the 15 plot points.

## How to Run the Code

We provided a user-friendly Streamlit web application to make viewing, inspecting, and demonstrating the system extremely easy.

### 1. Installation
Ensure you have Python 3.9+ installed and running. Open a terminal in this directory and install the requirements:
```bash
pip install -r requirements.txt
```

### 2. API Key Configuration
This system runs on OpenAI models (`gpt-4o-mini` and `gpt-4o`). You must provide an API key. You can do this in two ways:
**Method A (Preferred):** Export your key as an environment variable before running the script:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```
**Method B (UI Approach):** Run the application and paste your API key directly into the secure sidebar configuration panel that will appear on the left of the screen.

*(Note: If you are an instructor testing this repository, assume there are no hardcoded keys. You must provide your own using one of the methods above).*

### 3. Launching the App
Run the following command to start the application:
```bash
streamlit run app.py
```
This will open a browser window to `http://localhost:8501`. Click "Generate Mystery Novel 📖" to begin!

## Expected Run Time and Costs
- **Run Time:** Generating the ground truth, 15 individual investigation loops, and the final narrative takes approximately **60 to 90 seconds** to complete.
- **Cost:** The system primarily uses `gpt-4o-mini` for the loops and `gpt-4o` for the final narration. The estimated cost per full story generation is roughly **$0.02 - $0.05** depending on story length.

## Exemplar Stories
To review our successful runs showing the 15+ plot points, and the unsuccessful ("mis-spun") runs highlighting system limitations or hallucinated facts, please see the generated text files included in this repository:
- `exemplar_success.txt`: A full 15-plot point mystery novel complete with ground truth specs.
- `exemplar_fail.txt`: A failed demonstration where the AI hallucinates, breaks the 15-loop count, or solves the mystery without evidence.
