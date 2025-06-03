import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from io import BytesIO
import os

# --- Page Configuration ---
# This MUST be the very first Streamlit command
st.set_page_config(
    page_title="Insurance Plan Comparator",
    page_icon="⚖️",
    layout="wide"
)

# --- Sidebar ---
with st.sidebar:
    st.title("⚖️ About the Comparator")
    st.info(
        """
        This app uses Google's Gemini AI to compare health insurance plans. 
        Upload two or more brochures to see a side-by-side analysis of their key features.
        """
    )
    st.divider()
    st.header("How to Use")
    st.markdown(
        """
        1.  Ensure your **Google AI API Key** is set in the app's secrets.
        2.  **Upload two or more** insurance plan PDFs on the main page.
        3.  Click the **"Compare Plans"** button.
        4.  Review the comparison table and summary.
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
        # Return an error string instead of calling st.error directly
        return f"Error reading {uploaded_file.name}: {e}"

# --- The NEW Comparison Prompt ---
comparison_prompt = """
You are an expert AI Health Insurance Analyst specializing in comparative analysis. Your task is to meticulously analyze the text from two separate insurance policy brochures, which will be provided to you labeled as 'Plan 1' and 'Plan 2'.

Your goal is to create a single, comprehensive side-by-side comparison table.

**Instructions:**
1.  The table **must** have exactly three columns: 'Feature', 'Plan 1', and 'Plan 2'.
2.  For each feature listed below, find the corresponding information in the text for Plan 1 and Plan 2 and place it in the respective columns.
3.  If information for a specific feature is not found in a plan's text, you **must** state "Not Mentioned" in that cell. Do not leave it blank.
4.  After the table, add a new section under a heading `### Key Differences Summary`. In this section, write 3-4 bullet points summarizing the most important differences a customer should consider.

**Features to Compare:**

| Feature                      |
| :--------------------------- |
| Room Rent Limit              |
| Daycare Procedures           |
| Co-payment                   |
| Pre & Post-Hospitalization   |
| Restoration Benefit          |
| Lifelong Renewability        |
| No Claim Bonus (NCB)         |
| PED Waiting Period           |
| Consumable Cover             |
| Maternity Benefits           |

Please generate the Markdown table and the summary as requested.
"""


# --- Main App Interface ---
st.title("⚖️ Health Insurance Plan Comparator")
st.markdown("Upload two or more insurance brochures (PDF) to compare their features side-by-side.")

# Use accept_multiple_files=True to allow multiple uploads
uploaded_files = st.file_uploader("Choose PDF files...", type=["pdf"], accept_multiple_files=True)

# Only show the compare button if 2 or more files are uploaded
if uploaded_files and len(uploaded_files) >= 2:
    if st.button(f"Compare {len(uploaded_files)} Plans", type="primary"):
        with st.spinner(f"Reading and analyzing {len(uploaded_files)} brochures... This may take a moment. 🤔"):
            
            # --- Text Extraction and Prompt Creation ---
            plan_texts = []
            for i, file in enumerate(uploaded_files[:2]): # Limit to first 2 files for this version
                text = pdf_to_text(file)
                if "Error reading" in text:
                    st.error(text)
                    st.stop()
                plan_texts.append(f"--- PLAN {i+1} ({file.name}) TEXT START ---\n\n{text}\n\n--- PLAN {i+1} TEXT END ---")

            # Combine all parts into the final prompt
            final_prompt_for_ai = f"{comparison_prompt}\n\n{''.join(plan_texts)}"

            # --- AI Call and Display ---
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model.generate_content(final_prompt_for_ai)
                
                st.subheader("📊 Comparison Results")
                st.markdown(response.text)
                st.success("Comparison Complete!")
                st.balloons()

            except Exception as e:
                st.error(f"An error occurred while communicating with the AI: {e}")

elif uploaded_files and len(uploaded_files) < 2:
    st.warning("Please upload at least two PDF files to enable the comparison feature.")
