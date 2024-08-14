import os
import asyncio
from flask import Flask, render_template, request, redirect, url_for, session
from telethon import TelegramClient
from telethon.errors import PhoneCodeExpiredError, PhoneCodeInvalidError
from dotenv import load_dotenv
import uuid

# API_ID = 24325110
# API_HASH = '09c12098a3e94010de9988e3168ced9e'
load_dotenv()

app = Flask(__name__)
app.secret_key = 'chevar'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_PATH'] = 'users'
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')


def generate_uid_with_key(key):
    uid = uuid.uuid4()  # Generate a random UUID
    combined = f"{key}-{uid}"
    return combined


Session_Flask = app.config['SESSION_FILE_PATH'] = 'users/' + generate_uid_with_key('chevar')


def generated_key():
    return str(API_ID) + '_' + str(API_HASH)


async def create_client():
    client = TelegramClient(Session_Flask, API_ID, API_HASH)
    await client.connect()
    return client


@app.route('/')
def home():
    if 'user' in session:
        return render_template('home.html', username=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']

        async def login_async():
            client = await create_client()
            if not await client.is_user_authorized():
                try:
                    sent_code = await client.send_code_request(phone)
                    session['phone'] = phone
                    session['phone_code_hash'] = sent_code.phone_code_hash
                    return redirect(url_for('verify'))
                except Exception as e:
                    return f'Error: {str(e)}'
            else:
                session['user'] = (await client.get_me()).username
                return redirect(url_for('home'))

        return asyncio.run(login_async())

    return render_template('login.html')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code = request.form['code']

        async def verify_async():
            client = await create_client()
            phone = session['phone']
            phone_code_hash = session['phone_code_hash']

            try:
                # Debug: Log the phone, code, and phone_code_hash
                print(f"Verifying phone: {phone}, code: {code}, phone_code_hash: {phone_code_hash}")

                await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                session['user'] = (await client.get_me()).username
                return redirect(url_for('home'))

            except PhoneCodeExpiredError:
                return "The confirmation code has expired. Please request a new code."
            except PhoneCodeInvalidError:
                return "The confirmation code is invalid. Please check the code and try again."
            except Exception as e:
                return f'Error: {str(e)}'

        return asyncio.run(verify_async())

    return render_template('verify.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('phone', None)
    session.pop('phone_code_hash', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)