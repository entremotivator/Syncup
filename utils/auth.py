import streamlit as st
from utils.woo_product_auth import woo_product_login, get_user_product_access_level
from utils.woocommerce_sync import get_wc_customer_orders, display_orders_analytics

def initialize_auth_state():
    """Initialize authentication-related session state variables."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None

def login(email, password):
    """Handle user login using WooCommerce products."""
    try:
        user_data = woo_product_login(email, password)
        if user_data:
            # Store user data in session
            st.session_state.user = type('User', (), {
                'id': user_data.get('wp_user_id') or user_data.get('wc_customer_id') or hash(email),
                'email': user_data['email'],
                'username': user_data['username'],
                'display_name': user_data['display_name'],
                'purchased_products': user_data['purchased_products'],
                'product_access': user_data['product_access']
            })()
            st.session_state.access_token = user_data.get('wp_token', 'woo_access')
            return user_data
        return None
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None

def logout():
    """Handle user logout."""
    st.session_state.user = None
    st.session_state.access_token = None
    st.success("Logged out successfully!")
    st.rerun()

def show_auth_page():
    """Display authentication page - same as original but with WooCommerce product auth."""
    st.subheader("🔐 Please sign in to continue")
    
    # Keep only the Login tab (no signup)
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button and email and password:
            user = login(email, password)
            if user:
                st.success("Logged in successfully!")
                st.rerun()

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

    if st.session_state.user:
        with st.sidebar:
            st.markdown("### 👤 User Info")
            st.write(f"**Name:** {st.session_state.user.display_name}")
            st.write(f"**Email:** {st.session_state.user.email}")
            
            # Show product access info
            if hasattr(st.session_state.user, 'purchased_products'):
                product_count = len(st.session_state.user.purchased_products)
                st.write(f"**Products Owned:** {product_count}")
                
                # Show access level
                access_info = get_user_product_access_level(st.session_state.user.email)
                st.write(f"**Access Level:** {access_info['access_level'].title()}")
            
            if st.button("🔓 Logout", use_container_width=True):
                logout()

def show_woocommerce_orders():
    """Display WooCommerce orders for the current user."""
    if not st.session_state.user:
        return
    
    user_id = st.session_state.user.id
    if not user_id:
        st.warning("User ID not available")
        return
    
    st.subheader("🛒 Your WooCommerce Orders")
    
    with st.spinner("Loading your orders..."):
        orders = get_wc_customer_orders(user_id)
    
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

def get_user_client():
    """Return a mock client for compatibility with existing code."""
    return st.session_state.get('access_token') is not None

def require_auth(func):
    """Decorator to require authentication for pages."""
    def wrapper(*args, **kwargs):
        if st.session_state.user is None:
            show_auth_page()
            return
        return func(*args, **kwargs)
    return wrapper
