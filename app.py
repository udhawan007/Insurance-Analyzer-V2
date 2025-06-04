import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from io import BytesIO
import os
import requests
from googleapiclient.discovery import build

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
        
        It can search for policies online, analyze a single plan from a web link, or compare uploaded brochures side-by-side.
        """
    )
    st.divider()
    st.header("ℹ️ How to Use")
    st.markdown(
        """
        1.  Choose your method: **Search**, **Analyze from Link**, or **Compare Uploads**.
        2.  Provide the plan name, URL, or PDF files.
        3.  Click the corresponding button to start the analysis.
        """
    )
    st.warning("The AI analysis is for informational purposes only. Always verify details with the official policy documents.")


# --- AI and API Configuration ---
try:
    GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SEARCH_API_KEY = st.secrets["GOOGLE_API_KEY"] # Using the same key
    SEARCH_ENGINE_ID = st.secrets["SEARCH_ENGINE_ID"]
    genai.configure(api_key=GEMINI_API_KEY)
except KeyError as e:
    st.error(f"🔴 **Error:** Secret key '{e.args[0]}' not found. Please add it to your Streamlit Secrets.")
    st.stop()

# --- Helper Functions ---
def pdf_to_text(file_bytes, source_name="file"):
    try:
        pdf_file = BytesIO(file_bytes)
        reader = pdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF from {source_name}: {e}"

def find_brochure_online(plan_name):
    """Uses Google Search API to find a PDF brochure, checking top results."""
    try:
        service = build("customsearch", "v1", developerKey=SEARCH_API_KEY)
        query = f"{plan_name} health insurance brochure filetype:pdf"
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=3).execute()
        
        if 'items' in res and len(res['items']) > 0:
            for item in res['items']:
                pdf_url = item.get('link')
                if pdf_url and pdf_url.lower().endswith('.pdf'):
                    try:
                        head_response = requests.head(pdf_url, timeout=5)
                        if head_response.status_code == 200 and 'application/pdf' in head_response.headers.get('Content-Type',''):
                            return pdf_url
                    except requests.exceptions.RequestException:
                        continue
            return "Found search results, but no direct PDF link among the top ones."
        else:
            return None
    except Exception as e:
        return f"Error during search: {e}"

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

tab1, tab2, tab3 = st.tabs(["🔍 Search & Analyze", "🔗 Analyze from Link", "📄 Compare Uploaded PDFs"])

# --- TAB 1: SEARCH & ANALYZE ---
with tab1:
    st.markdown("##### Enter the name of a health insurance plan to find and analyze it.")
    plan_name_input = st.text_input("Enter Plan Name", placeholder="e.g., Star Health Comprehensive Plan", key="search_plan_name")

    if st.button("Find & Analyze Plan", type="primary", key="search_button"):
        if not plan_name_input:
            st.warning("Please enter a plan name.")
        else:
            with st.spinner(f"Searching for '{plan_name_input}' brochure online..."):
                pdf_url = find_brochure_online(plan_name_input)
            
            if pdf_url and "Error" not in pdf_url and "Found search results" not in pdf_url:
                st.success(f"Found brochure: {pdf_url}")
                with st.spinner("Downloading and analyzing the plan..."):
                    try:
                        response = requests.get(pdf_url, timeout=10)
                        response.raise_for_status()
                        extracted_text = pdf_to_text(response.content, source_name=plan_name_input)

                        if "Error reading" not in extracted_text:
                            final_prompt = f"{single_analysis_prompt}\n\n--- DOCUMENT TEXT ---\n\n{extracted_text}"
                            model = genai.GenerativeModel('models/gemini-1.5-flash')
                            ai_response = model.generate_content(final_prompt)
                            st.subheader(f"📊 Analysis for {plan_name_input}")
                            st.markdown(ai_response.text)
                            st.balloons()
                        else:
                            st.error(extracted_text)
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to download file from URL: {e}")
            else:
                st.error(f"Could not find a suitable PDF brochure for '{plan_name_input}'. Please try a more specific name or use another method.")

# --- TAB 2: ANALYZE FROM LINK (The New Feature) ---
with tab2:
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


# --- TAB 3: COMPARE UPLOADED PDFs ---
with tab3:
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
