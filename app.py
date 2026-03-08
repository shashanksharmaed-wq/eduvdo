import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build

# --- App Config ---
st.set_page_config(page_title="AI School Lesson Planner", layout="wide")
st.title("📚 AI Lesson & Video Generator")
st.subheader("Upload a textbook PDF to generate plans and video links")

# --- Sidebar for API Keys ---
with st.sidebar:
    st.header("Setup")
    openai_key = st.text_input("OpenAI API Key", type="password")
    youtube_key = st.text_input("YouTube API Key", type="password")
    st.info("Get an OpenAI key at platform.openai.com and YouTube key at console.cloud.google.com")

# --- Functions ---
def extract_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:10000] # Limit text for API stability

def find_youtube_video(query, api_key):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(q=query + " educational", part="snippet", type="video", maxResults=1)
    response = request.execute()
    if response['items']:
        return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    return None

# --- Main UI ---
uploaded_file = st.file_uploader("Choose a School Book (PDF)", type="pdf")

if uploaded_file and openai_key and youtube_key:
    if st.button("Generate Lesson Plan"):
        client = OpenAI(api_key=openai_key)
        
        with st.spinner("Reading book and finding videos..."):
            # 1. Extract
            book_text = extract_text(uploaded_file)
            
            # 2. AI Generation
            prompt = f"Create a detailed lesson plan based on this text. End the response with a line exactly like this: 'SEARCH_QUERY: [insert 3 word topic here]'. \n\n Text: {book_text}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            full_text = response.choices[0].message.content
            
            # 3. Parse Video Query & Fetch
            plan_content, search_part = full_text.split("SEARCH_QUERY:")
            video_url = find_youtube_video(search_part.strip(), youtube_key)
            
            # 4. Display Results
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📝 Generated Lesson Plan")
                st.write(plan_content)
            
            with col2:
                st.markdown("### 🎥 Recommended Video")
                if video_url:
                    st.video(video_url)
                    st.success(f"Video Found: {video_url}")
                else:
                    st.warning("No relevant video found.")
else:
    st.warning("Please upload a PDF and enter your API keys in the sidebar.")
