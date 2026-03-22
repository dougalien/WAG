import datetime
import math
import requests
import streamlit as st

# ---------- Page & Theme ----------
st.set_page_config(
    page_title="WAG: Walks Are Good",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --wag-bg: #FFF8E7;
        --wag-primary: #1F7A8C;
        --wag-secondary: #F4A259;
        --wag-accent: #254441;
        --wag-text: #1F2421;
        --wag-muted: #5C6B73;
    }

    .main {
        background-color: var(--wag-bg);
    }

    .wag-title {
        text-align: center;
        padding-top: 0.5rem;
        padding-bottom: 0.25rem;
        color: var(--wag-accent);
        font-family: "Trebuchet MS", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .wag-subtitle {
        text-align: center;
        color: var(--wag-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    .wag-separator {
        text-align: center;
        color: var(--wag-secondary);
        font-size: 1.3rem;
        margin: 0.5rem 0 1.0rem 0;
    }

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

    .wag-body-text {
        color: var(--wag-text);
        font-size: 0.95rem;
        line-height: 1.5;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    table.wag-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    table.wag-table th,
    table.wag-table td {
        border: 1px solid rgba(37, 68, 65, 0.15);
        padding: 0.35rem 0.4rem;
        text-align: center;
    }

    table.wag-table th {
        background-color: rgba(31, 122, 140, 0.12);
        color: var(--wag-accent);
    }

    table.wag-table tr:nth-child(even) {
        background-color: rgba(255, 248, 231, 0.7);
    }

    table.wag-table tr:nth-child(odd) {
        background-color: #FFFFFF;
    }

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- API Keys from Streamlit secrets ----------
PERPLEXITY_API_KEY = st.secrets["PERPLEXITY_API_KEY"]
WORLDTIDES_API_KEY = st.secrets["WORLDTIDES_API_KEY"]
OPENWEATHERMAP_API_KEY = st.secrets["OPENWEATHERMAP_API_KEY"]

# ---------- Fixed Locations ----------
# Boston Harbor approx
BOSTON_LAT = 42.35
BOSTON_LON = -71.05
# Salem, MA
SALEM_LAT = 42.52
SALEM_LON = -70.90


# ---------- Time helpers ----------
def get_today_range():
    now = datetime.datetime.now()
    start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    end = start + datetime.timedelta(days=1)
    return start, end


# ---------- WorldTides ----------
def get_tides_boston():
    start, end = get_today_range()
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    url = (
        "https://www.worldtides.info/api/v3"
        f"?extremes&lat={BOSTON_LAT}&lon={BOSTON_LON}"
        f"&start={start_ts}&end={end_ts}&key={WORLDTIDES_API_KEY}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    extremes = data.get("extremes", [])
    tides = []
    for ex in extremes:
        ts = datetime.datetime.fromtimestamp(ex["dt"])
        tides.append(
            {
                "time": ts,
                "type": ex.get("type", ""),
                "height": ex.get("height"),
            }
        )
    return tides


def tide_state_for_time(tides, t, window_hours=1.5):
    if not tides:
        return "Unknown"
    closest = min(tides, key=lambda ex: abs((ex["time"] - t).total_seconds()))
    diff_hours = abs((closest["time"] - t).total_seconds()) / 3600.0
    if diff_hours <= window_hours:
        if "High" in closest["type"]:
            return "High tide"
        if "Low" in closest["type"]:
            return "Low tide"
    return "Mid tide"


# ---------- OpenWeatherMap ----------
def get_hourly_weather_salem():
    """
    Uses OpenWeather One Call 3.0 hourly forecast for Salem, MA.
    If your account only supports 2.5, change '3.0' to '2.5' below.
    """
    url = (
        "https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={SALEM_LAT}&lon={SALEM_LON}"
        "&exclude=current,minutely,daily,alerts"
        f"&appid={OPENWEATHERMAP_API_KEY}&units=imperial"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("hourly", [])


# ---------- Sunlight ----------
def estimate_sunset():
    now = datetime.datetime.now()
    # Simple fixed ~6:45 PM local
    return datetime.datetime(now.year, now.month, now.day, 18, 45, 0)


def is_dark(hour_dt, sunset_dt):
    return hour_dt > sunset_dt


# ---------- Walk rules ----------
def classify_walk(temp_f, is_raining, tide_state, dark):
    if is_raining:
        return "Stay Home"

    if temp_f <= 32:
        return "Forest Walk" if not dark else "Golf Course Walk"
    elif 32 < temp_f <= 60:
        return "Forest Walk" if not dark else "Golf Course Walk"
    else:
        if "High" in tide_state:
            return "Swim Walk"
        elif "Low" in tide_state:
            return "Forest Walk"
        else:
            return "Forest Walk"


# ---------- Perplexity summary ----------
def summarize_with_perplexity(rows, sunset_dt):
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }

        now = datetime.datetime.now()

        lines = []
        for r in rows:
            lines.append(
                f"{r['hour_label']}: {r['walk_type']}, "
                f"{r['temp']}°F, {r['conditions']}, {r['tide_state']}, "
                f"{'dark' if r['dark'] else 'light'}"
            )
        condensed = "\n".join(lines)

        system_msg = (
            f"The current date and time are {now.strftime('%Y-%m-%d %H:%M')}.\n"
            f"Sunset time in Salem/Boston area is approximately {sunset_dt.strftime('%-I:%M %p')}.\n"
            "You are a friendly dog-walking assistant for Steve the dog.\n"
            "You have been given an hour-by-hour schedule with recommended walk type, "
            "temperature, conditions, tide state, and whether it is light or dark.\n"
            "Write a short, friendly paragraph (3–5 sentences) explaining:\n"
            "- The best 1–2 windows for a walk today and what kind of walk (Forest / Golf Course / Swim) is best.\n"
            "- Any simple precautions (coat if below freezing, light if dark).\n"
            "End by wishing Steve a fun walk.\n"
            "Do NOT complain about missing live data or search results. Assume the schedule you receive is correct.\n"
        )

        messages = [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": (
                    "Here is the schedule:\n"
                    f"{condensed}\n\n"
                    "Please follow the instructions above."
                ),
            },
        ]

        data = {
            "model": "sonar-pro",
            "messages": messages,
            "max_tokens": 400,
        }

        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data,
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(Could not get summary from Perplexity: {e})"


# ---------- Main walk planning ----------
def plan_walk():
    now = datetime.datetime.now()
    today_start, today_end = get_today_range()

    # Tides
    try:
        tides = get_tides_boston()
        tide_ok = True
        tide_error = ""
    except Exception as e:
        tides = []
        tide_ok = False
        tide_error = str(e)

    # Weather
    try:
        hourly = get_hourly_weather_salem()
        weather_ok = True
        weather_error = ""
    except Exception as e:
        hourly = []
        weather_ok = False
        weather_error = str(e)

    errors = []
    if not tide_ok:
        errors.append(f"Tide data error: {tide_error}")
    if not weather_ok:
        errors.append(f"Weather data error: {weather_error}")
    if errors:
        return None, None, errors

    sunset_dt = estimate_sunset()

    rows = []
    end_limit = today_end.replace(hour=21, minute=0, second=0)
    for h in hourly:
        t = datetime.datetime.fromtimestamp(h["dt"])
        if t < now or t > end_limit:
            continue

        temp = round(h.get("temp", 0))
        weather_desc = h.get("weather", [{}])[0].get("description", "").capitalize()

        rain = False
        if "rain" in weather_desc.lower() or "drizzle" in weather_desc.lower():
            rain = True
        if h.get("rain"):
            rain = True

        ts_state = tide_state_for_time(tides, t)
        dark = is_dark(t, sunset_dt)
        walk_type = classify_walk(temp, rain, ts_state, dark)

        try:
            hour_label = t.strftime("%-I %p")
        except ValueError:
            hour_label = t.strftime("%I %p")

        rows.append(
            {
                "dt": t,
                "hour_label": hour_label,
                "temp": temp,
                "conditions": weather_desc,
                "tide_state": ts_state,
                "dark": dark,
                "walk_type": walk_type,
            }
        )

    return rows, sunset_dt, None


# ---------- UI ----------
st.markdown('<h1 class="wag-title">WAG: Walks Are Good 🐕</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="wag-subtitle">A dog-walking helper by We Are Dougalien — using real tides and weather.</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="wag-separator">🐾 🦴 🐾</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="wag-body-text">'
    "Press the button below to fetch today&apos;s Boston Harbor tides and Salem weather "
    "and get an hour‑by‑hour walk plan for Steve."
    "</p>",
    unsafe_allow_html=True,
)

if st.button("Let&apos;s Go For a Walk"):
    rows, sunset_dt, errors = plan_walk()

    if errors:
        st.markdown('<div class="wag-card"><h3>Data status</h3>', unsafe_allow_html=True)
        st.markdown(
            '<div class="wag-body-text">'
            "Sorry, I couldn&apos;t fetch all the live data I need right now.<br>"
            + "<br>".join(errors)
            + "</div></div>",
            unsafe_allow_html=True,
        )
    elif not rows:
        st.markdown('<div class="wag-card"><h3>Data status</h3>', unsafe_allow_html=True)
        st.markdown(
            '<div class="wag-body-text">'
            "No valid hours found for the rest of today. Try again earlier in the day."
            "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        summary = summarize_with_perplexity(rows, sunset_dt)

        st.markdown(
            '<div class="wag-card"><h3>Walk summary for Steve</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="wag-body-text">{summary}</div></div>',
            unsafe_allow_html=True,
        )

        table_html = [
            '<table class="wag-table">',
            "<tr>",
            "<th>Hour</th>",
            "<th>Walk type</th>",
            "<th>Temp (°F)</th>",
            "<th>Conditions</th>",
            "<th>Tide</th>",
            "<th>Light/Dark</th>",
            "</tr>",
        ]
        for r in rows:
            table_html.append(
                "<tr>"
                f"<td>{r['hour_label']}</td>"
                f"<td>{r['walk_type']}</td>"
                f"<td>{r['temp']}</td>"
                f"<td>{r['conditions']}</td>"
                f"<td>{r['tide_state']}</td>"
                f"<td>{'Dark' if r['dark'] else 'Light'}</td>"
                "</tr>"
            )
        table_html.append("</table>")
        table_html_str = "\n".join(table_html)

        st.markdown(
            '<div class="wag-card"><h3>Hour‑by‑hour walk conditions</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(table_html_str, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
