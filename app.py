import streamlit as st
from utils.auth import (
    initialize_auth_state,
    show_auth_page,
    show_user_info,
    check_authentication,
    show_woocommerce_orders
)
from utils.database import get_user_usage, get_user_orders_summary
from datetime import datetime

st.set_page_config(
    page_title="RentCast Property Analytics",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication state
initialize_auth_state()

# Main page content
st.title("🏡 RentCast Property Analytics")
st.markdown("### WordPress & WooCommerce Integrated Analytics Platform")
st.markdown("---")

# Check authentication
if not check_authentication():
    show_auth_page()
else:
    # Show user info in sidebar
    show_user_info()

    # Get user data
    user = st.session_state.user
    user_email = user.get("email", "N/A")
    user_id = user.get("id")
    display_name = user.get("display_name", user.get("username", "User"))

    # Welcome message and quick stats
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.success(f"🎉 Welcome back, **{display_name}**!")
        st.caption(f"Logged in as: {user_email}")

    with col2:
        try:
            queries_used = get_user_usage(user_id, user_email) if user_id else 0
        except Exception as e:
            st.error(f"Error fetching API usage: {e}")
            queries_used = 0
        st.metric("API Queries Used", f"{queries_used}/30")

    with col3:
        remaining = max(0, 30 - queries_used)
        st.metric("Remaining Queries", remaining)

    st.markdown("---")

    # WooCommerce Orders Summary
    if user_id:
        try:
            orders_summary = get_user_orders_summary(user_id)
        except Exception as e:
            st.error(f"Error fetching WooCommerce orders: {e}")
            orders_summary = None

        if orders_summary:
            st.subheader("🛒 Your WooCommerce Account Summary")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Orders", orders_summary.get("total_orders", 0))

            with col2:
                st.metric(
                    "Total Spent",
                    f"${orders_summary.get('total_spent', 0.0):.2f}"
                )

            with col3:
                st.metric(
                    "Completed Orders",
                    orders_summary.get("completed_orders", 0)
                )

            with col4:
                total_orders = orders_summary.get("total_orders", 0)
                total_spent = orders_summary.get("total_spent", 0.0)
                avg_order = total_spent / total_orders if total_orders > 0 else 0
                st.metric("Average Order", f"${avg_order:.2f}")

            # Show recent orders
            recent_orders = orders_summary.get("recent_orders", [])
            if recent_orders:
                st.subheader("📋 Recent Orders")
                for order in recent_orders[:3]:
                    with st.expander(
                        f"Order #{order.get('wc_order_id')} - ${order.get('total', 0):.2f}"
                    ):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Status:** {order.get('status', 'N/A').title()}")
                            date_created = order.get("date_created")
                            # Ensure timestamp is valid
                            if not date_created:
                                date_created = "N/A"
                            st.write(f"**Date:** {date_created[:10] if date_created != 'N/A' else 'N/A'}")
                        with col2:
                            st.write(f"**Products:** {order.get('product_count', 0)}")
                            st.write(f"**Payment:** {order.get('payment_method', 'N/A')}")

            st.markdown("---")

    # App overview
    st.subheader("📋 Available Features")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 🏠 Property Search
        - Search properties by address
        - Get detailed property information
        - View market analytics
        - RentCast API integration
        """)

    with col2:
        st.markdown("""
        ### 📊 Usage Dashboard
        - Track your API usage
        - View query history
        - Monitor account limits
        - WordPress user analytics
        """)

    with col3:
        st.markdown("""
        ### 🛒 WooCommerce Integration
        - View your order history
        - Order analytics & trends
        - Customer insights
        - Product information
        """)

    st.markdown("---")

    # Integration Status
    st.subheader("🔗 Integration Status")
    col1, col2 = st.columns(2)

    with col1:
        st.success("✅ **WordPress Authentication**")
        st.caption("Successfully connected to WordPress via JWT")
        st.success("✅ **Supabase Data Sync**")
        st.caption("User data synced to Supabase database")

    with col2:
        st.success("✅ **WooCommerce Integration**")
        st.caption("Order and product data available")
        st.success("✅ **RentCast API Ready**")
        st.caption("Property analytics API configured")

    st.markdown("---")

    # Quick Actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Search Properties", use_container_width=True):
            st.switch_page("pages/1_🏠_Property_Search.py")

    with col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/2_📊_Usage_Dashboard.py")

    with col3:
        if st.button("👤 Manage Profile", use_container_width=True):
            st.switch_page("pages/3_👤_Profile.py")

    st.markdown("---")

    # Show WooCommerce orders section
    with st.expander("🛒 View All WooCommerce Orders", expanded=False):
        try:
            show_woocommerce_orders()
        except Exception as e:
            st.error(f"Error displaying WooCommerce orders: {e}")

    st.markdown("---")
    st.info(
        "💡 **Navigation:** Use the sidebar to access different features of the application. "
        "Your WordPress login session is maintained across all pages."
    )

    # Footer
    st.markdown("---")
    st.caption(
        "🔒 **Security:** This application uses WordPress JWT authentication with "
        "Supabase data synchronization. Your data is encrypted and securely stored."
    )
