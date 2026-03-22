import datetime
import requests
import streamlit as st

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
st.title("WAG: Walks ARE GOOD")
st.write("by We Are Dougalien")
st.write("Press the button to plan Steve's walk using tides and weather from Perplexity Sonar.")

if st.button("Let's Go For a Walk"):
    text = call_sonar_for_walk("walk")
    st.subheader("Walk plan for Steve")
    st.write(text)
