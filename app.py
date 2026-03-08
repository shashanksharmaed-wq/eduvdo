import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build
from fpdf import FPDF

# --- 1. SECURE API LOADING ---
# If you put these in Streamlit Cloud > Settings > Secrets, 
# you will NEVER have to type them again.
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# --- 2. PDF GENERATION LOGIC ---
class LessonPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'School Lesson Plan: 5E & Panchadi Model', 0, 1, 'C')
        self.ln(5)
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)
    def add_content(self, content):
        self.set_font('Arial', '', 11)
        # We use 'ignore' to prevent crashes on special characters
        clean_text = content.encode('latin-1', 'ignore').decode('latin-1')
        self.multi_cell(0, 7, clean_text)
        self.ln()

# --- 3. YOUTUBE SEARCH LOGIC ---
def find_youtube_video(query, api_key):
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
st.set_page_config(page_title="Pro Pedagogy Planner", layout="wide")
st.title("🏫 Professional Hindi Lesson Planner")
st.markdown("### 5E Model | Panchadi Framework | 165-Day Pacing")

# Sidebar Fallback for Manual Entry
if not OPENAI_KEY or not YOUTUBE_KEY:
    with st.sidebar:
        st.warning("API Keys not found in Secrets. Enter them below:")
        OPENAI_KEY = st.text_input("OpenAI API Key", type="password")
        YOUTUBE_KEY = st.text_input("YouTube API Key", type="password")

# File Upload
uploaded_file = st.file_uploader("Upload Textbook (PDF)", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    # Automatic Pacing Calculation
    pages_per_day = round(total_pages / 165, 1)
    st.info(f"📚 Total Pages: {total_pages} | Recommended Pacing: ~{pages_per_day} pages per day.")

    c1, c2 = st.columns(2)
    start_p = c1.number_input("Start Page", 1, total_pages, 1)
    end_p = c2.number_input("End Page", 1, total_pages, min(start_p + 2, total_pages))

    if st.button("Generate Deep Lesson Plan"):
        if not OPENAI_KEY or not YOUTUBE_KEY:
            st.error("Missing API Keys! Please check Secrets or Sidebar.")
        else:
            with st.spinner("Analyzing content and building pedagogical plan..."):
                # Extracting Text from PDF
                context_text = ""
                for i in range(start_p - 1, end_p):
                    context_text += doc[i].get_text()

                client = OpenAI(api_key=OPENAI_KEY)
                
                # High-Depth Pedagogy Prompt
                prompt = f"""
                Create a 60-minute in-depth lesson plan in HINDI for: Pages {start_p}-{end_p}.
                Follow this structure exactly:
                1. Learning Objectives (Bloom's Taxonomy)
                2. 5E Model: Engage, Explore, Explain, Elaborate, Evaluate.
                3. Panchadi: Adhiti, Bodha, Abhyasa, Prayoga, Prasar.
                4. TLM (Teaching Learning Materials) & Play-based Activity.
                5. Assessment Questions.
                
                Text Content: {context_text[:8000]}
                
                End the response with this tag: SEARCH_QUERY: [Specific Topic in English]
                """

                # AI Generation
                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": prompt}]
                )
                
                full_output = response.choices[0].message.content
                
                # --- NANO-CHECK: Error Prevention for the "Split" issue ---
                if "SEARCH_QUERY:" in full_output:
                    parts = full_output.split("SEARCH_QUERY:")
                    plan_text = parts[0].strip()
                    search_query = parts[1].strip()
                else:
                    plan_text = full_output
                    search_query = f"Education topic page {start_p}" # Safe Fallback

                # Get Video
                video_link = find_youtube_video(search_query, YOUTUBE_KEY)

                # --- 5. RESULTS DISPLAY ---
                res_col, vid_col = st.columns([2, 1])
                
                with res_col:
                    st.subheader("📝 Pedagogy Plan")
                    st.markdown(plan_text)
                    
                    # PDF Download
                    pdf = LessonPDF()
                    pdf.add_page()
                    pdf.chapter_title(f"Lesson Plan: Pages {start_p} to {end_p}")
                    pdf.add_content(plan_text)
                    pdf_data = pdf.output(dest='S').encode('latin-1', 'ignore')
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_data,
                        file_name=f"Lesson_P{start_p}.pdf",
                        mime="application/pdf"
                    )

                with vid_col:
                    st.subheader("🎥 Hindi Video Resource")
                    if video_link:
                        st.video(video_link)
                    else:
                        st.warning("No matching Hindi educational video found.")
