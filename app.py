import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from io import BytesIO
import os

# --- Page Configuration ---
# This MUST be the first Streamlit command in your script
st.set_page_config(
    page_title="Health Insurance Analyzer",
    page_icon="📄",
    layout="wide"
)

# --- Sidebar ---
# This section creates the sidebar with information and instructions
with st.sidebar:
    st.title("📄 About the Analyzer")
    st.info(
        """
        This app uses Google's Gemini AI to analyze health insurance brochures. 
        It extracts key features and presents them in a clear, easy-to-read table.
        """
    )
    st.divider()
    st.header("How to Use")
    st.markdown(
        """
        1.  Make sure you have added your **Google AI API Key** in the app's settings.
        2.  **Upload a PDF** of the insurance plan on the main page.
        3.  Click the **"Analyze This Brochure"** button.
        4.  Review the **Analysis Results** table.
        """
    )
    st.warning("The analysis is AI-generated and for informational purposes only. Always verify details with the official policy document.")


# --- AI and API Configuration ---
# Fetch API key from Streamlit secrets and configure the AI model
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
def pdf_to_text(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    try:
        file_bytes = BytesIO(uploaded_file.read())
        reader = pdf.PdfReader(file_bytes)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# --- The Master Prompt ---
master_prompt = """
You are an expert AI Health Insurance Analyst. Your task is to meticulously analyze the provided text from a health insurance brochure. Your goal is to extract specific, vital information about the plan's features, benefits, and limitations.

After your analysis, you must present the extracted information **only in a Markdown table format**. Do not add any introductory or concluding text outside of the table.

The table must have the following columns:
* **Feature**
* **Status (Yes/No)**
* **Details & Conditions**

If you cannot find specific information for a feature within the provided text, you must state **"Not Mentioned in Brochure"** in the "Details & Conditions" column.

Here are the features you must extract:

| Feature | Extraction Instructions |
| :--- | :--- |
| **Room Rent Limit** | Determine if a limit exists. If **Yes**, specify the exact limit (e.g., "Single Private AC Room", "Up to ₹8,000/day", "1% of Sum Insured"). If **No**, state "No Limit". |
| **Daycare Procedures** | Determine if all daycare procedures are covered. If **Yes**, state "All procedures covered". If only specific procedures are covered, list them. If **No**, confirm that they are not covered. |
| **Co-payment** | Determine if a co-payment clause exists. If **Yes**, specify the percentage and the conditions under which it applies (e.g., "10% on all claims", "20% for senior citizens"). If **No**, state "No Co-payment". |
| **Pre & Post-Hospitalization** | Determine if pre and post-hospitalization expenses are covered. If **Yes**, specify the number of days covered for both (e.g., "60 days pre-hospitalization, 180 days post-hospitalization"). |
| **Restoration Benefit** | Determine if the Restoration Benefit is available. If **Yes**, specify the limit and conditions (e.g., "100% of Sum Insured, for unrelated illnesses", "Unlimited restoration"). If **No**, confirm it's not available. |
| **Lifelong Renewability** | Determine if the policy offers lifelong renewability. This is almost always **Yes**, but you must confirm it from the brochure. |
| **No Claim Bonus (NCB)** | Determine if a No Claim Bonus is offered. If **Yes**, specify the percentage of increase per claim-free year and the maximum accumulation limit (e.g., "50% per year, up to a max of 200% of Sum Insured"). If **No**, confirm it's not available. |
| **Cashless Hospital Network**| Determine if a cashless hospital network is available. This is almost always **Yes**, but you must confirm it from the brochure. |
| **PED Waiting Period** | Find the waiting period for Pre-Existing Diseases (PED). Specify the duration clearly (e.g., "48 months", "3 years"). Classify it as **Low** (2 years or less) or **High** (more than 2 years). |
| **Consumable Cover** | Determine if non-payable items or consumables are covered (e.g., gloves, syringes). If **Yes**, state if it's an inbuilt feature or an optional add-on, and mention any limits. If **No**, confirm it's not covered. |
| **Maternity Benefits** | Determine if maternity benefits are included. If **Yes**, specify the waiting period and the coverage limit (e.g., "Waiting period of 24 months, up to ₹50,000 for normal delivery"). If **No**, confirm it's not covered. |
"""


# --- Main App Interface ---
st.title("🩺 Health Insurance Plan Analyzer")
st.markdown("Upload a health insurance brochure (PDF) and the AI will extract the key features for you.")

uploaded_file = st.file_uploader("Choose a PDF file...", type=["pdf"], label_visibility="collapsed")

if uploaded_file:
    if st.button("Analyze This Brochure", type="primary"):
        with st.spinner("Reading the brochure and thinking... This may take a moment. 🤔"):
            extracted_text = pdf_to_text(uploaded_file)

            if extracted_text:
                st.info("PDF processed successfully. Now sending to the AI for analysis...")

                final_prompt = f"""
                {master_prompt}
                ---
                Here is the text from the insurance brochure PDF. Please analyze it based on the instructions I provided above:
                ---
                {extracted_text}
                """
                try:
                    model = genai.GenerativeModel('models/gemini-1.5-flash')
                    response = model.generate_content(final_prompt)
                    
                    st.subheader("📊 Analysis Results:")
                    st.markdown(response.text)
                    st.success("Analysis Complete!")
                    st.balloons() # The celebration animation!
                except Exception as e:
                    st.error(f"An error occurred while communicating with the AI: {e}")
            else:
                st.error("Could not extract text from the PDF. The file might be corrupted or image-based.")
