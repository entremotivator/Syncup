import streamlit as st
import requests
import datetime
import pandas as pd
import plotly.express as px
from typing import List, Dict, Optional
from utils.wordpress_auth import supabase, wp_config

@st.cache_data(ttl=600, show_spinner=False)
def get_wc_customer_orders(wp_user_id: int) -> List[Dict]:
    """Get WooCommerce orders for a WordPress customer"""
    if not wp_config:
        st.error("WordPress configuration not available")
        return []

    # First, get the WooCommerce customer ID from WordPress user ID
    customer_id = get_wc_customer_id_from_wp_user(wp_user_id)
    if not customer_id:
        st.info("No WooCommerce customer found for this WordPress user")
        return []

    url = f"{wp_config['wp_url']}/wp-json/wc/v3/orders"
    params = {
        "customer": customer_id,
        "per_page": 100,
        "orderby": "date",
        "order": "desc"
    }

    try:
        resp = requests.get(
            url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params=params,
            timeout=15
        )

        if resp.status_code == 200:
            orders = resp.json()
            
            # Enrich order data and sync to Supabase
            enriched_orders = []
            for order in orders:
                enriched_order = enrich_order_data(order)
                enriched_orders.append(enriched_order)
                sync_order_to_supabase(enriched_order, wp_user_id)
            
            return enriched_orders
        else:
            st.error(f"WooCommerce API error: {resp.status_code} - {resp.text}")
            return []

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch WooCommerce orders: {e}")
        return []

def get_wc_customer_id_from_wp_user(wp_user_id: int) -> Optional[int]:
    """Get WooCommerce customer ID from WordPress user ID"""
    if not wp_config:
        return None

    url = f"{wp_config['wp_url']}/wp-json/wc/v3/customers"
    params = {
        "search": str(wp_user_id),
        "per_page": 1
    }

    try:
        resp = requests.get(
            url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params=params,
            timeout=10
        )

        if resp.status_code == 200:
            customers = resp.json()
            if customers:
                return customers[0]['id']
        
        # If not found by search, try to get by email from WordPress user
        wp_user = get_wp_user_by_id(wp_user_id)
        if wp_user and wp_user.get('email'):
            return get_wc_customer_by_email(wp_user['email'])
            
        return None

    except Exception as e:
        st.warning(f"Could not get WooCommerce customer ID: {e}")
        return None

def get_wp_user_by_id(wp_user_id: int) -> Optional[Dict]:
    """Get WordPress user by ID"""
    if not wp_config:
        return None

    url = f"{wp_config['wp_url']}/wp-json/wp/v2/users/{wp_user_id}"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def get_wc_customer_by_email(email: str) -> Optional[int]:
    """Get WooCommerce customer ID by email"""
    if not wp_config:
        return None

    url = f"{wp_config['wp_url']}/wp-json/wc/v3/customers"
    params = {
        "email": email,
        "per_page": 1
    }

    try:
        resp = requests.get(
            url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params=params,
            timeout=10
        )

        if resp.status_code == 200:
            customers = resp.json()
            return customers[0]['id'] if customers else None
        return None

    except Exception as e:
        st.warning(f"Could not get customer by email: {e}")
        return None

def enrich_order_data(order: Dict) -> Dict:
    """Enrich order data with calculated fields"""
    order['total_float'] = float(order.get('total', 0))
    order['subtotal_float'] = float(order.get('subtotal', 0))
    order['tax_total_float'] = float(order.get('total_tax', 0))
    
    # Parse dates
    if order.get('date_created'):
        order['date_created_parsed'] = datetime.datetime.fromisoformat(
            order['date_created'].replace('T', ' ').replace('Z', '')
        )
    
    if order.get('date_completed'):
        order['date_completed_parsed'] = datetime.datetime.fromisoformat(
            order['date_completed'].replace('T', ' ').replace('Z', '')
        )
    
    # Extract product information
    order['product_count'] = len(order.get('line_items', []))
    order['product_names'] = [item.get('name', '') for item in order.get('line_items', [])]
    
    return order

