# app.py

# --- THE GOLDEN FIX: Force the project root into the Python path ---
# This explicitly tells the running script where to find its packages.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from orchestration.main_orchestrator import MainOrchestrator

load_dotenv()

st.set_page_config(page_title="Autonomous 247 Hub", page_icon="🤖", layout="wide")

@st.cache_resource
def get_orchestrator():
    print("UI: Initializing MainOrchestrator for the first time...")
    return MainOrchestrator()

orchestrator = get_orchestrator()

# --- The rest of the file is IDENTICAL to the last correct version ---
# (Session state, auth handling, UI layout, etc.)
def initialize_session_state():
    defaults = {
        'linkedin_authenticated': False,
        'is_generating': False,
        'current_task_message': "",
        'last_result': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
initialize_session_state()
def handle_linkedin_auth():
    auth_code = st.query_params.get("code")
    if auth_code and not st.session_state.linkedin_authenticated:
        with st.spinner("Finalizing LinkedIn connection..."):
            token_response = orchestrator.linkedin_service.exchange_code_for_token(auth_code)
            if token_response and token_response.get("success"):
                if orchestrator.linkedin_service.fetch_user_info():
                    st.session_state.linkedin_authenticated = True
                    st.success("✅ LinkedIn connected successfully!")
                    st.query_params.clear()
                else:
                    st.error("Authentication succeeded, but failed to fetch user profile.")
            else:
                error_msg = token_response.get('message', 'An unknown error occurred.')
                st.error(f"Connection failed: {error_msg}")
        st.stop()
handle_linkedin_auth()
st.title("Autonomous 247 Content Hub 🤖")
st.caption("Your AI-Powered Content Automation Co-Pilot")
st.divider()
st.header("✨ Manual Content Generation")
if st.session_state.is_generating:
    st.info(st.session_state.current_task_message)
    if st.button("🛑 STOP GENERATION", use_container_width=True, type="secondary"):
        orchestrator.trigger_kill_switch()
        st.warning("Stop signal sent! The process will halt gracefully at the next step...")
else:
    content_type = st.selectbox("1. Select a Task:",("YouTube Video", "Astrology Daily Posts", "LinkedIn Post"),key="sb_content_type")
    if content_type == "Astrology Daily Posts":
        st.info("This will generate 12 image posts (one for each zodiac sign) based on today's data.")
        if st.button("🔮 Generate Today's 12 Astrology Posts", use_container_width=True, type="primary"):
            st.session_state.is_generating = True
            st.session_state.current_task_message = "Generating 12 Astrology Posts..."
            orchestrator.reset_kill_switch()
            with st.spinner("Generating posts... This may take several minutes."):
                posts = orchestrator.generate_all_astrology_posts()
            if posts is not None:
                st.session_state.last_result = {"success": True, "message": f"Successfully generated {len(posts)} astrology posts!"}
            else:
                st.session_state.last_result = {"success": False, "message": "Astrology post generation failed or was cancelled."}
            st.session_state.is_generating = False
            st.rerun()
    else:
        niche = st.text_input("2. Enter Niche:", placeholder="e.g., Artificial Intelligence, Health & Wellness", key="ti_niche")
        topic = st.text_input("3. Enter a Topic:", placeholder="e.g., The Future of Generative AI", key="ti_topic")
        auto_search = st.toggle("Enable Autonomous Research", value=True, help="Allows the AI to search the web for context before generating.")
        if st.button(f"🚀 Generate {content_type}", use_container_width=True, type="primary", disabled=(not topic or not niche)):
            st.session_state.is_generating = True
            st.session_state.current_task_message = f"Generating {content_type} on '{topic}'..."
            orchestrator.reset_kill_switch()
            result = None
            with st.spinner(st.session_state.current_task_message):
                if content_type == "YouTube Video":
                    result = orchestrator.generate_single_youtube_video(topic=topic, niche=niche, auto_search_context=auto_search, upload=False)
            st.session_state.last_result = result
            st.session_state.is_generating = False
            st.rerun()
if st.session_state.last_result:
    res = st.session_state.last_result
    if res.get("success"):
        st.success(res.get("message", "Operation completed successfully!"))
        if res.get("path"):
            st.info(f"Output file is available at: {res['path']}")
    else:
        st.error(res.get("message", "An unknown error occurred."))
    st.session_state.last_result = None
st.divider()
with st.expander("⚙️ System Automation & Settings"):
    st.subheader("System Dashboard")
    status_data = orchestrator.get_automation_status()
    stats = status_data.get('stats', {})
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Automation Status", "Running" if status_data.get('is_running') else "Stopped")
    c2.metric("Videos Generated", stats.get('videos_generated', 0))
    c3.metric("Videos Uploaded", stats.get('videos_uploaded', 0))
    c4.metric("Errors", stats.get('errors', 0))
    next_run = status_data.get('next_run', 'N/A')
    if next_run != 'N/A' and next_run != "No jobs scheduled":
        c5.metric("Next Scheduled Run", datetime.fromisoformat(next_run.split('.')[0]).strftime('%a, %H:%M'))
    else:
        c5.metric("Next Scheduled Run", next_run)
    st.subheader("Automated Mode (YouTube Only)")
    col1_auto, col2_auto = st.columns(2)
    with col1_auto:
        if st.button("▶️ Start Automation", use_container_width=True):
            orchestrator.start_automation()
            st.toast("Automation scheduler started!")
            st.rerun()
    with col2_auto:
        if st.button("⏹️ Stop Automation", use_container_width=True):
            orchestrator.stop_automation()
            st.toast("Automation scheduler stopped.")
            st.rerun()
    st.subheader("Automation Settings")
    current_settings = orchestrator.scheduler.settings 
    with st.form("settings_form"):
        automation_niche = st.text_input("Automation Niche", value=current_settings.get("automation_niche", ""))
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        selected_days = st.multiselect("Upload Days", options=days, default=current_settings.get("upload_days", []))
        h, m = map(int, current_settings.get("upload_time", "19:00").split(':'))
        selected_time = st.time_input("Upload Time (UTC)", value=datetime(2023, 1, 1, h, m).time())
        if st.form_submit_button("💾 Save Settings"):
            new_settings = {"automation_niche": automation_niche, "upload_days": selected_days, "upload_time": selected_time.strftime("%H:%M")}
            orchestrator.update_automation_settings(new_settings)
            st.toast("Settings saved successfully!")
            st.rerun()
    st.subheader("🔗 Connect Social Accounts")
    if st.session_state.linkedin_authenticated:
        st.success("✅ Connected to LinkedIn!")
    else:
        auth_url = orchestrator.linkedin_service.generate_auth_url()
        st.link_button("Connect to LinkedIn", auth_url)
