import os
from quart import Quart, render_template_string, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

app = Quart(__name__)

API_ID = int(os.environ.get("API_ID", 23483842))
API_HASH = os.environ.get("API_HASH", "63f3942db5bb0bd6ab36352ca52e773b")

user_sessions = {}

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>String Session Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding: 20px; }
        .card { background: #fff; width: 100%; max-width: 400px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .note { font-size: 13px; color: #555; margin-bottom: 15px; border-left: 3px solid #2481cc; padding-left: 10px; }
        input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #2481cc; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
<div class="card">
    <h3>String Session Generator</h3>
    <div class="note">Enter your phone number with country code. We do not store any data; this is a gateway tool for your private projects.</div>
    
    <div id="step-1">
        <input type="text" id="phone" placeholder="+91XXXXXXXXXX">
        <button onclick="sendPhone()">Send Code</button>
    </div>
    <div id="step-2" class="hidden">
        <input type="text" id="code" placeholder="Enter Code/OTP">
        <input type="password" id="password" placeholder="2FA Password (if any)" class="hidden">
        <button onclick="verify()">Verify</button>
    </div>
    <div id="result" class="hidden">
        <p><strong>Session:</strong></p>
        <textarea id="session-out" style="width:100%; height:60px;"></textarea>
    </div>
    <div id="error" style="color:red; margin-top:10px;"></div>
</div>
<script>
let currentPhone = "";
async function callApi(route, data) {
    const res = await fetch(route, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
    return await res.json();
}
async function sendPhone() {
    currentPhone = document.getElementById("phone").value;
    const res = await callApi("/submit_phone", {phone: currentPhone});
    if(res.status === "ok") {
        document.getElementById("step-1").classList.add("hidden");
        document.getElementById("step-2").classList.remove("hidden");
    } else { document.getElementById("error").innerText = res.message; }
}
async function verify() {
    const data = {phone: currentPhone, code: document.getElementById("code").value, password: document.getElementById("password").value};
    const res = await callApi("/verify", data);
    if(res.status === "2fa") {
        document.getElementById("password").classList.remove("hidden");
        document.getElementById("error").innerText = "2FA Password Required";
    } else if(res.status === "ok") {
        document.getElementById("step-2").classList.add("hidden");
        document.getElementById("result").classList.remove("hidden");
        document.getElementById("session-out").value = res.session;
    } else { document.getElementById("error").innerText = res.message; }
}
</script>
</body>
</html>
"""

@app.route('/')
async def index(): return await render_template_string(HTML_TEMPLATE)

@app.route('/submit_phone', methods=['POST'])
async def submit_phone():
    data = await request.get_json()
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    hash_code = (await client.send_code_request(data['phone'])).phone_code_hash
    user_sessions[data['phone']] = {"client": client, "hash": hash_code}
    return jsonify({"status": "ok"})

@app.route('/verify', methods=['POST'])
async def verify():
    data = await request.get_json()
    sess = user_sessions[data['phone']]
    try:
        await sess['client'].sign_in(data['phone'], data['code'], phone_code_hash=sess['hash'])
        res = {"status": "ok", "session": sess['client'].session.save()}
    except SessionPasswordNeededError:
        res = {"status": "2fa"}
    except Exception as e:
        if data.get('password'):
            await sess['client'].sign_in(password=data['password'])
            res = {"status": "ok", "session": sess['client'].session.save()}
        else: res = {"status": "error", "message": str(e)}
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
