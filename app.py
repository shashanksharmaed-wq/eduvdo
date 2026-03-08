import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build

st.set_page_config(page_title="Chapter-Wise AI Planner", layout="wide")
st.title("📖 Chapter-Specific Lesson Planner")

# --- Setup Sidebar ---
with st.sidebar:
    openai_key = st.text_input("OpenAI API Key", type="password")
    youtube_key = st.text_input("YouTube API Key", type="password")

# --- Functions ---
def get_chapters(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    toc = doc.get_toc() # This grabs the Table of Contents
    if not toc:
        return None, doc
    # Format chapters: "Chapter Name (Page X)"
    chapters = [{"title": t, "page": p - 1} for lvl, t, p in toc if lvl == 1]
    return chapters, doc

def find_youtube_video(query, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(q=query + " lesson", part="snippet", type="video", maxResults=1)
    response = request.execute()
    return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}" if response['items'] else None

# --- App Interface ---
uploaded_file = st.file_uploader("Upload School Book", type="pdf")

if uploaded_file:
    chapters, doc = get_chapters(uploaded_file)
    
    if chapters:
        # User selects which chapter to process
        selected_chapter = st.selectbox("Select a Chapter", chapters, format_func=lambda x: x['title'])
        
        if st.button("Generate Plan for this Chapter"):
            if not openai_key or not youtube_key:
                st.error("Please enter API keys first!")
            else:
                with st.spinner("Analyzing chapter..."):
                    # Extract text ONLY for that chapter (up to 10 pages)
                    start_page = selected_chapter['page']
                    chapter_text = ""
                    for i in range(start_page, min(start_page + 10, len(doc))):
                        chapter_text += doc[i].get_text()

                    # AI Call
                    client = OpenAI(api_key=openai_key)
                    prompt = f"Create a lesson plan for the chapter: {selected_chapter['title']}. Content: {chapter_text[:8000]}. End with 'SEARCH_QUERY: [topic]'"
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
                    
                    full_res = response.choices[0].message.content
                    plan, query = full_res.split("SEARCH_QUERY:")
                    
                    # Video Search
                    video_url = find_youtube_video(query.strip(), youtube_key)

                    # Result Display
                    c1, c2 = st.columns(2)
                    with c1: st.markdown(plan)
                    with c2: 
                        if video_url: st.video(video_url)
    else:
        st.warning("No Table of Contents found in this PDF. Try a different book.")
