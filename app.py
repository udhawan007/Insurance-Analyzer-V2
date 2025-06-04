import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from io import BytesIO
import os
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Prism | AI Insurance Comparator",
    page_icon="💎",
    layout="wide"
)

# --- Sidebar ---
with st.sidebar:
    st.title("💎 About Prism")
    st.info(
        """
        **Prism** is an AI-powered assistant designed to bring clarity to complex health insurance plans. 
        
        It can analyze a single plan from a web link or compare uploaded brochures side-by-side.
        """
    )
    st.divider()
    st.header("ℹ️ How to Use")
    st.markdown(
        """
        1.  Choose your method: **Analyze from Link** or **Compare Uploads**.
        2.  Provide the URL or PDF files.
        3.  Click the corresponding button to start the analysis.
        """
    )
    st.warning("The AI analysis is for informational purposes only. Always verify details with the official policy documents.")


# --- AI and API Configuration ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("🔴 **Error:** `GOOGLE_API_KEY` not found. Please go to 'Manage app' -> 'Secrets' and add your key.")
    st.stop()
except Exception as e:
    st.error(f"🔴 **Error configuring the AI model:** {e}")
    st.stop()


# --- Helper Function to Extract Text from PDF ---
def pdf_to_text(file_bytes, source_name="file"):
    """Extracts text from PDF bytes."""
    try:
        pdf_file = BytesIO(file_bytes)
        reader = pdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF from {source_name}: {e}"

# --- Prompts ---
single_analysis_prompt = """
You are an expert AI Health Insurance Analyst. Your task is to meticulously analyze the provided text from a health insurance brochure and extract specific, vital information.

Present the extracted information **only in a Markdown table format** with two columns: 'Feature' and 'Details & Conditions'. If information for a feature is not found, state "Not Mentioned".

**Features to Extract:** Room Rent Limit, Daycare Procedures, Co-payment, Pre & Post-Hospitalization, Restoration Benefit, Lifelong Renewability, No Claim Bonus (NCB), PED Waiting Period, Consumable Cover, Maternity Benefits.
"""

comparison_prompt = """
You are an expert AI Health Insurance Analyst specializing in comparative analysis. Analyze the text from two brochures ('Plan 1' and 'Plan 2') and create a side-by-side comparison table with columns: 'Feature', 'Plan 1', 'Plan 2'. If info is missing, state "Not Mentioned". After the table, add a '### Key Differences Summary' with 3-4 bullet points.

**Features to Compare:** Room Rent Limit, Daycare Procedures, Co-payment, Pre & Post-Hospitalization, Restoration Benefit, Lifelong Renewability, No Claim Bonus (NCB), PED Waiting Period, Consumable Cover, Maternity Benefits.
"""


# --- Main App Interface ---
st.title("💎 Prism")
st.subheader("Your AI Health Insurance Assistant")
st.divider()

tab1, tab2 = st.tabs(["🔗 Analyze from Link", "📄 Compare Uploaded PDFs"])

# --- TAB 1: ANALYZE FROM LINK ---
with tab1:
    st.markdown("##### Analyze a single plan by providing a direct link to its PDF brochure.")
    pdf_url_input = st.text_input("Enter URL of a Single PDF Brochure", placeholder="https://.../policy_brochure.pdf", key="link_url")

    if st.button("Analyze from Link", type="primary", key="link_button"):
        if not pdf_url_input:
            st.warning("Please enter a URL.")
        else:
            with st.spinner("Downloading and analyzing the plan from the link..."):
                try:
                    response = requests.get(pdf_url_input, timeout=10)
                    response.raise_for_status()
                    extracted_text = pdf_to_text(response.content, source_name="the provided URL")

                    if "Error reading" not in extracted_text:
                        final_prompt = f"{single_analysis_prompt}\n\n--- DOCUMENT TEXT ---\n\n{extracted_text}"
                        model = genai.GenerativeModel('models/gemini-1.5-flash')
                        ai_response = model.generate_content(final_prompt)
                        st.subheader("📊 Analysis from Link")
                        st.markdown(ai_response.text)
                        st.balloons()
                    else:
                        st.error(extracted_text)
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to download or access the file from the URL: {e}")

# --- TAB 2: COMPARE UPLOADED PDFs ---
with tab2:
    st.markdown("##### Compare plans by uploading their brochures.")
    uploaded_files = st.file_uploader("Upload two or more PDF brochures here", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed", key="upload_files")

    if uploaded_files and len(uploaded_files) >= 2:
        if st.button(f"Compare {len(uploaded_files)} Uploaded Plans", type="primary", key="compare_button"):
            plan_texts = []
            for i, file in enumerate(uploaded_files[:2]):
                with st.spinner(f"Reading {file.name}..."):
                    text = pdf_to_text(file.read(), source_name=file.name)
                    if "Error reading" in text:
                        st.error(text); st.stop()
                    plan_texts.append(f"--- PLAN {i+1} ({file.name}) TEXT START ---\n\n{text}\n\n--- PLAN {i+1} TEXT END ---")
            
            with st.spinner("AI is analyzing the plans..."):
                final_prompt_for_ai = f"{comparison_prompt}\n\n{''.join(plan_texts)}"
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model.generate_content(final_prompt_for_ai)
                st.subheader("📊 Comparison Results")
                st.markdown(response.text)
                st.success("Comparison Complete!")
                st.balloons()

    elif uploaded_files and len(uploaded_files) < 2:
        st.warning("⚠️ Please upload at least two PDF files to compare.")
