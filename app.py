import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build

# --- Page Configuration ---
st.set_page_config(page_title="Hindi AI School Planner", layout="wide")
st.title("📚 AI Lesson Planner (हिंदी)")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("🔑 API Setup")
    openai_key = st.text_input("OpenAI API Key", type="password")
    youtube_key = st.text_input("YouTube API Key", type="password")
    st.divider()
    
    st.header("⚙️ Plan Settings")
    # Control the length/detail of the lesson plan
    detail_level = st.select_slider(
        "Select Detail Level (विस्तार स्तर):",
        options=["Brief", "Standard", "Comprehensive"],
        value="Standard"
    )
    
    length_map = {
        "Brief": "Keep it short (max 200 words). Focus on 3 main points only.",
        "Standard": "Provide a balanced 1-page plan with summary and activity.",
        "Comprehensive": "Detailed 3-page style plan with minute-by-minute breakdown and 5 quiz questions."
    }

# --- Core Functions ---
def get_pdf_structure(pdf_file):
    """Detects Chapters or provides a way to read pages."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    toc = doc.get_toc() # Table of Contents
    if toc:
        chapters = [{"title": f"Ch {lvl}: {t}", "page": p - 1} for lvl, t, p in toc if lvl <= 2]
        return chapters, doc
    return None, doc

def find_hindi_video(query, api_key):
    """Searches YouTube for Hindi educational content."""
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        search_query = f"{query} educational lesson in Hindi"
        request = youtube.search().list(
            q=search_query,
            part="snippet",
            type="video",
            relevanceLanguage="hi",
            maxResults=1
        )
        response = request.execute()
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        st.error(f"YouTube Error: {e}")
    return None

# --- Main App Logic ---
uploaded_file = st.file_uploader("Upload School Book (PDF)", type="pdf")

if uploaded_file:
    chapters, doc = get_pdf_structure(uploaded_file)
    
    # Selection Mode
    st.divider()
    mode = st.radio("How would you like to select the content?", ["Select Chapter", "Manual Page Range"])
    
    chapter_text = ""
    topic_name = ""

    if mode == "Select Chapter" and chapters:
        selected = st.selectbox("Choose a Chapter:", chapters, format_func=lambda x: x['title'])
        topic_name = selected['title']
        start_p = selected['page']
        # Read up to 8 pages from chapter start
        for i in range(start_p, min(start_p + 8, len(doc))):
            chapter_text += doc[i].get_text()
    else:
        if mode == "Select Chapter":
            st.warning("No Table of Contents found. Using Manual Page Range instead.")
        
        c1, c2 = st.columns(2)
        start_page = c1.number_input("Start Page", 1, len(doc), 1)
        end_page = c2.number_input("End Page", 1, len(doc), min(start_page + 5, len(doc)))
        topic_name = f"Pages {start_page} to {end_page}"
        for i in range(start_page - 1, end_page):
            chapter_text += doc[i].get_text()

    # --- Generation Trigger ---
    if st.button("Generate Hindi Lesson Plan & Video"):
        if not openai_key or not youtube_key:
            st.error("Please enter both API keys in the sidebar!")
        else:
            with st.spinner("Processing PDF and searching for videos..."):
                client = OpenAI(api_key=openai_key)
                
                # Instruction to AI
                prompt = f"""
                You are a professional teacher. Based on the text below, create a {detail_level} lesson plan in HINDI.
                {length_map[detail_level]}
                
                Include:
                1. Objectives (उद्देश्य)
                2. Summary (सारांश)
                3. Activity (गतिविधि)
                
                TEXT: {chapter_text[:8000]}
                
                At the very end, write 'SEARCH_QUERY: [Specific Topic Name in English]'
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                output = response.choices[0].message.content
                
                # Split Plan and Video Query
                if "SEARCH_QUERY:" in output:
                    plan, search_q = output.split("SEARCH_QUERY:")
                else:
                    plan, search_q = output, topic_name
                
                # Fetch Video
                video_url = find_hindi_video(search_q.strip(), youtube_key)
                
                # --- Display Results ---
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.success("Lesson Plan Generated!")
                    st.markdown(plan)
                
                with col_right:
                    st.info("Recommended Video")
                    if video_url:
                        st.video(video_url)
                        st.write(f"[Open in YouTube]({video_url})")
                    else:
                        st.write("No matching Hindi video found.")

else:
    st.info("Waiting for PDF upload...")
