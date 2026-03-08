import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build
from fpdf import FPDF

# --- 1. SECURE API LOADING (FROM SECRETS) ---
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
        clean_text = content.encode('latin-1', 'ignore').decode('latin-1')
        self.multi_cell(0, 7, clean_text)
        self.ln()

# --- 3. YOUTUBE SEARCH LOGIC ---
def find_hindi_video(query, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            q=query + " educational lesson Hindi",
            part="snippet", type="video", relevanceLanguage="hi", maxResults=1
        )
        response = request.execute()
        if response['items']:
            return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    except:
        return None
    return None

# --- 4. APP INTERFACE ---
st.set_page_config(page_title="Ultra-Scripted Master Planner", layout="wide")
st.title("🎭 Scripted Lesson Master Engine")
st.markdown("### Exceeding Chrysalis & Edaic Standards with Minute-by-Minute Scripts")

# Sidebar for fallback if Secrets are empty
if not OPENAI_KEY or not YOUTUBE_KEY:
    with st.sidebar:
        st.warning("⚠️ API Keys missing from Secrets. Please enter below:")
        OPENAI_KEY = st.text_input("OpenAI API Key", type="password")
        YOUTUBE_KEY = st.text_input("YouTube API Key", type="password")

uploaded_file = st.file_uploader("Upload Textbook (PDF)", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    st.info(f"📚 Total Book Pages: {total_pages} | Recommended Pacing: ~{round(total_pages/165, 1)} pages/day.")

    c1, c2 = st.columns(2)
    p_num = c1.number_input("Select Page for Today's Script", 1, total_pages, 1)

    if st.button("🚀 Generate Ultra-Detailed Scripted Plan"):
        if not OPENAI_KEY or not YOUTUBE_KEY:
            st.error("API Keys required to proceed.")
        else:
            with st.spinner("Drafting Teacher Dialogues, Rhymes, and Minute-by-Minute Actions..."):
                # Extracting context
                text_context = doc[p_num-1].get_text()
                
                client = OpenAI(api_key=OPENAI_KEY)
                
                # SCRIPTED MASTER PROMPT
                prompt = f"""
                Create a MINUTE-BY-MINUTE scripted lesson plan (60 mins) in HINDI for Page {p_num}.
                Avoid generic labels like 'Explain' or 'Recite'. Write the EXACT DIALOGUE.
                
                Structure:
                1. (0-5 min) THE HOOK: Write the exact 4-8 line Hindi rhyme or story. 
                2. (5-15 min) DISCOVERY: List 5 exact Hindi questions the teacher should ask students.
                3. (15-40 min) CORE SCRIPT: Break into 5-min blocks. For each, write 'Teacher Says' and 'Teacher Does'.
                4. (40-50 min) PLAY-BASED: A specific classroom game with full Hindi rules.
                5. (50-60 min) WRAP-UP & TLM: List specific local objects the teacher must hold.
                6. PANCHADI MAPPING: Show how this fits Adhiti, Bodha, Abhyasa, Prayoga, Prasar.
                
                Book Text: {text_context[:8000]}
                End with tag: SEARCH_QUERY: [Specific Topic in English]
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": prompt}]
                )
                
                full_output = response.choices[0].message.content
                
                # CRASH-PROOF LOGIC (The "Split" Fix)
                if "SEARCH_QUERY:" in full_output:
                    parts = full_output.split("SEARCH_QUERY:")
                    plan_content = parts[0].strip()
                    video_query = parts[1].strip()
                else:
                    plan_content = full_output
                    video_query = f"Topic page {p_num} lesson"

                # Video & PDF Output
                v_url = find_hindi_video(video_query, YOUTUBE_KEY)
                
                # Display Results
                st.divider()
                col_plan, col_vid = st.columns([2, 1])
                
                with col_plan:
                    st.success("Lesson Script Ready!")
                    st.markdown(plan_content)
                    
                    pdf = ScriptedPDF()
                    pdf.add_page()
                    pdf.chapter_title(f"Detailed Script: Page {p_num}")
                    pdf.add_script_body(plan_content)
                    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
                    st.download_button("📥 Download Scripted PDF", pdf_bytes, f"Teacher_Script_P{p_num}.pdf")

                with col_vid:
                    st.info("Classroom Video Aid")
                    if v_url:
                        st.video(v_url)
                    else:
                        st.write("No matching video found.")
