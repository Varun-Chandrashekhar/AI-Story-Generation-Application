# CS7634 Phase 1: AI Storytelling

**Team Name:** Blueberry Gorilla
**Team Members:** Rugved Rajendra, Varun Chandrashekhar, Keshav Garg
**Template:** Suspense Generation
**System Name:** Silverback Suspense Generation

## How to Test the System

### Method A: Live Deployment (Recommended)

You can directly test and interact with our system through our live Streamlit deployment:
**[https://blueberry-gorilla.streamlit.app/](https://blueberry-gorilla.streamlit.app/)**

Once on the deployed app, open the sidebar panel on the left to securely paste your OpenAI API Key, and then click "Generate Mystery Novel 📖" to begin.

---

### Method B: Running Locally

If you prefer to run the system on your own machine, follow these instructions:

#### 1. Installation

Ensure you have Python 3.9+ installed and running. Open a terminal in this directory and install the requirements:

```bash
pip install -r requirements.txt
```

#### 2. API Key Configuration

This system runs on OpenAI models (`gpt-4o-mini` and `gpt-4o`). To provide your API key, simply run the application and paste it directly into the secure sidebar panel on the left side of the screen.

#### 3. Launching the App

Run the following command to start the application:

```bash
streamlit run app.py
```

This will open a browser window to `http://localhost:8501`. Click "Generate Mystery Novel 📖" to begin!
