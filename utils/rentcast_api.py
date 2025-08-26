# =====================================================
# utils/rentcast_api.py
# =====================================================

import streamlit as st
import requests
from utils.database import get_user_usage, increment_usage

# RentCast API configuration
RENTCAST_API_KEY = st.secrets["rentcast"]["api_key"]
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"
MAX_QUERIES = 30


def check_query_limit(user_id, email):
    """
    Check if user has exceeded query limit.
    Returns True if under limit, False if limit reached.
    """
    usage = get_user_usage(user_id, email)
    return usage < MAX_QUERIES


def fetch_property_details(address, user_id, email):
    """
    Fetch property details from RentCast API.
    Returns JSON data if successful, None if error or limit reached.
    """
    if not check_query_limit(user_id, email):
        st.error("You have reached your 30 API query limit.")
        return None

    headers = {
        "accept": "application/json",
        "X-Api-Key": RENTCAST_API_KEY
    }
    params = {"address": address}

    try:
        response = requests.get(f"{RENTCAST_BASE_URL}/properties", headers=headers, params=params)
        if response.status_code == 200:
            increment_usage(user_id, email)
            return response.json()
        else:
            st.error(f"Error fetching data from RentCast API. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
        return None


def get_market_data(address, user_id, email):
    """
    Fetch market data from RentCast API.
    Returns JSON data if successful, None if error or limit reached.
    """
    if not check_query_limit(user_id, email):
        st.error("You have reached your 30 API query limit.")
        return None

    headers = {
        "accept": "application/json",
        "X-Api-Key": RENTCAST_API_KEY
    }
    params = {"address": address}

    try:
        response = requests.get(f"{RENTCAST_BASE_URL}/markets", headers=headers, params=params)
        if response.status_code == 200:
            increment_usage(user_id, email)
            return response.json()
        else:
            st.error(f"Error fetching market data. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
        return None
