import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from io import BytesIO
import os
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Prism | AI Insurance Analyzer",
    page_icon="💎",
    layout="wide"
)

# --- Custom Font and Style ---
# We are embedding a modern font from Google Fonts and adding some minor style tweaks.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="st-"] {
  font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.title("💎 About Prism")
    st.info(
        """
        **Prism** is an AI-powered assistant designed to bring clarity to complex health insurance plans.
        """
    )
    st.divider()

    # --- Professional Sections using Expanders ---
    
    with st.expander("✍️ Provide Feedback"):
        st.markdown("Your feedback is crucial for improving Prism! Please share your thoughts, report bugs, or suggest new features.")
        # IMPORTANT: Make sure this placeholder is replaced with your actual Google Form link
        st.link_button("Go to Feedback Form", "YOUR_GOOGLE_FORM_LINK_HERE")

    with st.expander("📜 Disclaimer"):
        st.warning(
            """
            **For Informational Purposes Only.**
            The analysis provided by this AI is intended to be a helpful summary and should not be considered professional financial or legal advice. 
            The AI may make mistakes or misinterpret information. Always verify all details with the official policy document from the insurer before making any decisions.
            """
        )

    with st.expander("⚙️ How It Works"):
        st.markdown(
            """
            Prism uses a multi-step process to provide its analysis:
            1.  **Text Extraction:** It first reads and extracts all the readable text from the uploaded PDF brochure.
            2.  **Smart Prompting:** This text is then combined with a detailed set of instructions that tells the AI exactly what to look for.
            3.  **AI Analysis:** The complete package is sent to Google's Gemini model for analysis.
            4.  **Output Generation:** Finally, the AI generates the structured table and summary that you see in the results.
            """
        )
    
    st.divider()
    st.markdown("Created by **Udhayveer Singh**")
    st.markdown("[Connect on LinkedIn](https://www.linkedin.com/in/udhaysingh007)")


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

**Features to Extract:** Room Rent Limit, Co-payment, Pre & Post-Hospitalization, Daycare Procedures, Domiciliary Hospitalization, Organ Donor Expenses, Annual Health Check-ups, Restoration Benefit, No Claim Bonus (NCB), Consumable Cover, AYUSH Treatment Coverage, Maternity Benefits, PED Waiting Period, Major Exclusions (Summarize the top 3-5 key exclusions mentioned), Lifelong Renewability.
"""

comparison_prompt = """
You are an expert AI Health Insurance Analyst specializing in comparative analysis. Analyze the text from two brochures ('Plan 1' and 'Plan 2') and create a side-by-side comparison table with columns: 'Feature', 'Plan 1', 'Plan 2'. If info is missing, state "Not Mentioned". After the table, add a '### Key Differences Summary' with 3-4 bullet points.

