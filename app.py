import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Health Insurance Analyzer",
    page_icon="📄",
    layout="wide"
)

# --- Main App Logic ---
# Fetch API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("🔴 Error: GOOGLE_API_KEY not found. Please add it to your Streamlit Secrets.")
    st.stop()
except Exception as e:
    st.error(f"🔴 Error configuring the AI model: {e}")
    st.stop()

# --- Helper Functions ---
def get_gemini_response(pdf_content, prompt):
    """Generates a response from the Gemini model."""
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    response = model.generate_content([pdf_content, prompt])
    return response.text

def pdf_to_text(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    try:
        # Use BytesIO to handle the uploaded file in memory
        file_bytes = BytesIO(uploaded_file.read())
        reader = pdf.PdfReader(file_bytes)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# --- The Master Prompt ---
master_prompt = """
You are an expert AI Health Insurance Analyst...
[NOTE: The rest of your detailed prompt goes here. For brevity, I've truncated it, but you should paste your full prompt.]
"""

# --- Streamlit App Interface ---
st.title("📄 Health Insurance Plan Analyzer")
st.markdown("Upload a health insurance brochure (PDF) and the AI will extract the key features for you.")

uploaded_file = st.file_uploader("Choose a PDF file...", type=["pdf"])

if uploaded_file:
    if st.button("Analyze This Brochure"):
        with st.spinner("Reading the brochure and thinking... 🤔"):
            extracted_text = pdf_to_text(uploaded_file)
            if extracted_text:
                st.info("PDF processed. Now generating analysis...")
                response = get_gemini_response(
                    pdf_content=extracted_text,
                    prompt=master_prompt
                )
                st.subheader("Analysis Results:")
                st.markdown(response)
            else:
                st.error("Could not extract text from the PDF. The file might be corrupted, empty, or an image-based PDF.")
