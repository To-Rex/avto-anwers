from pydub import AudioSegment
import speech_recognition as sr
import json
import os
import requests
import random
from pyrogram import Client, filters
import re
from connection import connect_db, add_working_count, backup_db_to_json
import time
import difflib
import asyncio

API_ID = 24325110
API_HASH = '09c12098a3e94010de9988e3168ced9e'
GEMINI_API_KEY = 'AIzaSyCJd31hmAHHPom3ou7KNaDl2LQnbkEF5cQ'
app = Client("auto_reply_bot", api_id=API_ID, api_hash=API_HASH)
processed_messages = set()
data_cache = {}
message_timestamps = {}
reply_interval = 10
reply_threshold = 2


# Function to convert audio file to text
def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    try:
        # Load the audio file
        audio = sr.AudioFile(audio_file)
        with audio as source:
            print("Listening...")
            audio_data = recognizer.record(source)
            # Recognize speech using Google Web Speech API
            text = recognizer.recognize_google(audio_data, language="uz-UZ")
            return text
    except sr.UnknownValueError:
        return "Sorry, I did not understand the audio."
    except sr.RequestError as e:
        return f"Sorry, there was an error with the request: {e}"
    except Exception as e:
        return f"Error transcribing audio: {e}"


def update_power_value(new_value: bool):
    if not isinstance(new_value, bool):
        raise ValueError("The new_value must be a boolean.")
    file_path = 'config.json'
    data = {"power": new_value}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            existing_data = json.load(file)
            existing_data["power"] = new_value
            with open(file_path, 'w') as file:
                json.dump(existing_data, file, indent=4)
    else:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)


async def load_data_from_db():
    print("Loading data from the database...")
    global data_cache
    conn = connect_db()
    if not conn:
        print("Error: Database connection failed")
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT key, value FROM bot_responses;")
            data_cache = {row[0].lower().strip(): row[1] for row in cursor.fetchall()}
    except Exception as e:
        print(f"Error fetching data from the database: {e}")
    finally:
        print("iiiiyyyyyy")
        conn.close()


async def add_entry_to_db(key, values):
    if not key.strip():
        print("Error: Kalit bo'sh bo'lishi mumkin emas")
        return
    conn = connect_db()
    if not conn:
        print("Error: Database connection failed")
        return
    if not isinstance(values, list):
        values = [values]
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT value FROM bot_responses WHERE key = %s;", (key,))
            result = cursor.fetchone()
            if result:
                print(result)
                existing_values = result[0]
                if isinstance(existing_values, list):
                    existing_values.extend(value for value in values if value not in existing_values)
                else:
                    existing_values = [existing_values] + [value for value in values if value != existing_values]
                cursor.execute("UPDATE bot_responses SET value = %s WHERE key = %s;", (existing_values, key))
                await load_data_from_db()
            else:
                cursor.execute("INSERT INTO bot_responses (key, value) VALUES (%s, %s);", (key, values))
            conn.commit()
            data_cache[key.lower().strip()] = values
            await load_data_from_db()
    except Exception as e:
        print(f"Error adding entry to the database: {e}")
        await load_data_from_db()
    finally:
        await load_data_from_db()
        conn.close()


def get_power_value():
    file_path = 'config.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get("power", False)
    return False


def find_best_match(user_message):
    user_message = user_message.lower().strip()
    # O'xshash so'zlarni topish uchun threshold darajasi belgilaymiz (masalan, 0.6 yoki undan yuqori)
    threshold = 0.6
    # So'zning aniq mosligi uchun birinchi qidiruv
    if user_message in data_cache:
        responses = data_cache[user_message]
        return random.choice(responses) if responses else None
    # Agar aniq moslik bo'lmasa, o'xshash so'zlarni qidiramiz
    for key in data_cache:
        # O'xshashlik darajasini aniqlaymiz
        similarity = difflib.SequenceMatcher(None, key, user_message).ratio()
        if similarity >= threshold:
            responses = data_cache[key]
            return random.choice(responses) if responses else None
    # Agar yuqoridagi ikkita usul ham javob topa olmasa, oddiy qidiruvni amalga oshiramiz
    for key in data_cache:
        if re.search(key, user_message):
            responses = data_cache[key]
            return random.choice(responses) if responses else None
    return None


