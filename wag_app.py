import os
import time
import uuid
import logging
import sqlite3
import datetime
import requests
import openai
import streamlit as st

# ---------- Logging ----------
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------- API Keys (from Streamlit secrets) ----------
openai.api_key = st.secrets["OPENAI_API_KEY"]
perplexity_api_key = st.secrets["PERPLEXITY_API_KEY"]

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

# ---------- Perplexity Call (same logic as WAG.py) ----------
def get_perplexity_response(user_input: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json",
        }

        current_datetime = datetime.datetime.now()

        data = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Your specialty is to fetch tide information for Boston Harbor, MA and weather information for Salem, MA for the current day. "
                        "In this app, if the word 'walk' is used in the input then always assume the user is asking for tide and weather data for the current day for Boston Harbor and Salem, MA. "
                        "Make sure your response is correct by finding corroborating data to support your response and please include the time of the input. "
                        "The following url has tide and sunset data for the month at Boston Harbor. https://www.usharbors.com/harbor/Massachusetts/Boston-Harbor-ma/tides. "
                        "Create a table with a column of hour of the day in the 12 hour format a row on sunset time and another row of temperature in degrees F, a row of an indication of the weather conditions and finally a row that indications of high and low tide."
                    ),
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ],
        }

        response = requests.post(
            "https://api.perplexity.ai/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"Perplexity API request failed: {e}")
        return f"API request failed: {e}"

# ---------- OpenAI Call (same logic as WAG.py) ----------
def get_openai_response(messages):
    try:
        logging.debug(f"Messages sent to OpenAI: {messages}")

        current_datetime = datetime.datetime.now()

        # Insert current date/time system message at the front
        messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    f"The current date and time are: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}."
                ),
            },
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        openai_response = response.choices[0].message.content.strip()
        logging.debug(f"OpenAI Response: {openai_response}")
        return openai_response
    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return f"API request failed: {e}"

# ---------- Core Walk Logic (adapted from WAG.py) ----------
def process_walk():
    user_input = "walk"

    # Perplexity: tide + weather for Boston Harbor / Salem
    perplexity_response = get_perplexity_response(user_input)

    # Show Perplexity response in Streamlit
    st.subheader("Perplexity Tide & Weather (Boston Harbor / Salem)")
    st.write(perplexity_response)

    # Store Perplexity response in history if you want it in context
    add_to_chat_history("assistant", perplexity_response)

    # Chat history from DB
    chat_history = get_chat_history()

    # OpenAI system instructions (same as original WAG.py)
    openai_messages = [
        {
            "role": "system",
            "content": (
                "Determine the accurate time in Salem, MA and the time of sun-up and sun-down. Always Salem, MA"
                "Use the time of sun-up and sun-down to determine light or dark and anticipate condition changes during the walk considering a length of about an hour. "
                "If the temperature is 32 F or below, it's time for a Forest Walk before sun-down and a Golf Course Walk after sun-down and Stay Home if it is raining. If the temperature is between 32 F and 60 F, it's time for a Forest walk before sun-down and a Golf Course walk after sun-down and Stay Home if it is raining. If it's above 60 F then a Swim Walk is around high tide and good weather, a Forest Walk is around low tide and Stay Home is any time it is raining. "
                "Always provide a brief hour by hour list from the time of input until 9 PM. Include the type of walk, the temperature, and the weather for each hour. "
                "The dog's name is Steve. Please wish him a fun walk at the end of your response. "
                "Assume the walk will take about an hour and always provide a list of dog walking conditions hour by hour, not just the current hour. Encourge a coat when it is below 32 F and a light when it is dark. "
            ),
        }
    ] + chat_history + [
        {
            "role": "user",
            "content": user_input,
        }
    ]

    if openai_messages:
        openai_response = get_openai_response(openai_messages)
        add_to_chat_history("assistant", openai_response)
        st.subheader("Walk Plan for Steve")
        st.write(openai_response)
    else:
        st.error("Error: No messages to send to OpenAI.")

# ---------- Streamlit UI ----------
st.title("We Are Dougalien - Stevie's Walk Buddy")

st.write("Press the button to plan Steve's walk based on current tides and weather.")

if st.button("Walk!"):
    process_walk()
