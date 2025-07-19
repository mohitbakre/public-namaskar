# Part of your numerology_page.py or a separate utility function
import google.generativeai as genai
import streamlit as st

# Configure Gemini API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


def get_gemini_numerology_interpretation(life_path_number, user_name):
    model = genai.GenerativeModel('gemini-1.5-flash')  # Choose a suitable model

    prompt = f"As a highly experienced numerologist, provide a concise and inspiring interpretation for a person with Life Path Number {life_path_number}. Incorporate common traits and potential challenges associated with this number. Tailor the language to sound encouraging and insightful. For {user_name}."

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error getting interpretation: {e}"

# Then call this in your Numerology tab after calculation:
# ... inside the numerology_submit block
# llm_interpretation = get_gemini_numerology_interpretation(life_path_num, name)
# st.info(llm_interpretation)