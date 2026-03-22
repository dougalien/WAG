import os
import time
import logging
import datetime
import requests

import streamlit as st

# ---------- Setup & config ----------

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

PERPLEXITY_API_KEY = st.secrets["PERPLEXITY_API_KEY"]

LAST_WALK_FILE = "last_walk.txt"

# Single model for everything
PPLX_MODEL = "sonar-pro"


def save_last_walk_timestamp(ts):
    """Persist last walk time as a simple float (epoch seconds)."""
    try:
        with open(LAST_WALK_FILE, "w") as f:
            f.write(str(ts))
    except OSError as e:
        logging.error(f"Could not save last walk timestamp: {e}")


def load_last_walk_timestamp():
    """Load last walk time; returns float or None."""
    if not os.path.exists(LAST_WALK_FILE):
        return None
    try:
        with open(LAST_WALK_FILE, "r") as f:
            return float(f.read().strip())
    except (OSError, ValueError) as e:
        logging.error(f"Could not read last walk timestamp: {e}")
        return None


def format_elapsed_since(ts):
    if ts is None:
        return "No walk logged yet."
    seconds = time.time() - ts
    if seconds < 0:
        return "Time data not available."
    minutes = int(seconds // 60)
    hours = minutes // 60
    minutes = minutes % 60
    if hours == 0 and minutes == 0:
        return "Just now."
    if hours == 0:
        return f"{minutes} minute(s) ago."
    return f"{hours} hour(s) {minutes} minute(s) ago."


def call_sonar_pro_for_walk():
    """
    Single Sonar-pro call that:
    - fetches tide + weather info
    - builds the hour-by-hour walk plan for Steve
    """
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }

        current_datetime = datetime.datetime.now()

        system_prompt = (
            "You are Stevie's dedicated dog-walking assistant.\n\n"
            "Your tasks in this app are:\n"
            "1) Fetch tide information for Boston Harbor, MA and weather information for Salem, MA "
            "   for the current day, using web search when needed.\n"
            "2) Use that information to plan Stevie's dog walks in Salem, MA.\n\n"
            "TIDES & WEATHER REQUIREMENTS:\n"
            "- Make sure your tide and weather data are correct by finding corroborating data.\n"
            "- Include the time of the input in your reasoning.\n"
            "- The following URL has tide and sunset data for the month at Boston Harbor:\n"
            "  https://www.usharbors.com/harbor/Massachusetts/Boston-Harbor-ma/tides\n"
            "- Create a table with:\n"
            "  • A column of hour of the day in 12-hour format\n"
            "  • A row for sunset time\n"
            "  • A row for temperature in degrees F\n"
            "  • A row for weather conditions\n"
            "  • A row indicating high and low tide.\n\n"
            "WALK PLANNING RULES (ALWAYS SALEM, MA):\n"
            f"- The current date and time are: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}.\n"
            "- Determine the accurate time of sun-up and sun-down in Salem, MA.\n"
            "- Use sun-up and sun-down to decide if it is light or dark each hour.\n"
            "- Consider Stevie's walk length is about one hour.\n"
            "- Apply these rules:\n"
            "  • If temperature is 32 F or below: Forest Walk before sun‑down; Golf Course Walk after "
            "sun‑down; Stay Home if raining.\n"
            "  • If temperature is between 32 F and 60 F: Forest Walk before sun‑down; Golf Course Walk "
            "after sun‑down; Stay Home if raining.\n"
            "  • If temperature is above 60 F: Swim Walk around high tide and good weather; Forest Walk "
            "around low tide; Stay Home any time it is raining.\n"
            "- Provide a brief hour‑by‑hour list from the time of input until 9 PM.\n"
            "  For each hour, include: walk type, temperature, and weather.\n"
            "- Encourage a coat when it is below 32 F and a light when it is dark.\n"
            "- The dog's name is Steve. Wish him a fun walk at the end of your response.\n\n"
            "OUTPUT FORMAT:\n"
            "1) A short natural‑language summary of today's conditions for Stevie.\n"
            "2) A tide + weather table as described.\n"
            "3) An hour‑by‑hour walk plan for Steve from now until 9 PM, clearly labeled.\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "walk"},
        ]

        data = {
            "model": PPLX_MODEL,
            "messages": messages,
        }

        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data,
            timeout=90,
        )
        if response.status_code == 400:
            try:
                logging.error(f"400 error body: {response.json()}")
            except Exception:
                logging.error(f"400 error raw text: {response.text}")
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        logging.error(f"Perplexity/Sonar-pro request failed: {e}")
        return f"API request failed: {e}"


# ---------- Streamlit UI ----------

st.set_page_config(
    page_title="WAG",
    page_icon="🐕",
    layout="centered",
)

st.markdown(
    """
    <style>
    body {
        background: radial-gradient(circle at top, #fff7e6 0%, #ffe5f1 45%, #e6f7ff 100%);
    }
    .main {
        background-color: rgba(255, 255, 255, 0.9);
        padding-top: 1rem;
        padding-bottom: 2rem;
        border-radius: 16px;
    }
    h1 {
        color: #ff6b6b;
        letter-spacing: 0.06em;
    }
    h2, h3, h4 {
        color: #0b4f6c;
    }
    .creator-tag {
        font-size: 0.8rem;
        color: #777;
        margin-top: -0.4rem;
        margin-bottom: 0.6rem;
    }
    button[kind="primary"] {
        padding: 0.9rem 1.3rem;
        font-size: 1.15rem;
        border-radius: 999px;
        background: linear-gradient(90deg, #ff9f1c, #ffbf69);
        border: none;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(90deg, #ff8c00, #ffb347);
    }
    .big-text {
        font-size: 1.05rem;
        line-height: 1.4;
    }
    .since-walk {
        font-size: 0.95rem;
        color: #444;
        margin-top: 0.25rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("WAG")
st.markdown("<div class='creator-tag'>by We Are Dougalien</div>", unsafe_allow_html=True)
st.subheader("Stevie's Walk Buddy")

# Time since last walk
last_ts = load_last_walk_timestamp()
elapsed_text = format_elapsed_since(last_ts)
st.markdown(
    f"<div class='since-walk'>Time since Stevie's last walk: <b>{elapsed_text}</b></div>",
    unsafe_allow_html=True,
)

if st.button("🐾 Start Stevie's Walk", use_container_width=True):
    with st.spinner("Checking tides, weather, and planning Stevie's walk..."):
        now_ts = time.time()
        save_last_walk_timestamp(now_ts)

        result = call_sonar_pro_for_walk()

    st.markdown("### Stevie's Walk Plan")
    st.markdown(result, unsafe_allow_html=False)

st.write(
    "<div class='big-text'>Tap the paw whenever you are thinking about a walk. "
    "We will look at tides in Boston Harbor and weather in Salem, then lay out "
    "Stevie's options hour by hour.</div>",
    unsafe_allow_html=True,
)
