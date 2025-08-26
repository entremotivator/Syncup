# pages/2_📊_Usage_Dashboard.py
# =====================================================

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from utils.auth import initialize_auth_state
from utils.database import get_user_usage, get_usage_history

st.set_page_config(page_title="Usage Dashboard", page_icon="📊")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("📊 Usage Dashboard")
st.markdown("Monitor your API usage and account activity.")

user_email = st.session_state.user.email
user_id = st.session_state.user.id
queries_used = get_user_usage(user_id, user_email)

# Usage overview
st.subheader("🎯 Usage Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Queries Used", 
        queries_used, 
        delta=f"-{30-queries_used} remaining"
    )

with col2:
    usage_percentage = (queries_used / 30) * 100
    st.metric("Usage %", f"{usage_percentage:.1f}%")

with col3:
    remaining = 30 - queries_used
    st.metric("Remaining", remaining)

with col4:
    # Calculate days until reset (this would depend on your billing cycle)
    # For demo, assuming monthly reset
    now = datetime.now()
    next_month = now.replace(day=1) + timedelta(days=32)
    next_reset = next_month.replace(day=1)
    days_until_reset = (next_reset - now).days
    st.metric("Days Until Reset", days_until_reset)

# Progress bar
st.subheader("📈 Usage Progress")
progress = queries_used / 30
st.progress(progress)

# Color-coded status
if progress >= 1.0:
    st.error("🚫 Limit Reached - No more queries available")
elif progress >= 0.8:
    st.warning("⚠️ High Usage - Approaching limit")
elif progress >= 0.5:
    st.info("📊 Moderate Usage")
else:
    st.success("✅ Low Usage - Plenty of queries remaining")

# Usage chart (mock data - you'd want to implement proper tracking)
st.subheader("📉 Usage Trends")

# Generate mock daily usage data
dates = pd.date_range(start=datetime.now() - timedelta(days=29), end=datetime.now(), freq='D')
# Simulate usage pattern
mock_daily_usage = []
cumulative = 0
for i, date in enumerate(dates):
    if i < len(dates) - 1:  # All days except today
        daily = min(max(0, int(queries_used * (0.8 + 0.4 * (i / len(dates))) / len(dates) + 
                      (1 if i % 3 == 0 else 0))), 5)  # Random but realistic pattern
    else:  # Today
        daily = queries_used - cumulative
    
    cumulative += daily
    mock_daily_usage.append(daily)
    
    if cumulative >= queries_used:
        break

usage_df = pd.DataFrame({
    'Date': dates[:len(mock_daily_usage)],
    'Daily Queries': mock_daily_usage,
    'Cumulative': pd.Series(mock_daily_usage).cumsum()
})

fig = px.line(usage_df, x='Date', y='Cumulative', 
              title='Cumulative API Usage Over Time',
              labels={'Cumulative': 'Total Queries Used'})
fig.add_hline(y=30, line_dash="dash", line_color="red", 
              annotation_text="Query Limit (30)")

st.plotly_chart(fig, use_container_width=True)

# Usage by day of week (mock analysis)
st.subheader("📅 Usage Patterns")

col1, col2 = st.columns(2)

with col1:
    # Mock day of week data
    dow_data = pd.DataFrame({
        'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'Avg Queries': [4, 5, 6, 4, 3, 1, 2]  # Mock data
    })
    
    fig_dow = px.bar(dow_data, x='Day', y='Avg Queries', 
                     title='Average Usage by Day of Week')
    st.plotly_chart(fig_dow, use_container_width=True)

with col2:
    # Usage statistics
    st.subheader("📊 Statistics")
    st.metric("Average Daily Usage", f"{queries_used/30:.1f}")
    st.metric("Peak Usage Day", "Wednesday")  # Mock data
    st.metric("Most Active Hour", "2 PM")  # Mock data

# Account details
st.markdown("---")
st.subheader("👤 Account Details")

col1, col2 = st.columns(2)

with col1:
    st.text_input("Email", value=user_email, disabled=True)
    st.text_input("User ID", value=str(user_id), disabled=True)

with col2:
    st.text_input("Plan Type", value="Free Tier", disabled=True)
    st.text_input("Member Since", value=datetime.now().strftime("%B %Y"), disabled=True)

# Upgrade options (mock)
st.markdown("---")
st.subheader("🚀 Upgrade Options")
st.info("""
**Need more queries?** Consider upgrading to a premium plan:
- **Basic Plan**: 100 queries/month - $9.99/month
- **Pro Plan**: 500 queries/month - $29.99/month  
- **Business Plan**: Unlimited queries - $99.99/month
""")

if st.button("Contact Sales", type="secondary"):
    st.success("Coming soon! Contact support for upgrade options.")
