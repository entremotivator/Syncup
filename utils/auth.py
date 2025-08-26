import streamlit as st
from utils.wordpress_auth import wp_jwt_login, validate_wp_token, get_wp_user_from_supabase
from utils.woocommerce_sync import get_wc_customer_orders, display_orders_analytics

def initialize_auth_state():
    """Initialize authentication-related session state variables."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "wp_token" not in st.session_state:
        st.session_state.wp_token = None
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False

def login_with_wordpress(username: str, password: str):
    """Handle WordPress login with Supabase sync."""
    try:
        user_data = wp_jwt_login(username, password)
        if user_data:
            st.session_state.is_authenticated = True
            st.success("✅ Successfully logged in with WordPress!")
            return True
        else:
            st.session_state.is_authenticated = False
            return False
    except Exception as e:
        st.error(f"Login failed: {e}")
        st.session_state.is_authenticated = False
        return False

def logout():
    """Handle user logout."""
    st.session_state.user = None
    st.session_state.wp_token = None
    st.session_state.is_authenticated = False
    st.success("🔓 Logged out successfully!")
    st.rerun()

def check_authentication():
    """Check if user is authenticated and token is valid."""
    if not st.session_state.get('is_authenticated', False):
        return False
    
    if not st.session_state.get('wp_token'):
        return False
    
    # Validate WordPress token
    if not validate_wp_token(st.session_state.wp_token):
        st.session_state.is_authenticated = False
        st.session_state.user = None
        st.session_state.wp_token = None
        return False
    
    return True

def show_auth_page():
    """Display WordPress-only authentication page."""
    st.subheader("🔐 WordPress Login Required")
    st.info("Please log in with your WordPress credentials to access the RentCast Property Analytics.")
    
    # WordPress Login Form
    with st.form("wordpress_login_form"):
        st.markdown("### WordPress Authentication")
        username = st.text_input("WordPress Username or Email", placeholder="Enter your WordPress username or email")
        password = st.text_input("WordPress Password", type="password", placeholder="Enter your WordPress password")
        login_button = st.form_submit_button("🔑 Login with WordPress", use_container_width=True)
        
        if login_button and username and password:
            if login_with_wordpress(username, password):
                st.rerun()
    
    # Information section
    st.markdown("---")
    st.markdown("### ℹ️ Authentication Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **WordPress Integration**
        - Secure JWT authentication
        - User data synced automatically
        - WooCommerce order access
        """)
    
    with col2:
        st.markdown("""
        **Features Available**
        - Property search & analytics
        - Usage tracking & dashboard
        - Order history & analytics
        """)
    
    st.markdown("---")
    st.caption("🔒 Your data is securely synced between WordPress and our analytics platform.")

def show_user_info():
    """Display current user information and logout option."""
    if st.session_state.user:
        with st.sidebar:
            st.markdown("### 👤 User Info")
            st.write(f"**Name:** {st.session_state.user.get('display_name', 'N/A')}")
            st.write(f"**Username:** {st.session_state.user.get('username', 'N/A')}")
            st.write(f"**Email:** {st.session_state.user.get('email', 'N/A')}")
            
            if st.button("🔓 Logout", use_container_width=True):
                logout()

def show_woocommerce_orders():
    """Display WooCommerce orders for the current user."""
    if not st.session_state.user:
        return
    
    wp_user_id = st.session_state.user.get('id')
    if not wp_user_id:
        st.warning("WordPress user ID not available")
        return
    
    st.subheader("🛒 Your WooCommerce Orders")
    
    with st.spinner("Loading your orders..."):
        orders = get_wc_customer_orders(wp_user_id)
    
    if orders:
        display_orders_analytics(orders)
        
        # Detailed orders table
        st.subheader("📋 Order Details")
        
        orders_data = []
        for order in orders:
            orders_data.append({
                "Order ID": order['id'],
                "Date": order.get('date_created', '').split('T')[0],
                "Status": order.get('status', '').title(),
                "Total": f"${order.get('total_float', 0):.2f}",
                "Products": order.get('product_count', 0),
                "Payment": order.get('payment_method_title', 'N/A')
            })
        
        if orders_data:
            st.dataframe(orders_data, use_container_width=True)
    else:
        st.info("No WooCommerce orders found for your account.")

def require_auth(func):
    """Decorator to require authentication for pages."""
    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_auth_page()
            return
        return func(*args, **kwargs)
    return wrapper
