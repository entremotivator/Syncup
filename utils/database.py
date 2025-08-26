import streamlit as st
from utils.wordpress_auth import supabase

def initialize_user_usage(wp_user_id: int, email: str):
    """Initialize usage tracking for a WordPress user."""
    if not supabase:
        st.error("Supabase not available")
        return False

    try:
        # Check if usage record already exists
        existing = supabase.table("api_usage").select("*").eq("wp_user_id", wp_user_id).execute()
        
        if not existing.data:
            # Create new usage record
            supabase.table("api_usage").insert({
                "wp_user_id": wp_user_id,
                "email": email,
                "queries": 0,
                "created_at": st.session_state.get('current_time', 'now()')
            }).execute()
            return True
        return True
    except Exception as e:
        st.error(f"Failed to initialize usage tracking: {e}")
        return False

def get_user_usage(wp_user_id: int, email: str):
    """Get current API usage for a WordPress user."""
    if not supabase:
        return 0

    try:
        response = supabase.table("api_usage").select("*").eq("wp_user_id", wp_user_id).execute()
        if response.data:
            return response.data[0]["queries"]
        else:
            # Create usage record if it doesn't exist
            initialize_user_usage(wp_user_id, email)
            return 0
    except Exception as e:
        st.warning(f"Failed to get usage data: {e}")
        return 0

def increment_usage(wp_user_id: int, email: str):
    """Increment API usage count for a WordPress user."""
    if not supabase:
        return False

    try:
        current = get_user_usage(wp_user_id, email)
        result = supabase.table("api_usage").update({
            "queries": current + 1,
            "last_query": st.session_state.get('current_time', 'now()')
        }).eq("wp_user_id", wp_user_id).execute()
        
        return result.data is not None
    except Exception as e:
        st.error(f"Failed to increment usage: {e}")
        return False

def get_usage_history(wp_user_id: int):
    """Get usage history for dashboard."""
    if not supabase:
        return []

    try:
        # Get usage record
        usage_response = supabase.table("api_usage").select("*").eq("wp_user_id", wp_user_id).execute()
        
        # Get query history if available (you might want to add a query_history table)
        history_response = supabase.table("query_history").select("*").eq("wp_user_id", wp_user_id).order("created_at", desc=True).limit(50).execute()
        
        return {
            "usage": usage_response.data[0] if usage_response.data else None,
            "history": history_response.data if history_response.data else []
        }
    except Exception as e:
        st.warning(f"Failed to get usage history: {e}")
        return {"usage": None, "history": []}

def log_query(wp_user_id: int, email: str, query_type: str, query_data: dict):
    """Log a query to the history table."""
    if not supabase:
        return False

    try:
        supabase.table("query_history").insert({
            "wp_user_id": wp_user_id,
            "email": email,
            "query_type": query_type,
            "query_data": query_data,
            "created_at": st.session_state.get('current_time', 'now()')
        }).execute()
        return True
    except Exception as e:
        st.warning(f"Failed to log query: {e}")
        return False

def check_usage_limit(wp_user_id: int, email: str, limit: int = 30):
    """Check if user has exceeded usage limit."""
    current_usage = get_user_usage(wp_user_id, email)
    return current_usage < limit

