import os
import time
import uuid
import logging
import sqlite3
import datetime
import requests
import streamlit as st

# ---------- Logging ----------
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------- API Key (Perplexity only) ----------
PERPLEXITY_API_KEY = st.secrets["PERPLEXITY_API_KEY"]

# ---------- User ID Management ----------
USER_ID_FILE = "user_id.txt"


def get_user_id():
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, "r") as f:
            return f.read().strip()
    else:
        user_id = str(uuid.uuid4())
        with open(USER_ID_FILE, "w") as f:
            f.write(user_id)
        return user_id


user_id = get_user_id()

# ---------- Database Operations ----------
def initialize_database():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp REAL
        )
        """
    )
    conn.commit()
    return conn, cursor


conn, cursor = initialize_database()


def add_to_chat_history(role, content):
    try:
        timestamp = time.time()
        cursor.execute(
            """
            INSERT INTO messages (user_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, role, content, timestamp),
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")


def get_chat_history():
    try:
        cursor.execute(
            """
            SELECT role, content FROM messages
            WHERE user_id = ?
            ORDER BY timestamp ASC
            """,
            (user_id,),
        )
        history = cursor.fetchall()
        return [{"role": role, "content": content} for role, content in history]
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return []

# ---------- Perplexity (Sonar) Call ----------
def call_sonar_for_walk(user_input: str) -> str:
    """
    Single Perplexity call that:
    - Fetches tide info for Boston Harbor, MA
    - Fetches weather for Salem, MA
    - Applies your walk rules for Steve
    - Produces the hour-by-hour walk plan
    This merges the old Perplexity + OpenAI steps into one.
    """
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
            "model": "sonar-pro",  # Sonar Pro model name for chat completions
            "messages": messages,
            "max_tokens": 1200,
        }

        response = requests.post(
            "https://api.perplexity.ai/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content
    except requests.exceptions.RequestException as e:
        logging.error(f"Perplexity API request failed: {e}")
        return f"API request failed: {e}"

# ---------- Core Walk Logic (Perplexity-only) ----------
def process_walk():
    user_input = "walk"

    # Include prior chat history if you want continuity
    history = get_chat_history()
    # We won't send full history to Perplexity here to keep it simple,
    # but you could prepend history as additional messages if desired.

    sonar_response = call_sonar_for_walk(user_input)

    add_to_chat_history("user", user_input)
    add_to_chat_history("assistant", sonar_response)

    st.subheader("Walk plan for Steve (Perplexity Sonar)")
    st.write(sonar_response)

# ---------- Streamlit UI ----------
st.title("We Are Dougalien - Stevie's Walk Buddy")
st.write("Press the button to plan Steve's walk using tides and weather from Perplexity Sonar.")

if st.button("Walk!"):
    process_walk()
