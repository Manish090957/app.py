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

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Secure Telethon Session Generator</title>

<style>
*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

body{
    font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
    background:#f4f7f6;
    display:flex;
    justify-content:center;
    align-items:center;
    min-height:100vh;
    padding:20px;
}

.card{
    background:#fff;
    width:100%;
    max-width:420px;
    border-radius:20px;
    padding:30px;
    box-shadow:0 10px 35px rgba(0,0,0,.12);
}

h2{
    text-align:center;
    margin-bottom:10px;
    color:#222;
}

p{
    text-align:center;
    color:#666;
    font-size:14px;
    line-height:1.6;
}

input{
    width:100%;
    padding:14px;
    border:1px solid #ddd;
    border-radius:10px;
    margin-top:14px;
    outline:none;
    font-size:15px;
    transition:.3s;
}

input:focus{
    border-color:#2481cc;
}

button{
    width:100%;
    margin-top:14px;
    border:none;
    border-radius:10px;
    padding:14px;
    background:#2481cc;
    color:#fff;
    cursor:pointer;
    font-size:16px;
    font-weight:600;
    transition:.3s;
}

button:hover{
    background:#1a65a3;
}

button:disabled{
    opacity:.7;
    cursor:not-allowed;
}

.copy-btn{
    background:#16a34a;
}

.copy-btn:hover{
    background:#15803d;
}

.hidden{
    display:none;
}

.success-box{
    background:#eefbf2;
    border:2px solid #16a34a;
    border-radius:12px;
    padding:15px;
    margin-top:15px;
    font-family:monospace;
    font-size:12px;
    word-break:break-all;
    max-height:200px;
    overflow:auto;
}

.error{
    text-align:center;
    margin-top:15px;
    color:red;
    font-size:14px;
}

.success-title{
    color:#16a34a;
    text-align:center;
    font-weight:700;
    margin-top:15px;
}

.small{
    font-size:12px;
    color:#999;
    margin-top:10px;
}

.loader{
    display:none;
    text-align:center;
    margin-top:12px;
    color:#2481cc;
    font-size:14px;
}

.otp-container{
    display:flex;
    justify-content:center;
    gap:10px;
    margin-top:15px;
}

.otp-box{
    width:55px !important;
    height:55px;
    text-align:center;
    font-size:22px;
    font-weight:700;
    border-radius:12px;
    padding:0 !important;
}
</style>
</head>

<body>

<div class="card">

    <h2>String Session Generator</h2>

    <p id="status-text">
        Enter your phone number with country code.
    </p>

    <div id="step-phone">
        <input
            type="text"
            id="phone"
            placeholder="+919876543210"
        >

        <button id="phoneBtn" onclick="sendPhone()">
            Send Code
        </button>
    </div>

    <div id="step-otp" class="hidden">

    <div class="otp-container">
        <input type="text" class="otp-box" maxlength="1">
        <input type="text" class="otp-box" maxlength="1">
        <input type="text" class="otp-box" maxlength="1">
        <input type="text" class="otp-box" maxlength="1">
        <input type="text" class="otp-box" maxlength="1">
    </div>

    <button id="otpBtn" onclick="sendOtp()">
        Verify OTP
    </button>

</div>

    <div id="step-2fa" class="hidden">
        <input
            type="password"
            id="password"
            placeholder="Enter 2FA Password"
        >

        <button id="passBtn" onclick="sendPassword()">
            Submit Password
        </button>
    </div>

    <div id="step-success" class="hidden">

        <p class="success-title">
            Session Generated Successfully
        </p>

        <div
            class="success-box"
            id="token-box">
        </div>

        <button
            class="copy-btn"
            onclick="copySession()">
            Copy Session
        </button>

        <p class="small">
            Keep this session secure.
        </p>
    </div>

    <div class="loader" id="loader">
        Processing...
    </div>

    <div class="error" id="error-msg"></div>

</div>

<script>

let currentPhone = "";

function setLoading(status){
    document.getElementById("loader").style.display =
        status ? "block" : "none";
}

