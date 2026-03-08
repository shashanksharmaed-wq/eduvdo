import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build
from fpdf import FPDF

# --- PDF Generation Class ---
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
        # Replacing non-latin characters for PDF compatibility (Latin-1)
        # Note: For full Hindi PDF support, custom Unicode fonts are needed.
        self.multi_cell(0, 7, content.encode('latin-1', 'ignore').decode('latin-1'))
        self.ln()

# --- Functions ---
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

# --- UI Setup ---
st.set_page_config(page_title="Pro Pedagogy Planner", layout="wide")
st.title("🏫 Professional Lesson Planner (5E + Panchadi)")
st.markdown("### Focus: 165 Days | 45-60 Mins | Play-Based & TLM")

with st.sidebar:
    st.header("🔑 API Credentials")
    openai_key = st.text_input("OpenAI API Key", type="password")
    youtube_key = st.text_input("YouTube API Key", type="password")
    st.divider()
    st.info("This tool aligns lessons with NCF guidelines and international pedagogical standards.")

# --- File Processing ---
uploaded_file = st.file_uploader("Upload Textbook (PDF)", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    # Pacing Logic
    target_days = 165
    pages_per_day = round(total_pages / target_days, 1)
    
    st.sidebar.success(f"Pacing: Cover ~{pages_per_day} pages/day to finish in {target_days} days.")

    # Selection
    c1, c2 = st.columns(2)
    start_p = c1.number_input("Start Page", 1, total_pages, 1)
    end_p = c2.number_input("End Page", 1, total_pages, min(start_p + 2, total_pages))

    if st.button("Generate Professional Lesson Plan"):
        if not openai_key or not youtube_key:
            st.error("Please provide both API Keys.")
        else:
            with st.spinner("Analyzing text and applying pedagogical frameworks..."):
                # Extract Text
                context_text = ""
                for i in range(start_p - 1, end_p):
                    context_text += doc[i].get_text()

                client = OpenAI(api_key=openai_key)
                
                # High-Depth Prompt
                prompt = f"""
                Create a high-depth 45-60 minute lesson plan in HINDI for Pages {start_p}-{end_p}.
                Strictly follow this structure:
                1. Learning Objectives: Use Bloom's Taxonomy (Analyze, Evaluate, Create).
                2. 5E Model: Engage (Hook), Explore, Explain, Elaborate, Evaluate.
                3. Panchadi Framework: Adhiti, Bodha, Abhyasa, Prayoga, Prasar.
                4. Play-Based Activity: 1 specific classroom game related to the topic.
                5. TLM (Teaching Learning Materials): List specific items needed.
                6. Assessment: 3 questions to check understanding.
                
                Content: {context_text[:8000]}
                
                Format the end as: SEARCH_QUERY: [Specific Topic in English]
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": prompt}]
                )
                
                full_output = response.choices[0].message.content
                plan_text, search_query = full_output.split("SEARCH_QUERY:")
                
                # Fetch Video
                video_link = find_youtube_video(search_query.strip(), youtube_key)

                # --- Results Display ---
                res_col, vid_col = st.columns([2, 1])
                
                with res_col:
                    st.subheader("📝 Deep Lesson Plan")
                    st.markdown(plan_text)
                    
                    # PDF Download Feature
                    pdf = LessonPDF()
                    pdf.add_page()
                    pdf.chapter_title(f"Lesson Plan: Page {start_p} to {end_p}")
                    pdf.add_content(plan_text)
                    pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
                    
                    st.download_button(
                        label="📥 Download Plan as PDF",
                        data=pdf_output,
                        file_name=f"Lesson_Plan_P{start_p}.pdf",
                        mime="application/pdf"
                    )

                with vid_col:
                    st.subheader("🎥 Visual Aid")
                    if video_link:
                        st.video(video_link)
                    else:
                        st.warning("No relevant Hindi video found.")
