import streamlit as st
import requests
import os
from datetime import datetime
import math

# =========================================
# CONFIG
# =========================================

st.set_page_config(page_title="WAG", layout="wide")

MAPBOX_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
WORLDTIDES_URL = "https://www.worldtides.info/api/v3"

# =========================================
# SECRETS
# =========================================

def get_secret(name):
    try:
        return st.secrets[name]
    except:
        return os.getenv(name)

APP_PASSWORD = get_secret("APP_PASSWORD")
OPENAI_KEY = get_secret("OPENAI_API_KEY")
MAPBOX_KEY = get_secret("MAPBOX_API_KEY")
WORLDTIDES_KEY = get_secret("WORLDTIDES_API_KEY")

# =========================================
# STATE
# =========================================

if "auth" not in st.session_state:
    st.session_state.auth = False
if "lat" not in st.session_state:
    st.session_state.lat = None
if "lon" not in st.session_state:
    st.session_state.lon = None
if "location_name" not in st.session_state:
    st.session_state.location_name = ""
if "recommendation" not in st.session_state:
    st.session_state.recommendation = ""

# =========================================
# LOGIN
# =========================================

def login():
    st.title("WAG")
    st.markdown("**W**alk **A**dvice **G**uide by We are dougalien")

    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == APP_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Incorrect password")

# =========================================
# MAPBOX FUNCTIONS
# =========================================

def reverse_geocode(lat, lon):
    url = f"{MAPBOX_URL}/{lon},{lat}.json"
    params = {"access_token": MAPBOX_KEY}
    r = requests.get(url, params=params).json()
    try:
        return r["features"][0]["place_name"]
    except:
        return "Unknown location"

def search_places(lat, lon, query="park"):
    url = f"{MAPBOX_URL}/{query}.json"
    params = {
        "proximity": f"{lon},{lat}",
        "limit": 5,
        "access_token": MAPBOX_KEY
    }
    r = requests.get(url, params=params).json()

    results = []
    for f in r.get("features", []):
        results.append({
            "name": f["place_name"],
            "lat": f["center"][1],
            "lon": f["center"][0]
        })
    return results

# =========================================
# TIDES
# =========================================

def get_tide(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "key": WORLDTIDES_KEY,
        "length": 3600
    }
    r = requests.get(WORLDTIDES_URL, params=params).json()
    try:
        return r["heights"][0]["height"]
    except:
        return None

# =========================================
# DISTANCE
# =========================================

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)

# =========================================
# OPENAI RECOMMENDATION
# =========================================

def get_recommendation(place, tide):
    prompt = f"""
You are a dog walking assistant.

Location: {st.session_state.location_name}
Place: {place['name']}
Tide: {tide}

Give:
- best walk suggestion
- why it fits
- simple instructions
- backup option

Keep it short.
"""

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data
    )

    return r.json()["choices"][0]["message"]["content"]

# =========================================
# MAIN APP
# =========================================

def app():

    st.title("WAG")
    st.markdown("**W**alk **A**dvice **G**uide by We are dougalien")

    # ---------------------------
    # Location
    # ---------------------------
    st.header("1. Location")

if st.button("Use My Location"):
    loc = get_geolocation()

    if loc and "lat" in loc:
        st.session_state.lat = loc["lat"]
        st.session_state.lon = loc["lon"]

        st.session_state.location_name = reverse_geocode(
            st.session_state.lat,
            st.session_state.lon
        )

    elif loc and "error" in loc:
        st.error(f"Location error: {loc['error']}")

if st.session_state.location_name:
    st.success(st.session_state.location_name)

    # ---------------------------
    # Walk Style
    # ---------------------------
    st.header("2. Walk Type")

    walk_type = st.selectbox(
        "Choose walk",
        ["Best Walk", "Woods", "Beach", "Quick"]
    )

    # ---------------------------
    # Recommendation
    # ---------------------------
    st.header("3. Recommendation")

    if st.button("Find Walk"):

        if st.session_state.lat is None:
            st.warning("Set location first")
            return

        query = "park"
        if walk_type == "Beach":
            query = "beach"

        places = search_places(
            st.session_state.lat,
            st.session_state.lon,
            query
        )

        if not places:
            st.error("No places found")
            return

        best = places[0]

        tide = get_tide(
            st.session_state.lat,
            st.session_state.lon
        )

        rec = get_recommendation(best, tide)

        st.session_state.recommendation = rec

    if st.session_state.recommendation:
        st.markdown("### WAG Recommendation")
        st.write(st.session_state.recommendation)

        st.map([{
            "lat": st.session_state.lat,
            "lon": st.session_state.lon
        }])

# =========================================
# RUN
# =========================================

if not st.session_state.auth:
    login()
else:
    app()