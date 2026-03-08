import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build
from fpdf import FPDF

# --- 1. SECURE API LOADING ---
# Automatically loads keys from Streamlit Cloud Secrets
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# --- 2. PDF GENERATION CLASS ---
class ScriptedPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Ultra-Scripted Teacher Guide - 60 Min Plan', 0, 1, 'R')
        self.ln(5)
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(220, 230, 241)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)
        
    def add_script_body(self, content):
        self.set_font('Arial', '', 11)
        # We encode to latin-1 to prevent the standard FPDF library from crashing on special characters
        clean_text = content.encode('latin-1', 'ignore').decode('latin-1')
        self.multi_cell(0, 7, clean_text)
        self.ln()

# --- 3. YOUTUBE SEARCH LOGIC ---
def find_hindi_video(query, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            q=query + " educational lesson Hindi",
            part="snippet", 
            type="video", 
            relevanceLanguage="hi", 
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    except Exception as e:
        # Fails silently and safely if quota is reached or key is wrong
        pass
    return None

# --- 4. APP INTERFACE & SETUP ---
st.set_page_config(page_title="Ultra-Scripted Master Planner", layout="wide")
st.title("🎭 Scripted Lesson Master Engine")
st.markdown("### Minute-by-Minute Scripts | Mind Maps | Assessments")

# Fallback if Secrets are not configured
if not OPENAI_KEY or not YOUTUBE_KEY:
    with st.sidebar:
        st.warning("⚠️ API Keys missing from Secrets. Please enter below:")
        OPENAI_KEY = st.text_input("OpenAI API Key", type="password")
        YOUTUBE_KEY = st.text_input("YouTube API Key", type="password")

# --- 5. CORE LOGIC ---
uploaded_file = st.file_uploader("Upload Textbook (PDF)", type="pdf")

if uploaded_file:
    # Read PDF
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    st.info(f"📚 Total Book Pages: {total_pages} | Recommended Pacing: ~{round(total_pages/165, 1)} pages/day.")

    # Select Page Range
    c1, c2 = st.columns(2)
    start_p = c1.number_input("Start Page", 1, total_pages, 1)
    end_p = c2.number_input("End Page (Optional)", start_p, total_pages, start_p)

    if st.button("🚀 Generate Full Plan (with Mind Map & Assessment)"):
        if not OPENAI_KEY or not YOUTUBE_KEY:
            st.error("API Keys required to proceed.")
        else:
            with st.spinner("Drafting Script, Mind Map, and Assessment..."):
                
                # Extract text from selected pages
                text_context = ""
                for i in range(start_p - 1, end_p):
                    text_context += doc[i].get_text()
                
                client = OpenAI(api_key=OPENAI_KEY)
                
                # THE MASTER PROMPT
                prompt = f"""
                Create a MINUTE-BY-MINUTE scripted lesson plan (60 mins) in HINDI for Pages {start_p}-{end_p}.
                Write the EXACT DIALOGUE for the teacher. Do not use generic instructions.
                
                Structure:
                1. (0-5 min) THE HOOK: Exact Hindi rhyme/story to grab attention.
                2. (5-15 min) DISCOVERY: 5 exact Hindi questions the teacher must ask.
                3. (15-40 min) CORE SCRIPT: Break into 5-min blocks ('Teacher Says:' / 'Teacher Does:').
                4. (40-50 min) PLAY-BASED: A classroom game with explicit Hindi rules.
                5. (50-60 min) WRAP-UP & TLM: List specific local objects the teacher must bring/hold.
                6. PANCHADI MAPPING: Show how the lesson hits Adhiti, Bodha, Abhyasa, Prayoga, Prasar.
                7. MIND MAP / SUMMARY: Create a structured, text-based hierarchy (using bullets and arrows '->') summarizing the core concepts.
                8. ASSESSMENT: Create a short quiz (3 MCQs, 2 Short Answer, 1 Creative Task) with an Answer Key.
                
                Book Text: {text_context[:8000]}
                
                End with this exact tag format:
                SEARCH_QUERY: [Specific Topic in English]
                """

                # Call AI
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": prompt}]
                )
                
                full_output = response.choices[0].message.content
                
                # CRASH-PROOF LOGIC
                if "SEARCH_QUERY:" in full_output:
                    parts = full_output.split("SEARCH_QUERY:")
                    plan_content = parts[0].strip()
                    video_query = parts[1].strip()
                else:
                    plan_content = full_output
                    video_query = f"Topic page {start_p} lesson"

                # Fetch Video
                v_url = find_hindi_video(video_query, YOUTUBE_KEY)
                
                # --- 6. UI DISPLAY ---
                st.divider()
                col_plan, col_vid = st.columns([2, 1])
                
                with col_plan:
                    st.success("Lesson Script, Mind Map, and Assessment Ready!")
                    st.markdown(plan_content)
                    
                    # PDF Download Button
                    pdf = ScriptedPDF()
                    pdf.add_page()
                    pdf.chapter_title(f"Detailed Script: Pages {start_p}-{end_p}")
                    pdf.add_script_body(plan_content)
                    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
                    
                    st.download_button(
                        label="📥 Download Scripted PDF", 
                        data=pdf_bytes, 
                        file_name=f"Teacher_Script_P{start_p}.pdf"
                    )
                    
                    st.caption("💡 **Pro Tip for Hindi Fonts:** If the downloaded PDF shows weird characters instead of Hindi, skip the download button and press **Ctrl + P** (or Cmd + P on Mac) to print this web page directly as a PDF. It preserves all Hindi fonts perfectly!")

                with col_vid:
                    st.info("Classroom Video Aid")
                    if v_url:
                        st.video(v_url)
                        st.write(f"[Open on YouTube]({v_url})")
                    else:
                        st.warning("No matching Hindi educational video found.")
else:
    st.info("Waiting for textbook PDF upload...")
