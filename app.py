import streamlit as st
from utils.auth import initialize_auth_state, show_auth_page, show_user_info, show_woocommerce_orders
from utils.database import get_user_usage, get_user_orders_summary
from utils.woo_product_auth import get_user_product_access_level

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
st.markdown("---")

# Same authentication check as original
if st.session_state.user is None:
    show_auth_page()
else:
    # Show user info in sidebar
    show_user_info()
    
    # Get user data (same structure as original)
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    display_name = getattr(st.session_state.user, 'display_name', user_email)
    
    # Welcome message and quick stats
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.success(f"Welcome back, {display_name}!")
        
        # Show WooCommerce product access info
        if hasattr(st.session_state.user, 'purchased_products'):
            access_info = get_user_product_access_level(user_email)
            st.caption(f"🛒 Access Level: {access_info['access_level'].title()} ({access_info['product_count']} products owned)")
    
    with col2:
        queries_used = get_user_usage(user_id, user_email)
        st.metric("Queries Used", f"{queries_used}/30")
    
    with col3:
        remaining = max(0, 30 - queries_used)
        st.metric("Remaining", remaining)
    
    st.markdown("---")
    
    # WooCommerce Product Access Summary
    if hasattr(st.session_state.user, 'purchased_products') and st.session_state.user.purchased_products:
        st.subheader("🛒 Your Product Access")
        
        access_info = get_user_product_access_level(user_email)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Products Owned", access_info['product_count'])
        
        with col2:
            st.metric("Total Spent", f"${access_info['total_spent']:.2f}")
        
        with col3:
            st.metric("Access Level", access_info['access_level'].title())
        
        with col4:
            permissions_count = len(access_info['permissions'])
            st.metric("Permissions", permissions_count)
        
        # Show recent products
        st.subheader("📦 Recent Product Purchases")
        recent_products = sorted(st.session_state.user.purchased_products, 
                               key=lambda x: x.get('order_date', ''), reverse=True)[:3]
        
        for product in recent_products:
            with st.expander(f"{product.get('name', 'Product')} - ${product.get('total', 0)}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Product ID:** {product.get('product_id')}")
                    st.write(f"**Quantity:** {product.get('quantity', 1)}")
                with col2:
                    st.write(f"**Order ID:** {product.get('order_id')}")
                    st.write(f"**Purchase Date:** {product.get('order_date', 'N/A')[:10]}")
        
        st.markdown("---")
    
    # App overview (same as original)
    st.subheader("📋 Available Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🏠 Property Search
        - Search properties by address
        - Get detailed property information
        - View market analytics
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Usage Dashboard
        - Track your API usage
        - View query history
        - Monitor account limits
        """)
    
    with col3:
        st.markdown("""
        ### 👤 Profile Management
        - Update account settings
        - View product purchases
        - Manage preferences
        """)
    
    st.markdown("---")
    
    # Show WooCommerce orders section
    with st.expander("🛒 View All WooCommerce Orders", expanded=False):
        show_woocommerce_orders()
    
    st.markdown("---")
    st.info("💡 Use the sidebar navigation to access different features of the application.")