def get_user_profile(wp_user_id: int):
    """Get user profile from Supabase."""
    if not supabase:
        return None

    try:
        response = supabase.table("wp_users").select("*").eq("wp_user_id", wp_user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.warning(f"Failed to get user profile: {e}")
        return None

def update_user_profile(wp_user_id: int, profile_data: dict):
    """Update user profile in Supabase."""
    if not supabase:
        return False

    try:
        result = supabase.table("wp_users").update(profile_data).eq("wp_user_id", wp_user_id).execute()
        return result.data is not None
    except Exception as e:
        st.error(f"Failed to update user profile: {e}")
        return False

def get_user_orders_summary(wp_user_id: int):
    """Get user's WooCommerce orders summary from Supabase."""
    if not supabase:
        return None

    try:
        response = supabase.table("wc_orders").select("*").eq("wp_user_id", wp_user_id).execute()
        
        if response.data:
            orders = response.data
            total_orders = len(orders)
            total_spent = sum(float(order.get('total', 0)) for order in orders)
            completed_orders = len([o for o in orders if o.get('status') == 'completed'])
            
            return {
                "total_orders": total_orders,
                "total_spent": total_spent,
                "completed_orders": completed_orders,
                "recent_orders": sorted(orders, key=lambda x: x.get('date_created', ''), reverse=True)[:5]
            }
        return None
    except Exception as e:
        st.warning(f"Failed to get orders summary: {e}")
        return None

def cleanup_old_sessions():
    """Clean up old user sessions (optional maintenance function)."""
    if not supabase:
        return False

    try:
        # Remove sessions older than 7 days
        import datetime
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
        
        supabase.table("user_sessions").delete().lt("last_login", cutoff_date).execute()
        return True
    except Exception as e:
        st.warning(f"Failed to cleanup old sessions: {e}")
        return False

# Database schema creation functions (run once to set up tables)
def create_database_tables():
    """Create necessary database tables in Supabase (run this once)."""
    if not supabase:
        return False

    # Note: These would typically be created via Supabase dashboard or SQL
    # This is just documentation of the required schema
    
    schemas = {
        "wp_users": """
        CREATE TABLE wp_users (
            id SERIAL PRIMARY KEY,
            wp_user_id INTEGER UNIQUE NOT NULL,
            email VARCHAR(255) NOT NULL,
            username VARCHAR(100),
            display_name VARCHAR(255),
            roles JSONB,
            capabilities JSONB,
            wp_token TEXT,
            wp_token_expires VARCHAR(50),
            last_login TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        "api_usage": """
        CREATE TABLE api_usage (
            id SERIAL PRIMARY KEY,
            wp_user_id INTEGER REFERENCES wp_users(wp_user_id),
            email VARCHAR(255) NOT NULL,
            queries INTEGER DEFAULT 0,
            last_query TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        "query_history": """
        CREATE TABLE query_history (
            id SERIAL PRIMARY KEY,
            wp_user_id INTEGER REFERENCES wp_users(wp_user_id),
            email VARCHAR(255) NOT NULL,
            query_type VARCHAR(100),
            query_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        "wc_orders": """
        CREATE TABLE wc_orders (
            id SERIAL PRIMARY KEY,
            wc_order_id INTEGER UNIQUE NOT NULL,
            wp_user_id INTEGER REFERENCES wp_users(wp_user_id),
            wc_customer_id INTEGER,
            status VARCHAR(50),
            total DECIMAL(10,2),
            subtotal DECIMAL(10,2),
            tax_total DECIMAL(10,2),
            currency VARCHAR(10),
            date_created TIMESTAMP WITH TIME ZONE,
            date_completed TIMESTAMP WITH TIME ZONE,
            product_count INTEGER,
            product_names JSONB,
            billing_email VARCHAR(255),
            billing_phone VARCHAR(50),
            shipping_method VARCHAR(255),
            payment_method VARCHAR(255),
            synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        "wc_products": """
        CREATE TABLE wc_products (
            id SERIAL PRIMARY KEY,
            wc_product_id INTEGER UNIQUE NOT NULL,
            name VARCHAR(255),
            slug VARCHAR(255),
            status VARCHAR(50),
            type VARCHAR(50),
            description TEXT,
            short_description TEXT,
            sku VARCHAR(100),
            price DECIMAL(10,2),
            regular_price DECIMAL(10,2),
            sale_price DECIMAL(10,2),
            stock_status VARCHAR(50),
            stock_quantity INTEGER,
            categories JSONB,
            tags JSONB,
            images JSONB,
            date_created TIMESTAMP WITH TIME ZONE,
            date_modified TIMESTAMP WITH TIME ZONE,
            synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
    }
    
    st.info("Database schemas defined. Please create these tables in your Supabase dashboard.")
    return schemas
