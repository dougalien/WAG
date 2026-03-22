import datetime
import requests
import streamlit as st

# ---------- Page & Theme ----------
st.set_page_config(
    page_title="WAG: Walks Are Good",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Dog‑friendly, color‑blind‑sensitive theme using CSS
st.markdown(
    """
    <style>
    :root {
        /* Main colors: blue + gold (good for most color blindness),
           plus a soft warm background and clear accents. */
        --wag-bg: #FFF8E7;        /* warm, soft background */
        --wag-primary: #1F7A8C;   /* teal‑blue for buttons/headers */
        --wag-secondary: #F4A259; /* golden orange accent */
        --wag-accent: #254441;    /* dark teal text/accent */
        --wag-text: #1F2421;      /* high‑contrast main text */
        --wag-muted: #5C6B73;     /* muted supporting text */
    }

    .main {
        background-color: var(--wag-bg);
    }

    /* Center and style the title block */
    .wag-title {
        text-align: center;
        padding: 0.5rem 0 0.25rem 0;
        color: var(--wag-accent);
        font-family: "Trebuchet MS", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .wag-subtitle {
        text-align: center;
        color: var(--wag-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Button styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, var(--wag-primary), var(--wag-secondary));
        color: white;
        border: none;
        border-radius: 999px;
        padding: 0.6rem 1.6rem;
        font-size: 1.05rem;
        font-weight: 600;
        font-family: "Trebuchet MS", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        cursor: pointer;
        transition: transform 0.05s ease-in-out, box-shadow 0.05s ease-in-out, filter 0.05s ease-in-out;
    }

    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        filter: brightness(1.03);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.20);
    }

    div.stButton > button:first-child:active {
        transform: translateY(0px);
        box-shadow: 0 3px 7px rgba(0, 0, 0, 0.18);
    }

    /* Card‑like container for results */
    .wag-card {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-top: 1.2rem;
        border: 1px solid rgba(31, 122, 140, 0.08);
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }

    .wag-card h3 {
        margin-top: 0;
        color: var(--wag-primary);
        font-family: "Trebuchet MS", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* Improve base text readability */
    .wag-body-text {
        color: var(--wag-text);
        font-size: 0.98rem;
        line-height: 1.5;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* Paw print separators */
    .wag-separator {
        text-align: center;
        color: var(--wag-secondary);
        font-size: 1.3rem;
        margin: 0.5rem 0 1.0rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- API Key (Perplexity only) ----------
PERPLEXITY_API_KEY = st.secrets["PERPLEXITY_API_KEY"]

# ---------- Perplexity (Sonar) Call ----------
def call_sonar_for_walk(user_input: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }

        current_datetime = datetime.datetime.now()

        messages = [
            {
                "role": "system",
                "content": (
                    f"The current date and time are: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
                    "Your specialty is to fetch tide information for Boston Harbor, MA and weather information for Salem, MA for the current day using web search.\n"
                    "In this app, if the word 'walk' is used in the input, always assume the user is asking for tide and weather data for the current day for Boston Harbor and Salem, MA.\n"
                    "Use https://www.usharbors.com/harbor/Massachusetts/Boston-Harbor-ma/tides for Boston Harbor tides and sunset time.\n\n"
                    "Step 1: Fetch and summarize today's tides (high/low and approximate times), sunset time in Boston Harbor, and weather (temperature in °F and conditions) in Salem, MA for each hour from now until 9 PM.\n"
                    "Step 2: Using those data, apply these dog-walk rules for Steve:\n"
                    "- If temperature ≤ 32°F: Forest Walk before sundown; Golf Course Walk after sundown; Stay Home if it is raining.\n"
                    "- If 32°F < temperature ≤ 60°F: Forest Walk before sundown; Golf Course Walk after sundown; Stay Home if it is raining.\n"
                    "- If temperature > 60°F: Swim Walk around high tide and good weather; Forest Walk around low tide; Stay Home any time it is raining.\n"
                    "Step 3: Create an hour-by-hour list from now until 9 PM. For each hour, include:\n"
                    "- Hour (12-hour format with am/pm)\n"
                    "- Recommended walk type (Forest Walk, Golf Course Walk, Swim Walk, or Stay Home)\n"
                    "- Temperature in °F\n"
                    "- Weather conditions\n"
                    "- Indication of high/low tide relevance if important.\n"
                    "Encourage a coat when it is below 32°F and a light when it is dark.\n"
                    "The dog's name is Steve. At the end of your response, wish Steve a fun walk.\n"
                    "If some data are approximate, clearly state that they are approximate but still provide your best walk recommendations.\n"
                ),
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        data = {
            "model": "sonar-pro",
            "messages": messages,
            "max_tokens": 1200,
        }

        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"API request failed: {e}"

# ---------- Streamlit UI ----------
st.markdown('<h1 class="wag-title">WAG: Walks Are Good 🐕</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="wag-subtitle">A dog-walking helper by We Are Dougalien — tuned for tides, weather, and Steve.</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="wag-separator">🐾 🦴 🐾</div>', unsafe_allow_html=True)

st.markdown(
    '<p class="wag-body-text">'
    "Press the button below to fetch today&apos;s tides and weather and get an hour‑by‑hour walk plan for Steve."
    "</p>",
    unsafe_allow_html=True,
)

if st.button("Let's Go For a Walk"):
    text = call_sonar_for_walk("walk")
    st.markdown(
        '<div class="wag-card"><h3>Walk plan for Steve</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="wag-body-text">{text}</div></div>',
        unsafe_allow_html=True,
    )
