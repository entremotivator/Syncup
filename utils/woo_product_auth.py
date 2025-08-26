import streamlit as st
import requests
from typing import Optional, Dict, List
from utils.wordpress_auth import supabase, wp_config

def get_user_purchased_products(email: str) -> List[Dict]:
    """Get products purchased by user email"""
    if not wp_config:
        return []

    try:
        # First, find customer by email
        customers_url = f"{wp_config['wp_url']}/wp-json/wc/v3/customers"
        customers_resp = requests.get(
            customers_url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params={"email": email, "per_page": 1},
            timeout=10
        )

        if customers_resp.status_code != 200 or not customers_resp.json():
            return []

        customer = customers_resp.json()[0]
        customer_id = customer['id']

        # Get customer orders
        orders_url = f"{wp_config['wp_url']}/wp-json/wc/v3/orders"
        orders_resp = requests.get(
            orders_url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params={
                "customer": customer_id,
                "status": "completed",
                "per_page": 100
            },
            timeout=15
        )

        if orders_resp.status_code != 200:
            return []

        orders = orders_resp.json()
        
        # Extract unique products from completed orders
        purchased_products = []
        product_ids = set()
        
        for order in orders:
            for item in order.get('line_items', []):
                product_id = item.get('product_id')
                if product_id and product_id not in product_ids:
                    product_ids.add(product_id)
                    purchased_products.append({
                        'product_id': product_id,
                        'name': item.get('name'),
                        'quantity': item.get('quantity', 1),
                        'total': item.get('total', '0'),
                        'order_id': order.get('id'),
                        'order_date': order.get('date_created')
                    })

        return purchased_products

    except Exception as e:
        st.error(f"Error fetching purchased products: {e}")
        return []

def check_product_access(email: str, required_product_ids: List[int] = None) -> bool:
    """Check if user has purchased required products for access"""
    purchased_products = get_user_purchased_products(email)
    
    if not purchased_products:
        return False
    
    # If no specific products required, any purchase grants access
    if not required_product_ids:
        return True
    
    # Check if user has purchased any of the required products
    purchased_ids = [p['product_id'] for p in purchased_products]
    return any(pid in purchased_ids for pid in required_product_ids)

def get_wc_product_details(product_id: int) -> Optional[Dict]:
    """Get WooCommerce product details"""
    if not wp_config:
        return None

    try:
        product_url = f"{wp_config['wp_url']}/wp-json/wc/v3/products/{product_id}"
        resp = requests.get(
            product_url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            timeout=10
        )

        if resp.status_code == 200:
            return resp.json()
        return None

    except Exception as e:
        st.warning(f"Could not fetch product details: {e}")
        return None

def woo_product_login(email: str, password: str) -> Optional[Dict]:
    """Login using WooCommerce product purchases + WordPress auth"""
    if not wp_config:
        st.error("WordPress configuration not available")
        return None

    # First authenticate with WordPress
    wp_url = f"{wp_config['wp_url']}/wp-json/jwt-auth/v1/token"
    
    try:
        # Try WordPress authentication first
        wp_resp = requests.post(
            wp_url,
            data={"username": email, "password": password},
            timeout=10
        )

        if wp_resp.status_code == 200:
            wp_token_data = wp_resp.json()
            
            # Get WordPress user details
            me_url = f"{wp_config['wp_url']}/wp-json/wp/v2/users/me"
            me_resp = requests.get(
                me_url,
                headers={"Authorization": f"Bearer {wp_token_data['token']}"},
                timeout=10
            )

            if me_resp.status_code == 200:
                wp_user = me_resp.json()
                user_email = wp_user.get('email', email)
                
                # Check WooCommerce product purchases
                purchased_products = get_user_purchased_products(user_email)
                
                if not purchased_products:
                    st.error("🛒 No product purchases found. Please purchase a product to access the application.")
                    return None
                
                # Create user data with product information
                user_data = {
                    "wp_user_id": wp_user.get("id"),
                    "email": user_email,
                    "username": wp_user.get("username", wp_token_data.get("user_nicename")),
                    "display_name": wp_user.get("name"),
                    "wp_token": wp_token_data['token'],
                    "purchased_products": purchased_products,
                    "product_access": True,
                    "roles": wp_user.get("roles", []),
                    "capabilities": wp_user.get("capabilities", {})
                }
                
                # Sync to Supabase with product info
                sync_result = sync_woo_product_user(user_data)
                if sync_result:
                    return user_data
                else:
                    st.error("Failed to sync user data")
                    return None
            else:
                st.error("Could not fetch WordPress user info")
                return None
        else:
            # If WordPress auth fails, try WooCommerce customer login
            return woo_customer_login(email, password)

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def woo_customer_login(email: str, password: str) -> Optional[Dict]:
    """Alternative login using WooCommerce customer data"""
    if not wp_config:
        return None

    try:
        # Check if customer exists with purchases
        purchased_products = get_user_purchased_products(email)
        
        if not purchased_products:
            st.error("🛒 No product purchases found for this email. Please purchase a product to access the application.")
            return None

        # Get customer details
        customers_url = f"{wp_config['wp_url']}/wp-json/wc/v3/customers"
        customers_resp = requests.get(
            customers_url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params={"email": email, "per_page": 1},
            timeout=10
        )

        if customers_resp.status_code == 200 and customers_resp.json():
            customer = customers_resp.json()[0]
            
            # Create user data based on WooCommerce customer + products
            user_data = {
                "wc_customer_id": customer['id'],
                "email": email,
                "username": customer.get('username', email.split('@')[0]),
                "display_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or email,
                "purchased_products": purchased_products,
                "product_access": True,
                "customer_data": customer
            }
            
            # Sync to Supabase
            sync_result = sync_woo_product_user(user_data)
            if sync_result:
                return user_data
        
        st.error("Customer authentication failed")
        return None

    except Exception as e:
        st.error(f"WooCommerce customer login error: {e}")
        return None

