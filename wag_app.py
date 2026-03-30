import os
import math
import html
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from streamlit_current_location import current_position

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="WAG", layout="wide")

MAPBOX_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
WORLDTIDES_URL = "https://www.worldtides.info/api/v3"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# =========================================================
# SECRETS
# =========================================================

def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

APP_PASSWORD = get_secret("APP_PASSWORD")
OPENAI_KEY = get_secret("OPENAI_API_KEY")
MAPBOX_KEY = get_secret("MAPBOX_API_KEY")
WORLDTIDES_KEY = get_secret("WORLDTIDES_API_KEY")
ANTHROPIC_KEY = get_secret("ANTHROPIC_API_KEY")
PERPLEXITY_KEY = get_secret("PERPLEXITY_API_KEY")

# =========================================================
# STATE
# =========================================================

def init_state():
    defaults = {
        "authenticated": False,
        "login_error": "",
        "dog_name": "Stevie",
        "dog_age": "",
        "dog_size": "Medium",
        "energy_level": "Moderate",
        "heat_tolerance": "Moderate",
        "cold_tolerance": "Moderate",
        "swimming_ok": "No",
        "crowd_sensitivity": "Moderate",
        "preferred_walk_length": "30 minutes",
        "lat": None,
        "lon": None,
        "location_name": "",
        "location_error": "",
        "manual_place": "",
        "walk_style": "Best Walk Now",
        "candidate_places": [],
        "top_places": [],
        "selected_place": None,
        "tide_data": None,
        "recommendation": "",
        "backup_plan": "",
        "audio_text": "",
        "raw_location_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================================================
# STYLES
# =========================================================

st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px;
    color: #111111;
}
.stApp {
    background: #F5F7FA;
}
.main-card {
    background: #FFFFFF;
    border: 1px solid #D0D6DE;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.input-box {
    background: #EEF4FB;
    border: 1px solid #C7D9ED;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.output-box {
    background: #F3F8F1;
    border: 1px solid #C9DCC4;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.alt-box {
    background: #FFF8EE;
    border: 1px solid #EAD4B0;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.section-label {
    font-size: 1.06rem;
    font-weight: 700;
    margin-bottom: 0.7rem;
}
.box-label {
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 0.45rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.brand-line {
    font-size: 1.02rem;
    color: #222222;
    margin-top: -0.15rem;
}
.brand-link {
    color: #2B5C88;
    font-size: 0.95rem;
    margin-top: 0.2rem;
}
.small-note {
    color: #4E5966;
    font-size: 0.95rem;
}
div.stButton > button {
    min-height: 48px;
    border-radius: 10px;
    font-weight: 650;
    border: 1px solid #BEC8D4;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea, input {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================

def display_name():
    return st.session_state.dog_name.strip() or "Your dog"

def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def safe_lower(text):
    return (text or "").lower()

def audio_button(text_to_speak: str):
    safe_text = html.escape(text_to_speak).replace("\n", " ")
    st.components.v1.html(
        f"""
        <button
            onclick="window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance('{safe_text}'));"
            style="
              background:#1f1f1f;
              color:white;
              border:none;
              padding:0.75rem 1rem;
              border-radius:10px;
              cursor:pointer;
              font-size:14px;
              font-weight:600;
              width:100%;
            ">
            Play Audio
        </button>
        """,
        height=60,
    )

# =========================================================
# LOGIN
# =========================================================

def render_login():
    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.markdown("""
        <div class="main-card" style="margin-top:3rem;">
            <div class="section-label">1. Sign In</div>
            <h1 style="margin-bottom:0.1rem;">WAG</h1>
            <div class="brand-line"><strong>W</strong>alk <strong>A</strong>dvice <strong>G</strong>uide by We are dougalien</div>
            <div class="brand-link">www.dougalien.com</div>
            <p class="small-note" style="margin-top:0.8rem;">
                Enter the app password to continue.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            pw = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Enter", use_container_width=True)

        if submitted:
            if not APP_PASSWORD:
                st.session_state.login_error = "APP_PASSWORD is missing from secrets."
            elif pw == APP_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.login_error = ""
                st.rerun()
            else:
                st.session_state.login_error = "Incorrect password."

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

# =========================================================
# MAPBOX
# =========================================================

def reverse_geocode(lat, lon):
    url = f"{MAPBOX_URL}/{lon},{lat}.json"
    params = {"access_token": MAPBOX_KEY, "limit": 1}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    features = data.get("features", [])
    if not features:
        return "Unknown location"
    return features[0]["place_name"]

def geocode_place(place_text):
    url = f"{MAPBOX_URL}/{place_text}.json"
    params = {
        "access_token": MAPBOX_KEY,
        "limit": 1
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    features = data.get("features", [])
    if not features:
        return None

    feature = features[0]
    lon, lat = feature["center"]
    return {
        "lat": lat,
        "lon": lon,
        "place_name": feature["place_name"]
    }

def mapbox_search(query, lat, lon, limit=8):
    url = f"{MAPBOX_URL}/{query}.json"
    params = {
        "proximity": f"{lon},{lat}",
        "limit": limit,
        "access_token": MAPBOX_KEY
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = []
    for f in data.get("features", []):
        try:
            plon, plat = f["center"]
            name = f["place_name"]
            results.append({
                "name": name,
                "lat": plat,
                "lon": plon,
                "distance_miles": round(haversine_miles(lat, lon, plat, plon), 2),
                "text": f.get("text", ""),
                "place_type": f.get("place_type", []),
                "raw": f
            })
        except Exception:
            continue
    return results

def walk_queries(style):
    mapping = {
        "Best Walk Now": ["park", "trail", "beach"],
        "Quick Walk": ["park", "green", "trail"],
        "Woods Walk": ["forest", "woods", "trail", "reservation", "park"],
        "Quiet Walk": ["trail", "reservation", "conservation", "park"],
        "Training Walk": ["park", "field", "common"],
        "Water Walk": ["pond", "lake", "river", "beach"],
        "Beach Walk": ["beach", "shore", "harbor", "point"],
    }
    return mapping.get(style, ["park", "trail"])

def gather_candidates(lat, lon, style):
    seen = {}
    results = []

    for q in walk_queries(style):
        for item in mapbox_search(q, lat, lon, limit=6):
            key = (round(item["lat"], 5), round(item["lon"], 5), item["name"])
            if key not in seen:
                seen[key] = True
                results.append(item)

    return results

# =========================================================
# WORLD TIDES
# =========================================================

def get_tide_data(lat, lon):
    if not WORLDTIDES_KEY:
        return None

    params = {
        "lat": lat,
        "lon": lon,
        "key": WORLDTIDES_KEY,
        "heights": 1,
        "extremes": 1,
        "length": 86400
    }

    r = requests.get(WORLDTIDES_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    height = None
    extreme_type = None
    extreme_time = None

    heights = data.get("heights", [])
    if heights:
        height = heights[0].get("height")

    extremes = data.get("extremes", [])
    if extremes:
        extreme_type = extremes[0].get("type")
        extreme_time = extremes[0].get("date")

    return {
        "height": height,
        "extreme_type": extreme_type,
        "extreme_time": extreme_time
    }

# =========================================================
# SCORING
# =========================================================

def score_place(place, style):
    name = safe_lower(place["name"])
    score = 100

    score -= place["distance_miles"] * 12

    if style == "Quick Walk":
        score -= place["distance_miles"] * 10
    if style == "Woods Walk":
        if any(k in name for k in ["woods", "forest", "trail", "reservation", "conservation"]):
            score += 24
        if "beach" in name:
            score -= 10
    if style == "Quiet Walk":
        if any(k in name for k in ["reservation", "conservation", "trail", "meadow"]):
            score += 18
        if any(k in name for k in ["common", "downtown", "harbor"]):
            score -= 8
    if style == "Training Walk":
        if any(k in name for k in ["field", "common", "park"]):
            score += 16
        if any(k in name for k in ["woods", "forest"]):
            score -= 4
    if style == "Water Walk":
        if any(k in name for k in ["beach", "shore", "river", "pond", "lake", "harbor"]):
            score += 22
    if style == "Beach Walk":
        if any(k in name for k in ["beach", "shore", "harbor", "point"]):
            score += 28
        else:
            score -= 14
    if style == "Best Walk Now":
        if any(k in name for k in ["park", "trail", "reservation", "conservation"]):
            score += 12

    if st.session_state.crowd_sensitivity == "High":
        if any(k in name for k in ["common", "harbor", "downtown"]):
            score -= 10
        if any(k in name for k in ["trail", "reservation", "conservation"]):
            score += 8

    if st.session_state.swimming_ok == "No":
        if style in ["Beach Walk", "Water Walk"]:
            score -= 4

    if st.session_state.preferred_walk_length == "15 minutes":
        score -= place["distance_miles"] * 8
    elif st.session_state.preferred_walk_length == "60 minutes":
        if any(k in name for k in ["trail", "reservation", "forest", "woods"]):
            score += 8

    return round(score, 2)

def rank_candidates(candidates, style):
    ranked = []
    for place in candidates:
        p = dict(place)
        p["score"] = score_place(p, style)
        ranked.append(p)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:3]

# =========================================================
# OPENAI
# =========================================================

def build_ai_prompt(top_places, tide_data):
    place_lines = []
    for i, p in enumerate(top_places, start=1):
        place_lines.append(
            f"{i}. {p['name']} | distance {p['distance_miles']} miles | score {p['score']}"
        )

    tide_text = "No tide data used."
    if tide_data:
        tide_text = (
            f"Current tide height: {tide_data.get('height')}. "
            f"Next extreme: {tide_data.get('extreme_type')} at {tide_data.get('extreme_time')}."
        )

    return f"""
Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Current location: {st.session_state.location_name}
Dog name: {display_name()}
Dog age: {st.session_state.dog_age or "[not provided]"}
Dog size: {st.session_state.dog_size}
Energy level: {st.session_state.energy_level}
Heat tolerance: {st.session_state.heat_tolerance}
Cold tolerance: {st.session_state.cold_tolerance}
Swimming okay: {st.session_state.swimming_ok}
Crowd sensitivity: {st.session_state.crowd_sensitivity}
Preferred walk length: {st.session_state.preferred_walk_length}
Requested walk style: {st.session_state.walk_style}

Top candidate places:
{chr(10).join(place_lines)}

Tide context:
{tide_text}

Choose the best option and explain why.
Also give one backup option.
Keep it concise and phone-friendly.
"""

def get_openai_recommendation(top_places, tide_data):
    if not OPENAI_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY.")

    payload = {
        "model": "gpt-4o",
        "temperature": 0.3,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise, practical, mobile-first dog walk planner."
            },
            {
                "role": "user",
                "content": build_ai_prompt(top_places, tide_data)
            }
        ]
    }

    r = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# =========================================================
# UI SECTIONS
# =========================================================

def render_header():
    st.markdown("""
    <div class="main-card">
        <h1 style="margin-bottom:0.1rem;">WAG</h1>
        <div class="brand-line"><strong>W</strong>alk <strong>A</strong>dvice <strong>G</strong>uide by We are dougalien</div>
        <div class="brand-link">www.dougalien.com</div>
    </div>
    """, unsafe_allow_html=True)

def render_dog_profile():
    st.markdown('<div class="section-label">1. Dog Profile</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.dog_name = st.text_input("Dog name", value=st.session_state.dog_name)
        st.session_state.dog_age = st.text_input("Dog age", value=st.session_state.dog_age, placeholder="Optional")
        st.session_state.dog_size = st.selectbox("Dog size", ["Small", "Medium", "Large"], index=["Small", "Medium", "Large"].index(st.session_state.dog_size))
        st.session_state.energy_level = st.selectbox("Energy level", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(st.session_state.energy_level))
    with c2:
        st.session_state.heat_tolerance = st.selectbox("Heat tolerance", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(st.session_state.heat_tolerance))
        st.session_state.cold_tolerance = st.selectbox("Cold tolerance", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(st.session_state.cold_tolerance))
        st.session_state.swimming_ok = st.selectbox("Swimming okay", ["No", "Yes"], index=["No", "Yes"].index(st.session_state.swimming_ok))
        st.session_state.crowd_sensitivity = st.selectbox("Crowd sensitivity", ["Low", "Moderate", "High"], index=["Low", "Moderate", "High"].index(st.session_state.crowd_sensitivity))

    st.session_state.preferred_walk_length = st.selectbox(
        "Preferred walk length",
        ["15 minutes", "30 minutes", "45 minutes", "60 minutes"],
        index=["15 minutes", "30 minutes", "45 minutes", "60 minutes"].index(st.session_state.preferred_walk_length)
    )

def render_location():
    st.markdown('<div class="section-label">2. Location</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="main-card">
        <div class="small-note">
            This app works best with phone location or a street address.
            You can use your phone's current location or enter a street address, city and state, or a place name.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Use My Location", use_container_width=True):
        pos = current_position()
        st.session_state.raw_location_result = pos

        if isinstance(pos, dict):
            lat = pos.get("latitude")
            lon = pos.get("longitude")

            if lat is not None and lon is not None:
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.location_error = ""
                try:
                    st.session_state.location_name = reverse_geocode(lat, lon)
                except Exception as e:
                    st.session_state.location_error = f"Reverse geocode error: {e}"
            else:
                st.session_state.location_error = "Location returned, but coordinates were missing."
        else:
            st.session_state.location_error = "No location returned. You can enter an address below."

    st.session_state.manual_place = st.text_input(
        "Or enter street address, city, and state",
        value=st.session_state.manual_place,
        placeholder="12 Maple St, Salem, MA"
    )

    if st.button("Use Entered Address", use_container_width=True):
        if not st.session_state.manual_place.strip():
            st.warning("Enter an address, city and state, or place name first.")
        else:
            try:
                result = geocode_place(st.session_state.manual_place.strip())
                if result:
                    st.session_state.lat = result["lat"]
                    st.session_state.lon = result["lon"]
                    st.session_state.location_name = result["place_name"]
                    st.session_state.location_error = ""
                else:
                    st.session_state.location_error = "Place not found."
            except Exception as e:
                st.session_state.location_error = f"Place lookup error: {e}"

    if st.session_state.location_name:
        st.success(f"Using location: {st.session_state.location_name}")

    if st.session_state.location_error:
        st.error(st.session_state.location_error)

def render_walk_style():
    st.markdown('<div class="section-label">3. Walk Style</div>', unsafe_allow_html=True)

    styles = [
        "Best Walk Now",
        "Quick Walk",
        "Woods Walk",
        "Quiet Walk",
        "Training Walk",
        "Water Walk",
        "Beach Walk"
    ]

    st.session_state.walk_style = st.radio(
        "Choose walk style",
        styles,
        index=styles.index(st.session_state.walk_style)
    )

def render_find_button():
    st.markdown('<div class="section-label">4. Recommendation</div>', unsafe_allow_html=True)

    if st.button("Find Best Walk", use_container_width=True):
        if st.session_state.lat is None or st.session_state.lon is None:
            st.warning("Use phone location or enter a place first.")
            st.stop()

        try:
            candidates = gather_candidates(
                st.session_state.lat,
                st.session_state.lon,
                st.session_state.walk_style
            )

            if not candidates:
                st.error("No nearby walk options were found.")
                st.stop()

            st.session_state.candidate_places = candidates
            st.session_state.top_places = rank_candidates(candidates, st.session_state.walk_style)
            st.session_state.selected_place = st.session_state.top_places[0]

            tide_data = None
            if st.session_state.walk_style in ["Beach Walk", "Water Walk"]:
                tide_data = get_tide_data(
                    st.session_state.selected_place["lat"],
                    st.session_state.selected_place["lon"]
                )

            st.session_state.tide_data = tide_data
            st.session_state.recommendation = get_openai_recommendation(st.session_state.top_places, tide_data)

            if tide_data:
                st.session_state.backup_plan = (
                    f"Tide context used: {tide_data.get('extreme_type')} at {tide_data.get('extreme_time')}."
                )
            else:
                st.session_state.backup_plan = "No tide adjustment was needed for this recommendation."

            st.session_state.audio_text = st.session_state.recommendation

        except Exception as e:
            st.error(f"Recommendation error: {e}")

def render_result():
    if not st.session_state.recommendation:
        return

    best = st.session_state.selected_place
    st.markdown('<div class="section-label">5. Result</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="input-box">
        <div class="box-label">{display_name()}</div>
        <div>Walk style: {st.session_state.walk_style}</div>
        <div style="margin-top:0.45rem;">Current location: {st.session_state.location_name}</div>
    </div>
    """, unsafe_allow_html=True)

    tide_line = ""
    if st.session_state.tide_data:
        tide_line = (
            f"<div style='margin-top:0.45rem;'><strong>Tide:</strong> "
            f"{st.session_state.tide_data.get('height')} "
            f"({st.session_state.tide_data.get('extreme_type')} at {st.session_state.tide_data.get('extreme_time')})</div>"
        )

    st.markdown(f"""
    <div class="output-box">
        <div class="box-label">WAG</div>
        <div><strong>Suggested place:</strong> {best['name']}</div>
        <div style="margin-top:0.45rem;"><strong>Distance:</strong> {best['distance_miles']} miles</div>
        <div style="margin-top:0.45rem;"><strong>Score:</strong> {best['score']}</div>
        {tide_line}
        <div style="margin-top:0.75rem;"><strong>Recommendation:</strong></div>
        <div style="margin-top:0.45rem;">{st.session_state.recommendation}</div>
    </div>
    """, unsafe_allow_html=True)

def render_top_options():
    if not st.session_state.top_places:
        return

    st.markdown('<div class="section-label">6. Top Options</div>', unsafe_allow_html=True)

    for i, place in enumerate(st.session_state.top_places, start=1):
        box_class = "output-box" if i == 1 else "alt-box"
        st.markdown(f"""
        <div class="{box_class}">
            <div class="box-label">Option {i}</div>
            <div><strong>{place['name']}</strong></div>
            <div style="margin-top:0.35rem;">Distance: {place['distance_miles']} miles</div>
            <div style="margin-top:0.35rem;">Score: {place['score']}</div>
        </div>
        """, unsafe_allow_html=True)

def render_map():
    if not st.session_state.selected_place or st.session_state.lat is None:
        return

    st.markdown('<div class="section-label">7. Map</div>', unsafe_allow_html=True)

    df = pd.DataFrame([
        {"lat": st.session_state.lat, "lon": st.session_state.lon},
        {"lat": st.session_state.selected_place["lat"], "lon": st.session_state.selected_place["lon"]},
    ])
    st.map(df)

def render_audio():
    if not st.session_state.audio_text:
        return

    st.markdown('<div class="section-label">8. Optional Audio</div>', unsafe_allow_html=True)
    audio_button(st.session_state.audio_text)

def render_dev_tools():
    st.markdown('<div class="section-label">9. Developer Tools</div>', unsafe_allow_html=True)

    with st.expander("Open developer tools", expanded=False):
        st.write("Raw location result:")
        raw_result = st.session_state.raw_location_result
        if isinstance(raw_result, (dict, list)):
            st.json(raw_result)
        elif raw_result is None:
            st.write("No location result yet.")
        else:
            st.code(str(raw_result))

        if st.session_state.top_places:
            st.write("Ranked places:")
            st.json(st.session_state.top_places)
        else:
            st.write("No ranked places yet.")

# =========================================================
# MAIN
# =========================================================

if not st.session_state.authenticated:
    render_login()
    st.stop()

render_header()
render_dog_profile()
render_location()
render_walk_style()
render_find_button()
render_result()
render_top_options()
render_map()
render_audio()
render_dev_tools()