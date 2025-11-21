import streamlit as st
import requests
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# ========================================
# CONFIGURATION - ADD YOUR CREDENTIALS HERE
# ========================================

# Supabase Credentials
SUPABASE_URL = "https://jqffwokcwmsbnlajhoah.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpxZmZ3b2tjd21zYm5sYWpob2FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2NzIyMzgsImV4cCI6MjA3OTI0ODIzOH0.IMwRFVvIMUJKRKAgGjykwsE7shOoUkInM7t36pYQvyM  # Replace with your Supabase anon/public key

# Platzi API Configuration
PLATZI_API_BASE = "https://api.platzi.com/graphql"

# ========================================
# INITIALIZE SUPABASE CLIENT
# ========================================

@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

# ========================================
# PLATZI API FUNCTIONS
# ========================================

def fetch_platzi_courses():
    """Fetch courses from Platzi API using GraphQL"""
    query = """
    query {
        allCourses(limit: 10) {
            edges {
                node {
                    title
                    slug
                    description
                    teacher {
                        name
                    }
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            PLATZI_API_BASE,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("allCourses", {}).get("edges", [])
        else:
            st.error(f"Platzi API error: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching Platzi courses: {e}")
        return []

# ========================================
# SUPABASE DATABASE FUNCTIONS
# ========================================

def create_courses_table(supabase):
    """Instructions for creating the table in Supabase"""
    st.info("""
    **Create this table in your Supabase SQL Editor:**
    
    ```sql
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        slug TEXT UNIQUE,
        description TEXT,
        teacher_name TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    ```
    """)

def save_course_to_supabase(supabase, course_data):
    """Save a course to Supabase"""
    try:
        response = supabase.table("courses").insert(course_data).execute()
        return True, "Course saved successfully!"
    except Exception as e:
        return False, f"Error saving course: {e}"

def get_all_courses_from_supabase(supabase):
    """Retrieve all courses from Supabase"""
    try:
        response = supabase.table("courses").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error retrieving courses: {e}")
        return []

def delete_course_from_supabase(supabase, course_id):
    """Delete a course from Supabase"""
    try:
        supabase.table("courses").delete().eq("id", course_id).execute()
        return True, "Course deleted successfully!"
    except Exception as e:
        return False, f"Error deleting course: {e}"

# ========================================
# STREAMLIT UI
# ========================================

def main():
    st.set_page_config(
        page_title="Platzi & Supabase Integration",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Platzi Courses Manager")
    st.markdown("Connect to Platzi API and manage courses in Supabase")
    
    # Initialize Supabase
    supabase = init_supabase()
    
    if not supabase:
        st.error("⚠️ Supabase connection failed. Please check your credentials.")
        st.stop()
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose an option:",
        ["Setup Instructions", "Fetch from Platzi", "View Saved Courses", "Manual Entry"]
    )
    
    # ========================================
    # PAGE: SETUP INSTRUCTIONS
    # ========================================
    
    if page == "Setup Instructions":
        st.header("🔧 Setup Instructions")
        
        st.markdown("""
        ### Step 1: Install Required Packages
        Run this in your terminal:
        ```bash
        pip install streamlit supabase requests pandas
        ```
        
        ### Step 2: Get Supabase Credentials
        1. Go to [https://supabase.com](https://supabase.com)
        2. Create a new project (or use existing)
        3. Go to **Settings** → **API**
        4. Copy:
           - **Project URL** (e.g., `https://xxxxx.supabase.co`)
           - **anon/public key**
        
        ### Step 3: Add Credentials to Code
        Open the code and replace:
        - `SUPABASE_URL = "your-project-url.supabase.co"`
        - `SUPABASE_KEY = "your-supabase-anon-key"`
        
        ### Step 4: Create Database Table
        Go to your Supabase SQL Editor and run:
        """)
        
        create_courses_table(supabase)
        
        st.markdown("""
        ### Step 5: Run the App
        ```bash
        streamlit run app.py
        ```
        """)
    
    # ========================================
    # PAGE: FETCH FROM PLATZI
    # ========================================
    
    elif page == "Fetch from Platzi":
        st.header("🌐 Fetch Courses from Platzi API")
        
        if st.button("Fetch Courses", type="primary"):
            with st.spinner("Fetching courses from Platzi..."):
                courses = fetch_platzi_courses()
                
                if courses:
                    st.success(f"Found {len(courses)} courses!")
                    
                    for idx, edge in enumerate(courses):
                        node = edge.get("node", {})
                        teacher = node.get("teacher", {})
                        
                        with st.expander(f"📖 {node.get('title', 'Unknown')}"):
                            st.write(f"**Slug:** {node.get('slug', 'N/A')}")
                            st.write(f"**Teacher:** {teacher.get('name', 'N/A')}")
                            st.write(f"**Description:** {node.get('description', 'No description')}")
                            
                            if st.button(f"Save to Supabase", key=f"save_{idx}"):
                                course_data = {
                                    "title": node.get("title"),
                                    "slug": node.get("slug"),
                                    "description": node.get("description"),
                                    "teacher_name": teacher.get("name")
                                }
                                success, message = save_course_to_supabase(supabase, course_data)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                else:
                    st.warning("No courses found or API error occurred.")
    
    # ========================================
    # PAGE: VIEW SAVED COURSES
    # ========================================
    
    elif page == "View Saved Courses":
        st.header("💾 Saved Courses in Supabase")
        
        if st.button("Refresh Data", type="primary"):
            st.rerun()
        
        courses = get_all_courses_from_supabase(supabase)
        
        if courses:
            st.success(f"Found {len(courses)} saved courses")
            
            # Display as DataFrame
            df = pd.DataFrame(courses)
            st.dataframe(df, use_container_width=True)
            
            # Individual course management
            st.subheader("Manage Courses")
            for course in courses:
                with st.expander(f"📚 {course.get('title', 'Unknown')}"):
                    st.write(f"**ID:** {course.get('id')}")
                    st.write(f"**Slug:** {course.get('slug')}")
                    st.write(f"**Teacher:** {course.get('teacher_name')}")
                    st.write(f"**Description:** {course.get('description')}")
                    st.write(f"**Created:** {course.get('created_at')}")
                    
                    if st.button(f"🗑️ Delete", key=f"delete_{course.get('id')}"):
                        success, message = delete_course_from_supabase(supabase, course.get('id'))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No courses saved yet. Fetch some from Platzi or add manually!")
    
    # ========================================
    # PAGE: MANUAL ENTRY
    # ========================================
    
    elif page == "Manual Entry":
        st.header("✏️ Manually Add Course")
        
        with st.form("manual_course_form"):
            title = st.text_input("Course Title*")
            slug = st.text_input("Course Slug (unique)*")
            teacher_name = st.text_input("Teacher Name")
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Save Course")
            
            if submitted:
                if title and slug:
                    course_data = {
                        "title": title,
                        "slug": slug,
                        "teacher_name": teacher_name,
                        "description": description
                    }
                    success, message = save_course_to_supabase(supabase, course_data)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in Title and Slug fields")

if __name__ == "__main__":
    main()