def sync_woo_product_user(user_data: Dict) -> bool:
    """Sync WooCommerce product user to Supabase"""
    if not supabase:
        return False

    try:
        # Prepare user data for Supabase
        supabase_data = {
            "wp_user_id": user_data.get("wp_user_id"),
            "wc_customer_id": user_data.get("wc_customer_id"),
            "email": user_data["email"],
            "username": user_data["username"],
            "display_name": user_data["display_name"],
            "purchased_products": user_data["purchased_products"],
            "product_access": user_data["product_access"],
            "last_login": st.session_state.get('current_time', 'now()'),
            "roles": user_data.get("roles", []),
            "capabilities": user_data.get("capabilities", {}),
            "wp_token": user_data.get("wp_token"),
            "customer_data": user_data.get("customer_data")
        }

        # Check if user exists
        identifier = user_data.get("wp_user_id") or user_data.get("wc_customer_id") or user_data["email"]
        
        if user_data.get("wp_user_id"):
            existing = supabase.table("wp_users").select("*").eq("wp_user_id", user_data["wp_user_id"]).execute()
        elif user_data.get("wc_customer_id"):
            existing = supabase.table("wp_users").select("*").eq("wc_customer_id", user_data["wc_customer_id"]).execute()
        else:
            existing = supabase.table("wp_users").select("*").eq("email", user_data["email"]).execute()

        if existing.data:
            # Update existing user
            if user_data.get("wp_user_id"):
                supabase.table("wp_users").update(supabase_data).eq("wp_user_id", user_data["wp_user_id"]).execute()
            elif user_data.get("wc_customer_id"):
                supabase.table("wp_users").update(supabase_data).eq("wc_customer_id", user_data["wc_customer_id"]).execute()
            else:
                supabase.table("wp_users").update(supabase_data).eq("email", user_data["email"]).execute()
        else:
            # Insert new user
            supabase_data["created_at"] = st.session_state.get('current_time', 'now()')
            supabase.table("wp_users").insert(supabase_data).execute()

        # Initialize usage tracking
        from utils.database import initialize_user_usage
        user_id = user_data.get("wp_user_id") or user_data.get("wc_customer_id") or hash(user_data["email"])
        initialize_user_usage(user_id, user_data["email"])

        return True

    except Exception as e:
        st.error(f"Failed to sync WooCommerce product user: {e}")
        return False

def get_user_product_access_level(email: str) -> Dict:
    """Get user's product access level and permissions"""
    purchased_products = get_user_purchased_products(email)
    
    if not purchased_products:
        return {"access_level": "none", "products": [], "permissions": []}
    
    # Define product-based access levels (customize as needed)
    access_levels = {
        "basic": {"min_products": 1, "permissions": ["property_search"]},
        "premium": {"min_products": 3, "permissions": ["property_search", "analytics", "export"]},
        "enterprise": {"min_products": 5, "permissions": ["property_search", "analytics", "export", "api_access"]}
    }
    
    product_count = len(purchased_products)
    total_spent = sum(float(p.get('total', 0)) for p in purchased_products)
    
    # Determine access level
    if product_count >= 5:
        level = "enterprise"
    elif product_count >= 3:
        level = "premium"
    elif product_count >= 1:
        level = "basic"
    else:
        level = "none"
    
    return {
        "access_level": level,
        "products": purchased_products,
        "product_count": product_count,
        "total_spent": total_spent,
        "permissions": access_levels.get(level, {}).get("permissions", [])
    }
