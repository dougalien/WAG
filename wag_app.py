import datetime
import math
import requests
import streamlit as st

# ---------- Page & Theme ----------
st.set_page_config(
    page_title="WAG: Walks Are Good created by We are dougalien (www.dougalien.com)",
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

# ---------- Fixed Locations ----------
BOSTON_LAT = 42.35
BOSTON_LON = -71.05  # Boston Harbor


# ---------- Time helpers ----------
def get_today_range():
    now = datetime.datetime.now()
    start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
    end = start + datetime.timedelta(days=1)
    return start, end


# ---------- WorldTides (real tides) ----------
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


# ---------- Approximate weather model ----------
def approximate_weather_for_hour(t: datetime.datetime):
    hour = t.hour
    center = 15  # warmest ~3 PM
    span = 12
    diff = (hour - center) / span
    temp = 40 + 10 * math.cos(diff * math.pi)  # 40±10°F

    if 16 <= hour <= 19:
        if datetime.datetime.now().day % 2 == 0:
            conditions = "Light rain"
            raining = True
        else:
            conditions = "Mostly cloudy"
            raining = False
    else:
        if 10 <= hour <= 15:
            conditions = "Partly cloudy"
        elif hour < 10:
            conditions = "Mostly cloudy"
        else:
            conditions = "Clear"
        raining = False

    return round(temp), conditions, raining


# ---------- Sunlight ----------
def estimate_sunset():
    now = datetime.datetime.now()
    return datetime.datetime(now.year, now.month, now.day, 18, 45, 0)  # ~6:45 PM


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
def summarize_with_perplexity(rows, sunset_dt, tides):
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

        tide_lines = []
        for ex in tides:
            tide_lines.append(
                f"{ex['time'].strftime('%-I:%M %p')}: {ex['type']} ({ex['height']} m)"
            )
        tide_summary = "\n".join(tide_lines) if tide_lines else "No tide data available."

        system_msg = (
            f"The current date and time are {now.strftime('%Y-%m-%d %H:%M')}.\n"
            f"Sunset time in Salem/Boston area is approximately {sunset_dt.strftime('%-I:%M %p')}.\n"
            "You are a friendly dog-walking assistant for Steve the dog.\n\n"
            "You are given:\n"
            "- Real tide extremes (high and low) for Boston Harbor, MA from WorldTides for today.\n"
            "- An hour-by-hour schedule that uses those real tides plus approximate weather for Salem, MA.\n\n"
            "DATA QUALITY RULES:\n"
            "- At the top of your response, include exactly this line (no more, no less):\n"
            "  'Data status: Real tides, approximate weather.'\n"
            "- Do NOT complain about missing live weather data or search results.\n"
            "- Treat the provided schedule as the working basis for planning.\n\n"
            "Your job:\n"
            "- Write a short, friendly paragraph (3–5 sentences) explaining:\n"
            "  * The best 1–2 windows for a walk today and what kind of walk (Forest / Golf Course / Swim) is best.\n"
            "  * Any simple precautions (coat if below freezing, light if dark, avoid rain hours).\n"
            "- Then add a brief bullet list summarizing 2–4 recommended hours and walk types.\n"
            "- End by wishing Steve a fun walk.\n"
        )

        user_text = (
            "Here are today's Boston Harbor tide extremes:\n"
            f"{tide_summary}\n\n"
            "Here is the hour-by-hour schedule (from now until 9 PM) with walk type, temperature, conditions, "
            "tide state, and light/dark:\n"
            f"{condensed}\n\n"
            "Please follow the instructions above."
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_text},
        ]

        data = {
            "model": "sonar-pro",
            "messages": messages,
            "max_tokens": 500,
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

    try:
        tides = get_tides_boston()
        tide_ok = True
        tide_error = ""
    except Exception as e:
        tides = []
        tide_ok = False
        tide_error = str(e)

    if not tide_ok:
        return None, None, None, [f"Tide data error: {tide_error}"]

    sunset_dt = estimate_sunset()

    rows = []
    end_limit = today_end.replace(hour=21, minute=0, second=0)
    t = now.replace(minute=0, second=0, microsecond=0)
    while t <= end_limit:
        temp, conditions, raining = approximate_weather_for_hour(t)
        ts_state = tide_state_for_time(tides, t)
        dark = is_dark(t, sunset_dt)
        walk_type = classify_walk(temp, raining, ts_state, dark)

        try:
            hour_label = t.strftime("%-I %p")
        except ValueError:
            hour_label = t.strftime("%I %p")

        rows.append(
            {
                "dt": t,
                "hour_label": hour_label,
                "temp": temp,
                "conditions": conditions,
                "tide_state": ts_state,
                "dark": dark,
                "walk_type": walk_type,
            }
        )

        t += datetime.timedelta(hours=1)

    return rows, sunset_dt, tides, None


# ---------- UI ----------
st.markdown('<h1 class="wag-title">WAG: Walks Are Good 🐕</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="wag-subtitle">'
    "A dog-walking helper by We Are Dougalien — real tides, approximate weather for now."
    "</div>",
    unsafe_allow_html=True,
)
st.markdown('<div class="wag-separator">🐾 🦴 🐾</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="wag-body-text">'
    "Press the button below to fetch today&apos;s Boston Harbor tides, approximate Salem weather, "
    "and get an hour‑by‑hour walk plan for Steve."
    "</p>",
    unsafe_allow_html=True,
)

if st.button("Let&apos;s Go For a Walk"):
    rows, sunset_dt, tides, errors = plan_walk()

    if errors:
        st.markdown('<div class="wag-card"><h3>Data status</h3>', unsafe_allow_html=True)
        st.markdown(
            '<div class="wag-body-text">'
            "Sorry, I couldn&apos;t fetch the tide data I need right now.<br>"
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
        summary = summarize_with_perplexity(rows, sunset_dt, tides)

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