def sync_order_to_supabase(order: Dict, wp_user_id: int):
    """Sync WooCommerce order to Supabase"""
    if not supabase:
        return

    try:
        order_data = {
            "wc_order_id": order['id'],
            "wp_user_id": wp_user_id,
            "wc_customer_id": order.get('customer_id'),
            "status": order.get('status'),
            "total": order['total_float'],
            "subtotal": order['subtotal_float'],
            "tax_total": order['tax_total_float'],
            "currency": order.get('currency'),
            "date_created": order.get('date_created'),
            "date_completed": order.get('date_completed'),
            "product_count": order['product_count'],
            "product_names": order['product_names'],
            "billing_email": order.get('billing', {}).get('email'),
            "billing_phone": order.get('billing', {}).get('phone'),
            "shipping_method": order.get('shipping_lines', [{}])[0].get('method_title') if order.get('shipping_lines') else None,
            "payment_method": order.get('payment_method_title'),
            "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # Check if order already exists
        existing = supabase.table("wc_orders").select("wc_order_id").eq("wc_order_id", order['id']).execute()
        
        if existing.data:
            # Update existing order
            supabase.table("wc_orders").update(order_data).eq("wc_order_id", order['id']).execute()
        else:
            # Insert new order
            supabase.table("wc_orders").insert(order_data).execute()

    except Exception as e:
        st.warning(f"Failed to sync order {order.get('id')} to Supabase: {e}")

@st.cache_data(ttl=1800, show_spinner=False)
def get_wc_products() -> List[Dict]:
    """Get WooCommerce products and sync to Supabase"""
    if not wp_config:
        return []

    url = f"{wp_config['wp_url']}/wp-json/wc/v3/products"
    params = {
        "per_page": 100,
        "status": "publish"
    }

    try:
        resp = requests.get(
            url,
            auth=(wp_config['wc_key'], wp_config['wc_secret']),
            params=params,
            timeout=15
        )

        if resp.status_code == 200:
            products = resp.json()
            
            # Sync products to Supabase
            for product in products:
                sync_product_to_supabase(product)
            
            return products
        else:
            st.error(f"WooCommerce Products API error: {resp.status_code}")
            return []

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch WooCommerce products: {e}")
        return []

def sync_product_to_supabase(product: Dict):
    """Sync WooCommerce product to Supabase"""
    if not supabase:
        return

    try:
        product_data = {
            "wc_product_id": product['id'],
            "name": product.get('name'),
            "slug": product.get('slug'),
            "status": product.get('status'),
            "type": product.get('type'),
            "description": product.get('description'),
            "short_description": product.get('short_description'),
            "sku": product.get('sku'),
            "price": float(product.get('price', 0)),
            "regular_price": float(product.get('regular_price', 0)),
            "sale_price": float(product.get('sale_price', 0)) if product.get('sale_price') else None,
            "stock_status": product.get('stock_status'),
            "stock_quantity": product.get('stock_quantity'),
            "categories": [cat.get('name') for cat in product.get('categories', [])],
            "tags": [tag.get('name') for tag in product.get('tags', [])],
            "images": [img.get('src') for img in product.get('images', [])],
            "date_created": product.get('date_created'),
            "date_modified": product.get('date_modified'),
            "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        # Check if product already exists
        existing = supabase.table("wc_products").select("wc_product_id").eq("wc_product_id", product['id']).execute()
        
        if existing.data:
            # Update existing product
            supabase.table("wc_products").update(product_data).eq("wc_product_id", product['id']).execute()
        else:
            # Insert new product
            supabase.table("wc_products").insert(product_data).execute()

    except Exception as e:
        st.warning(f"Failed to sync product {product.get('id')} to Supabase: {e}")

def display_orders_analytics(orders: List[Dict]):
    """Display comprehensive order analytics"""
    if not orders:
        st.info("📦 No orders found")
        return
        
    # Convert to DataFrame for analysis
    df = pd.DataFrame(orders)
    df['month'] = pd.to_datetime(df['date_created']).dt.to_period('M')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completed_orders = len([o for o in orders if o['status'] == 'completed'])
        st.metric(
            "Total Orders", 
            len(orders),
            delta=f"{completed_orders} completed"
        )
    
    with col2:
        total_value = sum(o['total_float'] for o in orders)
        st.metric("Total Value", f"${total_value:,.2f}")
    
    with col3:
        avg_order = total_value / len(orders) if orders else 0
        st.metric("Average Order", f"${avg_order:,.2f}")
    
    with col4:
        recent_orders = len([o for o in orders if 
            o.get('date_created_parsed') and 
            o['date_created_parsed'] > datetime.datetime.now() - datetime.timedelta(days=30)
        ])
        st.metric("Recent Orders (30d)", recent_orders)
    
    # Order trend chart
    if len(orders) > 1:
        monthly_data = df.groupby('month').agg({
            'id': 'count',
            'total_float': 'sum'
        }).reset_index()
        monthly_data['month_str'] = monthly_data['month'].astype(str)
        
        fig = px.line(
            monthly_data, 
            x='month_str', 
            y=['id', 'total_float'],
            title="📈 Order Trends Over Time",
            labels={'value': 'Count/Amount', 'month_str': 'Month'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Order status breakdown
    status_counts = df['status'].value_counts()
    if len(status_counts) > 1:
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="📊 Order Status Distribution"
        )
        st.plotly_chart(fig_status, use_container_width=True)

def get_user_orders_from_supabase(wp_user_id: int) -> List[Dict]:
    """Get user orders from Supabase cache"""
    if not supabase:
        return []

    try:
        result = supabase.table("wc_orders").select("*").eq("wp_user_id", wp_user_id).order("date_created", desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        st.warning(f"Failed to get orders from Supabase: {e}")
        return []

