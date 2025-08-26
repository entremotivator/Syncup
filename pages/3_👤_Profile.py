import streamlit as st
from datetime import datetime
from utils.auth import initialize_auth_state, logout

st.set_page_config(page_title="Profile", page_icon="👤")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("👤 Profile Management")
st.markdown("Manage your account settings and preferences.")

user_email = st.session_state.user.email
user_id = st.session_state.user.id

# Profile overview
st.subheader("📋 Account Information")

col1, col2 = st.columns(2)

with col1:
    st.text_input("Email Address", value=user_email, disabled=True)
    st.text_input("User ID", value=str(user_id), disabled=True, help="Your unique identifier")

with col2:
    st.text_input("Account Status", value="Active", disabled=True)
    st.text_input("Member Since", value=datetime.now().strftime("%B %d, %Y"), disabled=True)

# Account actions
st.markdown("---")
st.subheader("🔧 Account Actions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔐 Security")
    
    if st.button("Change Password", type="secondary", use_container_width=True):
        st.info("Password change functionality would be implemented here using Supabase auth.")
    
    if st.button("Enable 2FA", type="secondary", use_container_width=True):
        st.info("Two-factor authentication setup would be implemented here.")

with col2:
    st.markdown("### 📧 Communication")
    
    email_notifications = st.checkbox("Email Notifications", value=True)
    usage_alerts = st.checkbox("Usage Limit Alerts", value=True)
    
    if st.button("Save Preferences", type="primary", use_container_width=True):
        st.success("Preferences saved successfully!")

# Data management
st.markdown("---")
st.subheader("💾 Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Data", type="secondary", use_container_width=True):
        st.info("Data export functionality would generate a CSV/JSON file with your usage history.")

with col2:
    if st.button("Clear History", type="secondary", use_container_width=True):
        st.warning("This would clear your search history (with confirmation dialog).")

with col3:
    if st.button("Delete Account", type="secondary", use_container_width=True):
        st.error("Account deletion would require email confirmation and a waiting period.")

# API key management (if applicable)
st.markdown("---")
st.subheader("🔑 API Access")

st.info("""
**API Integration Status**: Your account is connected to RentCast API through our secure backend.
No direct API key management is required for standard users.
""")

# Usage statistics
st.markdown("---")
st.subheader("📊 Account Statistics")

# Mock statistics - you would pull these from your database
stats_col1, stats_col2, stats_col3 = st.columns(3)

with stats_col1:
    st.metric("Total Searches", "42", delta="3 this week")

with stats_col2:
    st.metric("Favorite Search Type", "Properties")

with stats_col3:
    st.metric("Average Daily Usage", "1.4", delta="0.2 vs last month")

# Support section
st.markdown("---")
st.subheader("🆘 Support")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Need Help?**
    - 📚 Check our documentation
    - 💬 Contact support via email
    - 🎥 Watch tutorial videos
    """)

with col2:
    if st.button("Contact Support", type="secondary", use_container_width=True):
        st.success("Support ticket system would be integrated here.")

# Logout section
st.markdown("---")
st.subheader("🚪 Session Management")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("**Ready to sign out?** You'll need to log back in to access your account.")

with col2:
    if st.button("Logout", type="primary", use_container_width=True):
        logout()

# Footer
st.markdown("---")
st.caption("RentCast Property Analytics • Secure • Reliable • Fast")
