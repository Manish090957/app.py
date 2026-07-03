import os
from quart import Quart, render_template_string, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession

app = Quart(__name__)

# Backend se API credentials load honge
API_ID = int(os.environ.get("API_ID", 23483842))
API_HASH = os.environ.get("API_HASH", "63f3942db5bb0bd6ab36352ca52e773b")

user_sessions = {}

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Session & Credential Generator</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; padding: 20px; display: flex; justify-content: center; }
        .card { background: #fff; width: 100%; max-width: 450px; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .note { background: #e7f3ff; padding: 15px; border-left: 5px solid #2481cc; font-size: 13px; margin-bottom: 20px; color: #333; }
        input, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 6px; border: 1px solid #ddd; }
        button { background: #2481cc; color: white; border: none; cursor: pointer; font-weight: bold; }
        .result-box { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin-top: 15px; font-size: 12px; word-break: break-all; }
        .hidden { display: none; }
    </style>
</head>
<body>
<div class="card">
    <h2>Telegram Session Gateway</h2>
    <div class="note">
        <strong>Important Note:</strong> This tool is strictly for generating a StringSession and providing the associated API credentials. We do not store, monitor, or access your Telegram account. You may copy these details to use in your own private projects.
    </div>
    <div id="step-1">
        <input type="text" id="phone" placeholder="Enter Phone (e.g., +91...)">
        <button onclick="sendPhone()">Send Verification Code</button>
    </div>
    <div id="step-2" class="hidden">
        <input type="text" id="otp" placeholder="Enter OTP Code">
        <button onclick="sendOtp()">Generate Credentials</button>
    </div>
    <div id="result" class="hidden">
        <p><strong>Your Generated Details:</strong></p>
        <div class="result-box">
            <p><strong>API ID:</strong> <span id="out-apiid"></span></p>
            <p><strong>API HASH:</strong> <span id="out-apihash"></span></p>
            <p><strong>String Session:</strong></p>
            <textarea id="out-session" readonly style="width:100%; height:80px;"></textarea>
        </div>
    </div>
    <div id="error" style="color: red; font-size: 13px; margin-top: 10px;"></div>
</div>
<script>
let currentPhone = "";
async function sendPhone() {
    currentPhone = document.getElementById("phone").value;
    const res = await (await fetch("/submit_phone", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({phone: currentPhone})})).json();
    if(res.status === "ok") {
        document.getElementById("step-1").classList.add("hidden");
        document.getElementById("step-2").classList.remove("hidden");
    } else { document.getElementById("error").innerText = res.message; }
}
async function sendOtp() {
    const code = document.getElementById("otp").value;
    const res = await (await fetch("/submit_otp", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({phone: currentPhone, code: code})})).json();
    if(res.status === "ok") {
        document.getElementById("step-2").classList.add("hidden");
        document.getElementById("result").classList.remove("hidden");
        document.getElementById("out-apiid").innerText = res.api_id;
        document.getElementById("out-apihash").innerText = res.api_hash;
        document.getElementById("out-session").value = res.session;
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
    phone = data['phone']
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    hash_code = (await client.send_code_request(phone)).phone_code_hash
    user_sessions[phone] = {"client": client, "hash": hash_code}
    return jsonify({"status": "ok"})

@app.route('/submit_otp', methods=['POST'])
async def submit_otp():
    data = await request.get_json()
    sess = user_sessions[data['phone']]
    await sess['client'].sign_in(data['phone'], data['code'], phone_code_hash=sess['hash'])
    session_str = sess['client'].session.save()
    await sess['client'].disconnect()
    return jsonify({"status": "ok", "session": session_str, "api_id": API_ID, "api_hash": API_HASH})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