async function safeAPI(url,data){

    const res = await fetch(url,{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify(data)
    });

    return await res.json();
}

async function sendPhone(){

    const phone =
        document.getElementById("phone")
        .value.trim();

    if(!phone) return;

    currentPhone = phone;

    document.getElementById(
        "error-msg"
    ).innerText = "";

    setLoading(true);

    try{

        const res =
            await safeAPI(
                "/submit_phone",
                {phone}
            );

        if(res.status==="ok"){

            document
                .getElementById("step-phone")
                .classList.add("hidden");

            document
                .getElementById("step-otp")
                .classList.remove("hidden");

            document
                .getElementById("status-text")
                .innerText =
                "Check Telegram for OTP code.";

        }else{

            document
                .getElementById("error-msg")
                .innerText =
                res.message;
        }

    }catch(err){

        document
            .getElementById("error-msg")
            .innerText =
            "Network error.";

    }

    setLoading(false);
}

async function sendOtp() {

    const otpInputs =
        document.querySelectorAll(".otp-box");

    const otp =
        Array.from(otpInputs)
        .map(input => input.value.trim())
        .join("");

    if (otp.length !== 5) {
        document.getElementById(
            "error-msg"
        ).innerText =
            "Enter complete OTP.";
        return;
    }

    document.getElementById(
        "error-msg"
    ).innerText = "";

    setLoading(true);

    try {

        const res =
            await safeAPI(
                "/submit_otp",
                {
                    phone: currentPhone,
                    code: otp
                }
            );

        if (res.status === "ok") {

            showSuccess(
                res.session
            );

        } else if (
            res.status === "2fa_needed"
        ) {

            document
                .getElementById("step-otp")
                .classList.add("hidden");

            document
                .getElementById("step-2fa")
                .classList.remove("hidden");

            document
                .getElementById("status-text")
                .innerText =
                "2FA password required.";

        } else {

            document
                .getElementById("error-msg")
                .innerText =
                res.message;
        }

    } catch (err) {

        document
            .getElementById("error-msg")
            .innerText =
            "Network error.";
    }

    setLoading(false);
}

async function sendPassword(){

    const password =
        document
        .getElementById("password")
        .value.trim();

    if(!password) return;

    document.getElementById(
        "error-msg"
    ).innerText = "";

    setLoading(true);

    try{

        const res =
            await safeAPI(
                "/submit_password",
                {
                    phone:currentPhone,
                    password
                }
            );

        if(res.status==="ok"){

            showSuccess(
                res.session
            );

        }else{

            document
                .getElementById("error-msg")
                .innerText =
                res.message;
        }

    }catch(err){

        document
            .getElementById("error-msg")
            .innerText =
            "Network error.";
    }

    setLoading(false);
}

function showSuccess(sessionStr){

    document
        .getElementById("step-otp")
        .classList.add("hidden");

    document
        .getElementById("step-2fa")
        .classList.add("hidden");

    document
        .getElementById("step-success")
        .classList.remove("hidden");

    document
        .getElementById("status-text")
        .innerText =
        "Your StringSession is ready.";

    document
        .getElementById("token-box")
        .innerText =
        sessionStr;
}

async function copySession(){

    const text =
        document
        .getElementById("token-box")
        .innerText
        .trim();

    try{

        await navigator
            .clipboard
            .writeText(text);

        alert("Session copied!");

    }catch(err){

        const temp =
            document.createElement(
                "textarea"
            );

        temp.value = text;

        document.body
            .appendChild(temp);

        temp.select();

        document.execCommand(
            "copy"
        );

        document.body
            .removeChild(temp);

        alert("Session copied!");
    }
}