@app.on_message(filters.text & filters.private)
async def auto_reply(client, message):
    current_time = time.time()
    user_id = message.from_user.id
    my_ids = (await client.get_me()).id
    if message.from_user.is_bot:
        return
    if user_id not in message_timestamps:
        message_timestamps[user_id] = []
    message_timestamps[user_id].append(current_time)
    message_timestamps[user_id] = [timestamp for timestamp in message_timestamps[user_id] if
                                   current_time - timestamp <= reply_interval]
    use_reply_to = len(message_timestamps[user_id]) >= reply_threshold
    if message.id in processed_messages:
        return
    if message.text.startswith('/start'):
        if message.from_user.id == my_ids:
            update_power_value(True)
            await client.send_message(message.chat.id, 'Mening yordamchim ishga tushirildi')
        return
    if message.text.startswith('/stop'):
        if message.from_user.id == my_ids:
            update_power_value(False)
            await client.send_message(message.chat.id, 'Mening yordamchim ishni to`xtatdi')
        return
    if message.text.startswith('/buckup'):
        if message.from_user.id == my_ids:
            conn = connect_db()
            if conn:
                backup_db_to_json(conn)
                conn.close()
            await client.send_message(message.chat.id, 'Ma`lumotlar bazasi yuklandi')
        return
    if message.text.startswith('/add'):
        if message.from_user.id == my_ids:
            if '||' not in message.text:
                await client.send_message(message.chat.id, 'Kalit va qiymatni || bilan ajrating')
                return
            if message.text.count('||') > 1:
                await client.send_message(message.chat.id, 'Kalit va qiymatni || bilan ajrating')
                return
            if message.text.split('/add')[1].strip() == '':
                await client.send_message(message.chat.id, 'Kalit va qiymatni || bilan ajrating')
                return
            key_value = message.text.split('/add')[1].strip()
            key, value = key_value.split('||')
            await add_entry_to_db(key, value)
            await client.send_message(message.chat.id, 'Ma`lumotlar bazasiga muvaffaqiyatli qo`shildi')
        return
    if not get_power_value():
        return
    if message.from_user.id == my_ids:
        return
    user_message = message.text.lower().strip()
    reply_text = find_best_match(user_message)
    if reply_text is None or reply_text == '':
        try:
            response = requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent',
                headers={'Content-Type': 'application/json'},
                params={'key': GEMINI_API_KEY},
                json={
                    'contents': [
                        {
                            'parts': [
                                {'text': user_message + '\n' + ' iltimos uzbek tilida javob bering.'}
                            ]
                        }
                    ]
                }
            )
            if response.status_code == 200:
                gemini_response = response.json()
                reply_text = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get(
                    'text', "Gemini API dan to'g'ri javob olmadim.")
            else:
                reply_text = "Хато: Gemini API дан жавоб олишда муаммо"
        except Exception as e:
            reply_text = "Хато: Mening sun'iy intellektimda muammo bor" + str(e)
    else:
        conn = connect_db()
        if conn:
            add_working_count(conn, user_message)
            conn.close()
    reply_to_message_id = message.id if use_reply_to else None
    processed_messages.add(message.id)
    await client.send_message(message.chat.id, reply_text, reply_to_message_id=reply_to_message_id)


@app.on_message(filters.private & (filters.audio | filters.voice))
async def auto_reply_other(client, message):
    global transcribed_text
    current_time = time.time()
    user_id = message.from_user.id
    my_ids = (await client.get_me()).id
    if message.from_user.is_bot:
        return
    if user_id not in message_timestamps:
        message_timestamps[user_id] = []
    message_timestamps[user_id].append(current_time)
    message_timestamps[user_id] = [timestamp for timestamp in message_timestamps[user_id] if
                                   current_time - timestamp <= reply_interval]
    use_reply_to = len(message_timestamps[user_id]) >= reply_threshold
    if message.id in processed_messages:
        return
    if not get_power_value():
        return
    if message.from_user.id == my_ids:
        return
    if message.audio:
        file_id = message.audio.file_id
        file = await client.download_media(file_id)
        transcribed_text = audio_to_text(file)
    elif message.voice:
        file_id = message.voice.file_id
        file = await client.download_media(file_id)
        voice_audio = AudioSegment.from_ogg(file)
        wav_file = "temp_voice.wav"
        voice_audio.export(wav_file, format="wav")
        transcribed_text = audio_to_text(wav_file)

    user_message = transcribed_text.lower().strip()
    reply_text = find_best_match(user_message)
    print("text:", user_message)
    print("Reply text:", reply_text)
    if reply_text is None or reply_text == '':
        try:
            response = requests.post(
                'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent',
                headers={'Content-Type': 'application/json'},
                params={'key': GEMINI_API_KEY},
                json={
                    'contents': [
                        {
                            'parts': [
                                {'text': user_message + '\n' + ' iltimos uzbek tilida javob bering.'}
                            ]
                        }
                    ]
                }
            )
            if response.status_code == 200:
                gemini_response = response.json()
                reply_text = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get(
                    'text', "Gemini API dan to'g'ri javob olmadim.")
            else:
                reply_text = "Хато: Gemini API дан жавоб олишда муаммо"
        except Exception as e:
            reply_text = "Хато: Mening sun'iy intellektimda muammo bor" + str(e)
    else:
        conn = connect_db()
        if conn:
            add_working_count(conn, user_message)
            conn.close()
    reply_to_message_id = message.id if use_reply_to else None
    processed_messages.add(message.id)
    await client.send_message(message.chat.id, reply_text, reply_to_message_id=reply_to_message_id)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(load_data_from_db())
    app.run()
