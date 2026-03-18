import os
import json
from openai import OpenAI
from pydantic import BaseModel
import streamlit as st

def get_openai_client():
    """
    Returns an OpenAI client initialized with the API key.
    Reads from OPENAI_API_KEY environment variable. 
    If not found, checks Streamlit secrets.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try:
            if "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            pass
        
    if not api_key:
        st.error("Missing OPENAI_API_KEY. Please set the OPENAI_API_KEY environment variable or provide it in the UI.")
        st.stop()
        
    return OpenAI(api_key=api_key)

def generate_structured_response(system_prompt: str, user_prompt: str, response_model: type[BaseModel], model: str = "gpt-4o-mini"):
    """
    Helper function to call OpenAI and get a structured Pydantic response.
    """
    client = get_openai_client()
    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=response_model,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        st.error(f"Error calling LLM: {e}")
        return None

def generate_text_response(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini"):
    """
    Helper function to call OpenAI and get a raw string response.
    """
    client = get_openai_client()
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling LLM: {e}")
        return None