**Features to Compare:** Room Rent LImit, Co-payment, Pre & Post-Hospitalization, Daycare Procedures, Domiciliary Hospitalization, Organ Donor Expenses, Annual Health Check-ups, Restoration Benefit, No Claim Bonus (NCB), Consumable Cover, AYUSH Treatment Coverage, Maternity Benefits, PED Waiting Period, Major Exclusions (Briefly list key exclusions for each plan), Lifelong Renewability.
"""


# --- Main App Interface ---
st.title("💎 Prism")
st.subheader("Your AI Health Insurance Assistant")
st.divider()

tab1, tab2 = st.tabs(["🔗 Analyze from Link", "📄 Analyze/Compare Uploaded PDFs"])

# --- TAB 1: ANALYZE FROM LINK ---
with tab1:
    with st.container(border=True):
        st.markdown("##### Analyze a single plan by providing a direct link to its PDF brochure.")
        pdf_url_input = st.text_input("Enter URL of a Single PDF Brochure", placeholder="https://.../policy_brochure.pdf", key="link_url")

        if st.button("Analyze from Link", type="primary", key="link_button"):
            if not pdf_url_input:
                st.warning("Please enter a URL.")
            else:
                # Using the new st.status for better feedback
                with st.status("Analyzing from link...", expanded=True) as status:
                    try:
                        st.write("📥 Downloading PDF from the web...")
                        response = requests.get(pdf_url_input, timeout=15)
                        response.raise_for_status()
                        
                        st.write("📚 Extracting text from the PDF...")
                        extracted_text = pdf_to_text(response.content, source_name="the provided URL")

                        if "Error reading" not in extracted_text:
                            st.write("🤖 Sending text to AI for analysis...")
                            final_prompt = f"{single_analysis_prompt}\n\n--- DOCUMENT TEXT ---\n\n{extracted_text}"
                            model = genai.GenerativeModel('models/gemini-1.5-flash')
                            ai_response = model.generate_content(final_prompt)
                            
                            status.update(label="Analysis Complete!", state="complete", expanded=False)
                            st.subheader("📊 Analysis from Link")
                            st.markdown(ai_response.text)
                        else:
                            status.update(label="Error", state="error")
                            st.error(extracted_text)
                    except requests.exceptions.RequestException as e:
                        status.update(label="Download Failed", state="error")
                        st.error(f"Failed to download or access the file from the URL: {e}")

# --- TAB 2: ANALYZE/COMPARE UPLOADED PDFs ---
with tab2:
    with st.container(border=True):
        st.markdown("##### Upload one PDF for a detailed analysis or two PDFs for a side-by-side comparison.")
        uploaded_files = st.file_uploader("Upload PDF brochures here", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed", key="upload_files")

        # Scenario 1: One file is uploaded
        if uploaded_files and len(uploaded_files) == 1:
            st.info("Ready for a single plan analysis.")
            if st.button("Analyze Single Plan", type="primary", key="analyze_single_button"):
                single_file = uploaded_files[0]
                with st.status(f"Analyzing {single_file.name}...", expanded=True) as status:
                    st.write("📚 Extracting text from the PDF...")
                    extracted_text = pdf_to_text(single_file.read(), source_name=single_file.name)
                    
                    if "Error reading" not in extracted_text:
                        st.write("🤖 Sending text to AI for analysis...")
                        final_prompt = f"{single_analysis_prompt}\n\n--- DOCUMENT TEXT ---\n\n{extracted_text}"
                        model = genai.GenerativeModel('models/gemini-1.5-flash')
                        response = model.generate_content(final_prompt)

                        status.update(label="Analysis Complete!", state="complete", expanded=False)
                        st.subheader(f"📊 Analysis for {single_file.name}")
                        st.markdown(response.text)
                    else:
                        status.update(label="Error", state="error")
                        st.error(extracted_text)

        # Scenario 2: Two or more files are uploaded
        elif uploaded_files and len(uploaded_files) >= 2:
            st.info(f"Ready to compare the first two uploaded plans.")
            if st.button(f"Compare Plans", type="primary", key="compare_button"):
                with st.status("Comparing plans...", expanded=True) as status:
                    plan_texts = []
                    for i, file in enumerate(uploaded_files[:2]):
                        st.write(f"📚 Reading {file.name}...")
                        text = pdf_to_text(file.read(), source_name=file.name)
                        if "Error reading" in text:
                            status.update(label="Error", state="error")
                            st.error(text); st.stop()
                        plan_texts.append(f"--- PLAN {i+1} ({file.name}) TEXT START ---\n\n{text}\n\n--- PLAN {i+1} TEXT END ---")
                    
                    st.write("🤖 Sending plans to AI for comparison...")
                    final_prompt_for_ai = f"{comparison_prompt}\n\n{''.join(plan_texts)}"
                    model = genai.GenerativeModel('models/gemini-1.5-flash')
                    response = model.generate_content(final_prompt_for_ai)
                    
                    status.update(label="Comparison Complete!", state="complete", expanded=False)
                    st.subheader("📊 Comparison Results")
                    st.markdown(response.text)
