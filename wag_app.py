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
WORLDTIDES_API_KEY = st.secrets["WORLDTIDES_API_KEY"]
OPENWEATHERMAP_API_KEY = st.secrets["OPENWEATHERMAP_API_KEY"]

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
            "Your job is to help Steve the dog go for a walk today, using tides in Boston Harbor, MA and weather in Salem, MA.\n"
            "Use web search and, when available, sites like https://www.usharbors.com/harbor/Massachusetts/Boston-Harbor-ma/tides "
            "for Boston Harbor tides and sunset time, and reliable weather sources for Salem, MA.\n\n"
            "INSTRUCTIONS ABOUT DATA QUALITY:\n"
            "1) If you can find reasonably current tide and weather information for today:\n"
            "   - Begin the report with: 'Data status: Live-ish data found for today.'\n"
            "   - Then give a clear, simple report. You may still mark values as approximate if needed.\n"
            "2) If you cannot find reasonably current or detailed information and must rely mostly on typical patterns or older data:\n"
            "   - Begin the report with: 'Data status: Using approximate/typical conditions for this time of year.'\n"
            "   - Keep any explanation of limitations to 1–2 short sentences, then focus on practical recommendations.\n\n"
            "WALK PLANNING RULES FOR STEVE:\n"
            "- Treat the user input 'walk' as a request for tide and weather data for the current day for Boston Harbor and Salem, MA.\n"
            "- Summarize today's tides (approximate times of high and low) and sunset time, and weather (temperature in °F and conditions) "
            "for each hour from now until 9 PM, as precisely as available.\n"
            "- Apply these dog-walk rules:\n"
            "  * If temperature ≤ 32°F: Forest Walk before sundown; Golf Course Walk after sundown; Stay Home if it is raining.\n"
            "  * If 32°F < temperature ≤ 60°F: Forest Walk before sundown; Golf Course Walk after sundown; Stay Home if it is raining.\n"
            "  * If temperature > 60°F: Swim Walk around high tide and good weather; Forest Walk around low tide; Stay Home any time it is raining.\n"
            "- Create an hour-by-hour list from now until 9 PM. For each hour, include:\n"
            "  * Hour (12-hour format with am/pm)\n"
            "  * Recommended walk type (Forest Walk, Golf Course Walk, Swim Walk, or Stay Home)\n"
            "  * Temperature in °F\n"
            "  * Weather conditions\n"
            "  * Note high/low tide when relevant.\n"
            "- Encourage a coat when it is below 32°F and a light when it is dark.\n"
            "- The dog's name is Steve. End your response by wishing Steve a fun walk.\n"
            "Keep the overall response easy to read, like a friendly note to a human dog‑walker (not technical).\n"
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
