import json
import os
import requests
from pyrogram import Client, filters
import re

# Telegram bot API credentials
API_ID = 24325110
API_HASH = '09c12098a3e94010de9988e3168ced9e'

GEMINI_API_KEY = 'AIzaSyCJd31hmAHHPom3ou7KNaDl2LQnbkEF5cQ'

app = Client("auto_reply_bot", api_id=API_ID, api_hash=API_HASH)


def find_best_match(user_message, data):
    user_message = user_message.lower().strip()
    data = {k.lower().strip(): v for k, v in data.items()}
    if user_message in data:
        return data[user_message]
    for key in data:
        if key in user_message:
            return data[key]
    for key in data:
        if re.search(key, user_message):
            return data[key]
    return None


@app.on_message(filters.text & filters.private)
async def auto_reply(client, message):
    if message.text.startswith('/start'):
        update_power_value('true')
        return
    if message.text.startswith('/stop'):
        update_power_value('false')
        return
    if message.text.startswith('/add'):
        try:
            key, value = message.text.split(' ', 1)[1].split('", "')
            key = key.strip()[1:]
            value = value.strip()[:-1]
            add_entry_to_json(key, value)
            await client.send_message(message.chat.id, "Muvaffaqiyatli qo'shildi")
            return
        except:
            await client.send_message(message.chat.id,
                                      "Xatolik: To'g'ri formatda yozing. Masalan: /add \"salom\", \"Salom, qalaysiz?\"")
            return
    if not getPowerValue():
        return

    my_id = (await client.get_me()).id
    if message.from_user.id == my_id:
        print("Botdan kel")
        return
    user_message = message.text.lower().strip()

    with open('data.json', 'r') as f:
        data = json.load(f)

    reply_text = find_best_match(user_message, data)
    print(reply_text)
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
            reply_text = "Хато: Mening sun'iy intellektimda muammo bor"

    # Send the response back to the user
    await client.send_message(message.chat.id, reply_text)


@app.on_message(filters.audio & filters.private)
async def auto_reply_audio(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Iltimos, ishingiz zarurroq bolsa yozing. shunda tezroq javob "
                                               "berishimiz mumkin.")


@app.on_message(filters.voice & filters.private)
async def auto_reply_voice(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Iltimos, ishingiz zarurroq bolsa yozing. shunda tezroq javob "
                                               "berishimiz mumkin.")


@app.on_message(filters.photo & filters.private)
async def auto_reply_photo(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo rasm tashlab qo`ydingizku 😄")


@app.on_message(filters.video & filters.private)
async def auto_reply_video(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo video tashlab qo`ydingizku 😄")


@app.on_message(filters.document & filters.private)
async def auto_reply_document(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo fayl tashlab qo`ydingizku 😄")


@app.on_message(filters.animation & filters.private)
async def auto_reply_animation(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo animatsiya tashlab qo`ydingizku 😄")


@app.on_message(filters.sticker & filters.private)
async def auto_reply_sticker(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo stiker tashlab qo`ydingizku 😄")


@app.on_message(filters.contact & filters.private)
async def auto_reply_contact(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo kontakt tashlab qo`ydingizku 😄")


@app.on_message(filters.location & filters.private)
async def auto_reply_location(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo joylashuv tashlab qo`ydingizku 😄")


@app.on_message(filters.venue & filters.private)
async def auto_reply_venue(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo mehmonxona tashlab qo`ydingizku 😄")


@app.on_message(filters.poll & filters.private)
async def auto_reply_poll(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo so`rovnoma tashlab qo`ydingizku 😄")


@app.on_message(filters.dice & filters.private)
async def auto_reply_dice(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo zar tashlab qo`ydingizku 😄")


@app.on_message(filters.game & filters.private)
async def auto_reply_game(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo o'yin tashlab qo`ydingizku 😄")


@app.on_message(filters.service & filters.private)
async def auto_reply_service(client, message):
    if not getPowerValue():
        return
    await client.send_message(message.chat.id, "Ooo xizmat tashlab qo`ydingizku 😄")


def add_entry_to_json(key, value):
    file_path = 'data.json'
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)
    with open(file_path, 'r') as f:
        data = json.load(f)
    data[key] = value
    with open(file_path, 'w') as f:
        json.dump(data, f)


def update_power_value(new_value):
    file_path = 'config.json'
    if new_value.lower() == 'true':
        value = True
    elif new_value.lower() == 'false':
        value = False
    else:
        raise ValueError("Invalid value. Must be 'true' or 'false'.")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}
    data["power"] = value
    with open(file_path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def getPowerValue():
    file_path = 'config.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get("power", False)
    return False


app.run()