document.addEventListener(
    "DOMContentLoaded",
    ()=>{

    const inputs =
        document.querySelectorAll(
            ".otp-box"
        );

    inputs.forEach(
        (input,index)=>{

        input.addEventListener(
            "input",
            (e)=>{

            e.target.value =
                e.target.value
                .replace(
                    /\D/g,
                    ''
                );

            if(
                e.target.value &&
                index <
                inputs.length - 1
            ){
                inputs[
                    index + 1
                ].focus();
            }
        });

        input.addEventListener(
            "keydown",
            (e)=>{

            if(
                e.key ===
                "Backspace" &&
                !input.value &&
                index > 0
            ){
                inputs[
                    index - 1
                ].focus();
            }
        });

        input.addEventListener(
            "paste",
            (e)=>{

            e.preventDefault();

            const pasted =
                (
                    e.clipboardData
                    .getData("text")
                    || ""
                )
                .replace(
                    /\D/g,
                    ''
                )
                .slice(0,5);

            pasted
            .split("")
            .forEach(
                (char,i)=>{

                if(inputs[i]){
                    inputs[i]
                    .value =
                    char;
                }
            });

            const lastFilled =
                Math.min(
                    pasted.length,
                    inputs.length
                ) - 1;

            if(
                lastFilled >= 0
            ){
                inputs[
                    lastFilled
                ].focus();
            }
        });
    });
});

</script>

</body>
</html>
"""

@app.route('/')
async def index():
    return await render_template_string(
        HTML_TEMPLATE
    )


@app.route('/submit_phone', methods=['POST'])
async def submit_phone():

    data = await request.get_json() or {}

    phone = str(
        data.get("phone", "")
    ).strip().replace(" ", "")

    if not phone:
        return jsonify({
            "status": "error",
            "message":
            "Phone number missing."
        })

    client = None

    try:

        client = TelegramClient(
            StringSession(),
            API_ID,
            API_HASH,
            device_model="Telegram Web",
            system_version="Windows Web",
            app_version="1.0.0"
        )

        await client.connect()

        send_code = await client.send_code_request(
            phone
        )

        user_sessions[phone] = {
            "client": client,
            "phone_code_hash":
            send_code.phone_code_hash
        }

        return jsonify({
            "status": "ok"
        })

    except Exception as e:

        if client:
            await client.disconnect()

        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/submit_otp', methods=['POST'])
async def submit_otp():

    data = await request.get_json() or {}

    phone = str(
        data.get("phone", "")
    ).strip()

    code = str(
        data.get("code", "")
    ).strip()

    if phone not in user_sessions:
        return jsonify({
            "status": "error",
            "message":
            "Session context missing. Reload page."
        })

    session_data = user_sessions[
        phone
    ]

    client = session_data[
        "client"
    ]

    phone_code_hash = session_data[
        "phone_code_hash"
    ]

    try:

        if not client.is_connected():
            await client.connect()

        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=
            phone_code_hash
        )

        session_str = client.session.save()

        await client.disconnect()

        user_sessions.pop(
            phone,
            None
        )

        return jsonify({
            "status": "ok",
            "session":
            session_str
        })

    except SessionPasswordNeededError:

        return jsonify({
            "status":
            "2fa_needed"
        })

    except Exception as e:

        return jsonify({
            "status":
            "error",
            "message":
            str(e)
        })


@app.route(
    '/submit_password',
    methods=['POST']
)
async def submit_password():

    data = await request.get_json() or {}

    phone = str(
        data.get("phone", "")
    ).strip()

    password = str(
        data.get(
            "password", ""
        )
    ).strip()

    if phone not in user_sessions:

        return jsonify({
            "status":
            "error",
            "message":
            "Session context missing. Reload page."
        })

    client = user_sessions[
        phone
    ]["client"]

    try:

        if not client.is_connected():
            await client.connect()

        await client.sign_in(
            password=password
        )

        session_str = client.session.save()

        await client.disconnect()

        user_sessions.pop(
            phone,
            None
        )

        return jsonify({
            "status": "ok",
            "session":
            session_str
        })

    except Exception as e:

        return jsonify({
            "status":
            "error",
            "message":
            str(e)
        })


if __name__ == '__main__':

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host='0.0.0.0',
        port=port
    )
