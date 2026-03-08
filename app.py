import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI
from googleapiclient.discovery import build
from fpdf import FPDF

# --- 1. SECURE API LOADING ---
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# --- 2. PDF GENERATION CLASS ---
class ScriptedPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Premium Teacher Manual (60 Min)', 0, 1, 'R')
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
def find_educational_video(query, api_key, language):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            q=f"{query} educational lesson {language}",
            part="snippet", type="video", maxResults=1
        )
        response = request.execute()
        if response['items']:
            return f"https://www.youtube.com/watch?v={response['items'][0]['id']['videoId']}"
    except Exception:
        pass
    return None

# --- 4. APP INTERFACE & SETUP ---
st.set_page_config(page_title="Premium Curriculum Engine", layout="wide")
st.title("🏆 Premium Curriculum Master Engine")
st.markdown("### Surpassing LEAD & Chrysalis | High-Density Scripting | Micro-Teaching")

if not OPENAI_KEY or not YOUTUBE_KEY:
    with st.sidebar:
        st.warning("⚠️ API Keys missing from Secrets. Please enter below:")
        OPENAI_KEY = st.text_input("OpenAI API Key", type="password")
        YOUTUBE_KEY = st.text_input("YouTube API Key", type="password")

# --- 5. CORE LOGIC ---
uploaded_file = st.file_uploader("Upload Textbook (PDF)", type="pdf")

if uploaded_file:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    st.info(f"📚 Total Book Pages: {total_pages} | Recommended Pacing: ~{round(total_pages/165, 1)} pages/day.")

    st.divider()
    st.markdown("#### 🎯 Lesson Settings")
    col_lang, col_class, col_age = st.columns(3)
    
    target_lang = col_lang.selectbox("Medium of Instruction", ["English", "Hindi", "Marathi", "Gujarati", "Tamil", "Telugu", "Bengali", "Kannada"])
    target_class = col_class.selectbox("Class / Grade", ["Pre-Primary (KG)", "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8"])
    target_age = col_age.selectbox("Student Age Group", ["3-5 years", "6-8 years", "9-11 years", "12-14 years"])

    st.divider()
    c1, c2 = st.columns(2)
    start_p = c1.number_input("Start Page", 1, total_pages, 1)
    end_p = c2.number_input("End Page (Optional)", start_p, total_pages, start_p)

    if st.button(f"🚀 Generate Premium {target_lang} Manual for {target_class}"):
        if not OPENAI_KEY or not YOUTUBE_KEY:
            st.error("API Keys required to proceed.")
        else:
            with st.spinner(f"Writing High-Density Script... Integrating Micro-Teaching Skills..."):
                
                text_context = ""
                for i in range(start_p - 1, end_p):
                    text_context += doc[i].get_text()
                
                client = OpenAI(api_key=OPENAI_KEY)
                
                # --- THE ULTIMATE MASTER PROMPT ---
                prompt = f"""
                You are a Master Curriculum Architect designing a premium teacher's manual that MUST SURPASS LEAD School, Chrysalis, and EDAC standards. 
                Create a 60-minute lesson plan in {target_lang.upper()} for {target_class} (Age: {target_age}).
                
                CRITICAL RULE ON TIME: You CANNOT have 15 minutes of time pass with only 2 lines of dialogue. For EVERY 5-minute block, you MUST write highly dense dialogue, actions, and questions that would physically take 5 minutes to say and do. 
                
                FORMAT EVERY CORE SCRIPT BLOCK EXACTLY LIKE THIS:
                **[Time Marker: e.g., Minute 15 - 18]**
                * **Teacher Does:** [Exact physical action]
                * **Teacher Says ({target_lang}):** "[Minimum 4 to 5 full sentences of exact dialogue]"
                * **Anticipated Student Response:** "[What the kids will say]"
                * **Remediation:** "[What to say if the kids get it wrong]"
                * **Board Work:** "[Exactly what to write/draw on the blackboard right now]"
                * **Micro-Teaching Skill Applied:** "[Name the specific teaching skill used here, e.g., Skill of Reinforcement]"

                FULL LESSON STRUCTURE:
                1. MICRO-TEACHING FOCUS: List 2 specific micro-teaching skills (e.g., Skill of Probing Questions, Skill of Stimulus Variation) for the teacher to practice today and a quick 1-sentence tip for each.
                2. THE HOOK (Min 0-5): A full 4-8 line {target_lang} rhyme or detailed 2-minute story to grab {target_age} olds. Include physical actions.
                3. DISCOVERY & PRE-ASSESSMENT (Min 5-15): Provide 5 deep questions using the format above.
                4. CORE INSTRUCTION (Min 15-40): Break this into strictly 3-to-4 minute micro-blocks. YOU MUST FILL THE TIME WITH DIALOGUE. Use the format above for EVERY block.
                5. PLAY-BASED ACTIVITY (Min 40-52): Explicit {target_lang} game rules. Step 1, Step 2, Step 3. What the teacher says to start the game.
                6. WRAP-UP & TLM (Min 52-60): Specific local items needed. Final concluding dialogue.
                7. PEDAGOGY MAPPING: Show Adhiti, Bodha, Abhyasa, Prayoga, Prasar.
                8. MIND MAP: Bulleted text hierarchy (->) summarizing the lesson.
                9. BOARD SNAPSHOT & ASSESSMENT: 3 MCQs, 2 Short Answers, 1 Creative Task.

                Book Text Context: {text_context[:8000]}
                
                End with this exact tag format:
                SEARCH_QUERY: [Specific Topic in English]
                """

                # Using gpt-4o for maximum instruction following and verbose output
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000 
                )
                
                full_output = response.choices[0].message.content
                
                if "SEARCH_QUERY:" in full_output:
                    parts = full_output.split("SEARCH_QUERY:")
                    plan_content = parts[0].strip()
                    video_query = parts[1].strip()
                else:
                    plan_content = full_output
                    video_query = f"Topic page {start_p} lesson"

                v_url = find_educational_video(video_query, YOUTUBE_KEY, target_lang)
                
                # --- 6. UI DISPLAY ---
                st.divider()
                col_plan, col_vid = st.columns([2, 1])
                
                with col_plan:
                    st.success("High-Density Premium Manual Ready!")
                    st.markdown(plan_content)
                    
                    pdf = ScriptedPDF()
                    pdf.add_page()
                    pdf.chapter_title(f"Premium Script: Pages {start_p}-{end_p} ({target_class})")
                    pdf.add_script_body(plan_content)
                    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
                    
                    st.download_button(
                        label="📥 Download Premium PDF", 
                        data=pdf_bytes, 
                        file_name=f"Premium_Script_{target_class}_P{start_p}.pdf"
                    )
                    st.caption("💡 Tip: Use **Ctrl + P** on this webpage to print/save perfectly with regional Hindi/Marathi fonts!")

                with col_vid:
                    st.info(f"Classroom Video Aid ({target_lang})")
                    if v_url:
                        st.video(v_url)
                        st.write(f"[Open on YouTube]({v_url})")
                    else:
                        st.warning("No matching educational video found.")
else:
    st.info("Waiting for textbook PDF upload...")
