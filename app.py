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

user_sessions = {}

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>String Session Generator</title>
<style>
    body{font-family:'Segoe UI',sans-serif;background:#f4f7f6;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px;}
    .card{background:#fff;width:100%;max-width:420px;border-radius:20px;padding:30px;box-shadow:0 10px 35px rgba(0,0,0,.12);}
    .disclaimer{background:#fff3cd;padding:10px;border-radius:10px;font-size:12px;color:#856404;margin-bottom:15px;text-align:center;}
    input{width:100%;padding:14px;border:1px solid #ddd;border-radius:10px;margin-top:14px;}
    button{width:100%;margin-top:14px;border:none;border-radius:10px;padding:14px;background:#2481cc;color:#fff;cursor:pointer;font-weight:600;}
    .hidden{display:none;}
    .success-box{background:#eefbf2;border:1px solid #16a34a;border-radius:12px;padding:15px;margin-top:15px;font-family:monospace;font-size:12px;word-break:break-all;}
</style>
</head>
<body>
<div class="card">
    <h2>String Session Generator</h2>
    <div class="disclaimer">
        <strong>Disclaimer:</strong> This tool is strictly for generating a StringSession and providing the associated API credentials for your private use. We do not store, monitor, or access your Telegram account.
    </div>
    <div id="step-phone">
        <input type="text" id="phone" placeholder="+919876543210">
        <button onclick="sendPhone()">Send Code</button>
    </div>
    <div id="step-otp" class="hidden">
        <input type="text" id="otp" placeholder="Enter OTP (5 digits)">
        <button onclick="sendOtp()">Verify OTP</button>
    </div>
    <div id="step-2fa" class="hidden">
        <input type="password" id="password" placeholder="Enter 2FA Password">
        <button onclick="sendPassword()">Submit Password</button>
    </div>
    <div id="step-success" class="hidden">
        <p><strong>Credentials Generated:</strong></p>
        <div class="success-box" id="result-box"></div>
        <button class="copy-btn" onclick="copyResult()">Copy All</button>
    </div>
    <div id="error-msg" style="color:red; text-align:center; margin-top:15px;"></div>
</div>
<script>
let currentPhone = "";
async function safeAPI(url, data){
    const res = await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    return await res.json();
}
async function sendPhone(){
    currentPhone = document.getElementById("phone").value.trim();
    const res = await safeAPI("/submit_phone", {phone: currentPhone});
    if(res.status==="ok"){
        document.getElementById("step-phone").classList.add("hidden");
        document.getElementById("step-otp").classList.remove("hidden");
    } else {document.getElementById("error-msg").innerText = res.message;}
}
async function sendOtp(){
    const otp = document.getElementById("otp").value.trim();
    const res = await safeAPI("/submit_otp", {phone: currentPhone, code: otp});
    if(res.status==="ok"){ showSuccess(res); }
    else if(res.status==="2fa_needed"){
        document.getElementById("step-otp").classList.add("hidden");
        document.getElementById("step-2fa").classList.remove("hidden");
    } else {document.getElementById("error-msg").innerText = res.message;}
}
async function sendPassword(){
    const password = document.getElementById("password").value.trim();
    const res = await safeAPI("/submit_password", {phone: currentPhone, password});
    if(res.status==="ok"){ showSuccess(res); }
    else {document.getElementById("error-msg").innerText = res.message;}
}
function showSuccess(res){
    document.getElementById("step-otp").classList.add("hidden");
    document.getElementById("step-2fa").classList.add("hidden");
    document.getElementById("step-success").classList.remove("hidden");
    document.getElementById("result-box").innerText = `API_ID: ${res.api_id}\nAPI_HASH: ${res.api_hash}\nSESSION: ${res.session}`;
}
function copyResult(){
    navigator.clipboard.writeText(document.getElementById("result-box").innerText);
    alert("Copied!");
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
    phone = data.get("phone")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    send_code = await client.send_code_request(phone)
    user_sessions[phone] = {"client": client, "phone_code_hash": send_code.phone_code_hash}
    return jsonify({"status": "ok"})

@app.route('/submit_otp', methods=['POST'])
async def submit_otp():
    data = await request.get_json()
    phone, code = data.get("phone"), data.get("code")
    sess = user_sessions[phone]
    try:
        await sess['client'].sign_in(phone=phone, code=code, phone_code_hash=sess['phone_code_hash'])
        session_str = sess['client'].session.save()
        await sess['client'].disconnect()
        return jsonify({"status": "ok", "session": session_str, "api_id": API_ID, "api_hash": API_HASH})
    except SessionPasswordNeededError: return jsonify({"status": "2fa_needed"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)})

@app.route('/submit_password', methods=['POST'])
async def submit_password():
    data = await request.get_json()
    phone, password = data.get("phone"), data.get("password")
    client = user_sessions[phone]["client"]
    await client.sign_in(password=password)
    session_str = client.session.save()
    await client.disconnect()
    return jsonify({"status": "ok", "session": session_str, "api_id": API_ID, "api_hash": API_HASH})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
