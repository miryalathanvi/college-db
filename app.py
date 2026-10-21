import streamlit as st
from pymongo import MongoClient
import google.generativeai as genai
import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Student Entry System", page_icon="🎓", layout="centered")

# ==========================================
# 2. KEYS & DATABASE CONNECTIONS
# ==========================================
# Gemini AI Setup (Replace with your actual API Key)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    genai.configure(api_key=GEMINI_API_KEY)

# Local MongoDB Setup (MongoDB Compass)
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["school_db"]               # Database name
collection = db["students"]            # Collection name

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def generate_ai_assessment(name, grade, interests, notes):
    """Generates a brief AI assessment/feedback using Google Gemini."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Provide a concise 2-sentence encouraging assessment or tailored learning recommendation for a student with the following profile:
        - Name: {name}
        - Grade/Year: {grade}
        - Interests/Subjects: {interests}
        - Teacher Notes: {notes}
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Could not generate AI assessment: {str(e)}"

# ==========================================
# 4. STREAMLIT USER INTERFACE
# ==========================================
st.title("🎓 Student Profile Builder")
st.write("Fill out the student details below. AI feedback will be generated and saved to MongoDB.")

with st.form("student_form", clear_on_submit=True):
    st.subheader("Student Details")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *")
        email = st.text_input("Email Address *")
    with col2:
        grade = st.selectbox("Grade / Level", ["Freshman", "Sophomore", "Junior", "Senior", "Grade 9", "Grade 10", "Grade 11", "Grade 12"])
        age = st.number_input("Age", min_value=5, max_value=100, value=15)

    interests = st.text_input("Interests / Favorite Subjects", placeholder="e.g., Mathematics, Coding, Art, Physics")
    notes = st.text_area("Teacher Notes / Observations", placeholder="Enter any extra notes...")

    submitted = st.form_submit_button("Save Student Record")

# Handling Submission
if submitted:
    if not name or not email:
        st.error("Please fill in all required fields (Name and Email).")
    else:
        with st.spinner("Generating AI Feedback & Saving to MongoDB..."):
            # 1. Generate AI Assessment
            ai_feedback = generate_ai_assessment(name, grade, interests, notes)
            
            # 2. Construct Data Document
            student_data = {
                "name": name,
                "email": email,
                "grade": grade,
                "age": age,
                "interests": interests,
                "notes": notes,
                "ai_feedback": ai_feedback,
                "created_at": datetime.datetime.now(datetime.timezone.utc)
            }

            # 3. Store in MongoDB
            try:
                result = collection.insert_one(student_data)
                st.success(f"Record saved for **{name}** (MongoDB ID: `{result.inserted_id}`).")
                st.info(f"**AI Assessment:** {ai_feedback}")
            except Exception as e:
                st.error(f"Failed to save to MongoDB: {e}")

# ==========================================
# 5. VIEW STORED RECORDS
# ==========================================
st.divider()
if st.checkbox("Show Stored Students from MongoDB"):
    st.subheader("Records in MongoDB")
    records = list(collection.find({}, {"_id": 0}))  # Exclude raw ObjectId for clean tabular display
    if records:
        st.dataframe(records)
    else:
        st.write("No records found in the database yet.")