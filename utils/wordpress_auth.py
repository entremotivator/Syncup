import streamlit as st
import requests
import datetime
from typing import Optional, Dict
from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    """Initialize Supabase client with caching"""
    try:
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["anon_key"]
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {e}")
        return None

@st.cache_data(ttl=3600)
def get_wp_config():
    """Get WordPress configuration with error handling"""
    try:
        return {
            "wp_url": st.secrets["wordpress"]["base_url"],
            "wp_user": st.secrets["wordpress"]["username"],
            "wp_pass": st.secrets["wordpress"]["password"],
            "wc_key": st.secrets["woocommerce"]["consumer_key"],
            "wc_secret": st.secrets["woocommerce"]["consumer_secret"],
        }
    except Exception as e:
        st.error(f"WordPress configuration error: {e}")
        return None

supabase = init_supabase()
wp_config = get_wp_config()

def wp_jwt_login(username: str, password: str) -> Optional[Dict]:
    """WordPress JWT authentication with Supabase sync"""
    if not wp_config:
        st.error("WordPress configuration not available")
        return None

    url = f"{wp_config['wp_url']}/wp-json/jwt-auth/v1/token"

    try:
        with st.spinner("Authenticating with WordPress..."):
            resp = requests.post(
                url,
                data={"username": username, "password": password},
                timeout=10
            )

        if resp.status_code == 200:
            token_data = resp.json()

            # Fetch user details from WordPress
            me_url = f"{wp_config['wp_url']}/wp-json/wp/v2/users/me"
            me_resp = requests.get(
                me_url,
                headers={"Authorization": f"Bearer {token_data['token']}"},
                timeout=10
            )

            if me_resp.status_code == 200:
                user_info = me_resp.json()
                
                # Prepare user data for Supabase sync
                user_data = {
                    "wp_user_id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "username": user_info.get("username", token_data.get("user_nicename")),
                    "display_name": user_info.get("name"),
                    "wp_token": token_data['token'],
                    "wp_token_expires": token_data.get('expires', ''),
                    "last_login": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "roles": user_info.get("roles", []),
                    "capabilities": user_info.get("capabilities", {})
                }
                
                # Sync user to Supabase
                sync_result = sync_wp_user_to_supabase(user_data)
                if sync_result:
                    # Store in session state
                    st.session_state.user = {
                        "id": user_data["wp_user_id"],
                        "email": user_data["email"],
                        "username": user_data["username"],
                        "display_name": user_data["display_name"],
                        "wp_token": user_data["wp_token"]
                    }
                    st.session_state.wp_token = user_data["wp_token"]
                    return user_data
                else:
                    st.error("Failed to sync user data")
                    return None
            else:
                st.error(f"Could not fetch WordPress user info: {me_resp.text}")
                return None

        else:
            error_msg = resp.json().get('message', resp.text) if resp.text else 'Unknown error'
            st.error(f"WordPress login failed: {error_msg}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def sync_wp_user_to_supabase(user_data: Dict) -> bool:
    """Sync WordPress user data to Supabase"""
    if not supabase:
        st.error("Supabase not available")
        return False

    try:
        # Check if user exists in Supabase
        existing_user = supabase.table("wp_users").select("*").eq("wp_user_id", user_data["wp_user_id"]).execute()
        
        if existing_user.data:
            # Update existing user
            result = supabase.table("wp_users").update({
                "email": user_data["email"],
                "username": user_data["username"],
                "display_name": user_data["display_name"],
                "last_login": user_data["last_login"],
                "roles": user_data["roles"],
                "capabilities": user_data["capabilities"],
                "wp_token": user_data["wp_token"],
                "wp_token_expires": user_data["wp_token_expires"]
            }).eq("wp_user_id", user_data["wp_user_id"]).execute()
        else:
            # Insert new user
            result = supabase.table("wp_users").insert({
                "wp_user_id": user_data["wp_user_id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "display_name": user_data["display_name"],
                "last_login": user_data["last_login"],
                "roles": user_data["roles"],
                "capabilities": user_data["capabilities"],
                "wp_token": user_data["wp_token"],
                "wp_token_expires": user_data["wp_token_expires"],
                "created_at": user_data["last_login"]
            }).execute()

        # Initialize usage tracking if new user
        if not existing_user.data:
            initialize_user_usage_tracking(user_data["wp_user_id"], user_data["email"])

        return True

    except Exception as e:
        st.error(f"Failed to sync user to Supabase: {e}")
        return False

def initialize_user_usage_tracking(wp_user_id: int, email: str):
    """Initialize usage tracking for WordPress user in Supabase"""
    if not supabase:
        return

    try:
        supabase.table("api_usage").insert({
            "wp_user_id": wp_user_id,
            "email": email,
            "queries": 0,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"Failed to initialize usage tracking: {e}")

def get_wp_user_from_supabase(wp_user_id: int) -> Optional[Dict]:
    """Get WordPress user data from Supabase"""
    if not supabase:
        return None

    try:
        result = supabase.table("wp_users").select("*").eq("wp_user_id", wp_user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Failed to get user from Supabase: {e}")
        return None

def validate_wp_token(token: str) -> bool:
    """Validate WordPress JWT token"""
    if not wp_config or not token:
        return False

    try:
        validate_url = f"{wp_config['wp_url']}/wp-json/jwt-auth/v1/token/validate"
        resp = requests.post(
            validate_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        return resp.status_code == 200
    except:
        return False

