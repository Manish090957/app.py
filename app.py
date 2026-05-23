import os
import asyncio
from quart import Quart, render_template_string, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

app = Quart(__name__)

# Core Credentials
API_ID = int(os.environ.get("API_ID", 23483842))
API_HASH = os.environ.get("API_HASH", "63f3942db5bb0bd6ab36352ca52e773b")

# In-memory storage temporary tracking ke liye
user_sessions = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Telethon Session Generator</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; box-sizing: border-box; }
        h2 { margin-top: 0; color: #333; text-align: center; }
        p { color: #666; font-size: 14px; text-align: center; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; background: #2481cc; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #1a65a3; }
        .hidden { display: none; }
        .success-box { background: #e6f4ea; border: 1px solid #137333; padding: 15px; border-radius: 6px; word-break: break-all; font-family: monospace; font-size: 12px; margin-top: 15px; }
        .error { color: red; font-size: 14px; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>String Session Generator</h2>
        <p id="status-text">Enter your phone number with country code to request login.</p>
        
        <div id="step-phone">
            <input type="text" id="phone" placeholder="+919876543210">
            <button onclick="sendPhone()">Send Code</button>
        </div>

        <div id="step-otp" class="hidden">
            <input type="text" id="otp" placeholder="Enter 5-digit OTP">
            <button onclick="sendOtp()">Verify OTP</button>
        </div>

        <div id="step-2fa" class="hidden">
            <input type="password" id="password" placeholder="Enter 2FA Password">
            <button onclick="sendPassword()">Submit Password</button>
        </div>

        <div id="step-success" class="hidden">
            <p style="color: green; font-weight: bold;">🎉 Session Generated Successfully!</p>
            <div class="success-box" id="token-box"></div>
            <p style="font-size: 12px; margin-top: 10px; color: #999;">Copy this complete string and paste it into the bot panel.</p>
        </div>

        <div id="error-msg" class="error"></div>
    </div>

    <script>
        let currentPhone = "";

        async function safeAPI(url, data) {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await res.json();
        }

        async function sendPhone() {
            const phone = document.getElementById('phone').value.trim();
            if(!phone) return;
            currentPhone = phone;
            document.getElementById('error-msg').innerText = "";
            
            const res = await safeAPI('/submit_phone', { phone });
            if(res.status === 'ok') {
                document.getElementById('step-phone').classList.add('hidden');
                document.getElementById('step-otp').classList.remove('hidden');
                document.getElementById('status-text').innerText = "Check your official Telegram app for the code.";
            } else {
                document.getElementById('error-msg').innerText = res.message;
            }
        }

        async function sendOtp() {
            const otp = document.getElementById('otp').value.trim();
            if(!otp) return;
            document.getElementById('error-msg').innerText = "";

            const res = await safeAPI('/submit_otp', { phone: currentPhone, code: otp });
            if(res.status === 'ok') {
                showSuccess(res.session);
            } else if(res.status === '2fa_needed') {
                document.getElementById('step-otp').classList.add('hidden');
                document.getElementById('step-2fa').classList.remove('hidden');
                document.getElementById('status-text').innerText = "Two-Step Verification (2FA) is enabled on your account.";
            } else {
                document.getElementById('error-msg').innerText = res.message;
            }
        }

        async function sendPassword() {
            const password = document.getElementById('password').value.trim();
            if(!password) return;
            document.getElementById('error-msg').innerText = "";

            const res = await safeAPI('/submit_password', { phone: currentPhone, password });
            if(res.status === 'ok') {
                showSuccess(res.session);
            } else {
                document.getElementById('error-msg').innerText = res.message;
            }
        }

        function showSuccess(sessionStr) {
            document.getElementById('step-otp').classList.add('hidden');
            document.getElementById('step-2fa').classList.add('hidden');
            document.getElementById('step-success').classList.remove('hidden');
            document.getElementById('status-text').innerText = "Keep this session string secure.";
            document.getElementById('token-box').innerText = sessionStr;
        }
    </script>
</body>
</html>
"""

@app.route('/')
async def index():
    # ✅ FIXED: Added await here
    return await render_template_string(HTML_TEMPLATE)

@app.route('/submit_phone', methods=['POST'])
async def submit_phone():
    data = await request.get_json()
    phone = data.get("phone", "").strip().replace(" ", "")
    
    if not phone:
        return jsonify({"status": "error", "message": "Phone number missing."})
        
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH, device_model="Telegram Web", system_version="Windows Web", app_version="1.0.0")
        await client.connect()
        
        send_code = await client.send_code_request(phone)
        user_sessions[phone] = {
            "client": client,
            "phone_code_hash": send_code.phone_code_hash
        }
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/submit_otp', methods=['POST'])
async def submit_otp():
    data = await request.get_json()
    phone = data.get("phone")
    code = data.get("code", "").strip()
    
    if phone not in user_sessions:
        return jsonify({"status": "error", "message": "Session context missing. Reload page."})
        
    session_data = user_sessions[phone]
    client = session_data["client"]
    phone_code_hash = session_data["phone_code_hash"]
    
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        session_str = client.session.save()
        await client.disconnect()
        user_sessions.pop(phone, None)
        return jsonify({"status": "ok", "session": session_str})
    except SessionPasswordNeededError:
        return jsonify({"status": "2fa_needed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/submit_password', methods=['POST'])
async def submit_password():
    data = await request.get_json()
    phone = data.get("phone")
    password = data.get("password", "").strip()
    
    if phone not in user_sessions:
        return jsonify({"status": "error", "message": "Session context missing. Reload page."})
        
    client = user_sessions[phone]["client"]
    try:
        await client.sign_in(password=password)
        session_str = client.session.save()
        await client.disconnect()
        user_sessions.pop(phone, None)
        return jsonify({"status": "ok", "session": session_str})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
