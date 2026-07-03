import os
from quart import Quart, render_template_string, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

app = Quart(__name__)

# Default Credentials (fallback)
DEFAULT_API_ID = int(os.environ.get("API_ID", 23483842))
DEFAULT_API_HASH = os.environ.get("API_HASH", "63f3942db5bb0bd6ab36352ca52e773b")

# In-memory storage for temporary tracking
user_sessions = {}

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Telegram String Session Generator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', Tahoma, sans-serif;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    color: #e6edf3;
  }
  .card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 28px;
    width: 100%;
    max-width: 440px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.5);
  }
  h1 {
    font-size: 22px;
    margin-bottom: 6px;
    text-align: center;
    color: #58a6ff;
  }
  .subtitle {
    text-align: center;
    font-size: 13px;
    color: #8b949e;
    margin-bottom: 18px;
  }
  .disclaimer {
    background: #2d1b1b;
    border: 1px solid #6e2828;
    color: #ffb4b4;
    font-size: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 18px;
    line-height: 1.5;
  }
  .disclaimer b { color: #ff6b6b; }
  label {
    display: block;
    font-size: 13px;
    margin-bottom: 6px;
    color: #c9d1d9;
    font-weight: 500;
  }
  input {
    width: 100%;
    padding: 11px 12px;
    border: 1px solid #30363d;
    background: #0d1117;
    color: #e6edf3;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 14px;
    outline: none;
    transition: border 0.2s;
  }
  input:focus { border-color: #58a6ff; }
  button {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 8px;
    background: linear-gradient(135deg, #238636, #2ea043);
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  button:hover { opacity: 0.9; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .otp-boxes {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 14px;
  }
  .otp-boxes input {
    width: 100%;
    text-align: center;
    font-size: 20px;
    font-weight: 600;
    padding: 12px 0;
    margin: 0;
  }
  .session-box {
    background: #0d1117;
    border: 1px solid #30363d;
    padding: 12px;
    border-radius: 8px;
    font-size: 12px;
    word-break: break-all;
    color: #7ee787;
    margin-bottom: 14px;
    max-height: 160px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
  }
  .success-title {
    color: #7ee787;
    font-size: 16px;
    text-align: center;
    margin-bottom: 14px;
    font-weight: 600;
  }
  .warn {
    text-align: center;
    color: #f0883e;
    font-size: 12px;
    margin-top: 12px;
  }
  .loader {
    text-align: center;
    color: #58a6ff;
    font-size: 14px;
    padding: 10px;
  }
  .error {
    color: #ff6b6b;
    font-size: 13px;
    margin-bottom: 10px;
    text-align: center;
  }
  .hidden { display: none; }
  .row { display: flex; gap: 10px; }
  .row > div { flex: 1; }
  footer {
    text-align: center;
    font-size: 11px;
    color: #6e7681;
    margin-top: 16px;
  }
</style>
</head>
<body>
  <div class="card">
    <h1>🔐 String Session Generator</h1>
    <p class="subtitle">Telethon • Secure • Fast</p>

    <div class="disclaimer">
      <b>⚠ Disclaimer:</b> Never share your string session with anyone.
      Whoever holds it can fully access your Telegram account.
      Use this tool at your own risk.
    </div>

    <!-- STEP 1: Phone + Credentials -->
    <div id="step1">
      <div class="row">
        <div>
          <label>API ID</label>
          <input type="text" id="apiId" placeholder="Your API ID" />
        </div>
        <div>
          <label>API Hash</label>
          <input type="text" id="apiHash" placeholder="Your API Hash" />
        </div>
      </div>
      <label>Phone Number</label>
      <input type="text" id="phone" placeholder="+91XXXXXXXXXX" />
      <div class="error hidden" id="err1"></div>
      <button onclick="sendCode()">Send Code</button>
    </div>

    <!-- STEP 2: OTP -->
    <div id="step2" class="hidden">
      <label>Enter OTP sent to your Telegram</label>
      <div class="otp-boxes">
        <input maxlength="1" class="otp" />
        <input maxlength="1" class="otp" />
        <input maxlength="1" class="otp" />
        <input maxlength="1" class="otp" />
        <input maxlength="1" class="otp" />
      </div>
      <div class="error hidden" id="err2"></div>
      <button onclick="verifyOtp()">Verify OTP</button>
    </div>

    <!-- STEP 3: 2FA -->
    <div id="step3" class="hidden">
      <label>Two-Factor Password</label>
      <input type="password" id="password" placeholder="Your 2FA password" />
      <div class="error hidden" id="err3"></div>
      <button onclick="submitPwd()">Submit Password</button>
    </div>

    <!-- STEP 4: Done -->
    <div id="step4" class="hidden">
      <div class="success-title">✅ Session Generated Successfully</div>
      <div class="session-box" id="sessionOut"></div>
      <button onclick="copySession()">📋 Copy Session</button>
      <div class="warn">⚠ Keep this session private and secure.</div>
    </div>

    <!-- Loader -->
    <div id="loader" class="loader hidden">⏳ Processing...</div>

    <footer>Built with Telethon • v1.0</footer>
  </div>

<script>
  const otpInputs = document.querySelectorAll('.otp');
  otpInputs.forEach((inp, i) => {
    inp.addEventListener('input', () => {
      if (inp.value && i < otpInputs.length - 1) otpInputs[i + 1].focus();
    });
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !inp.value && i > 0) otpInputs[i - 1].focus();
    });
  });

  function showStep(n) {
    ['step1','step2','step3','step4'].forEach(s => document.getElementById(s).classList.add('hidden'));
    document.getElementById('step' + n).classList.remove('hidden');
  }
  function showLoader(v) {
    document.getElementById('loader').classList.toggle('hidden', !v);
  }
  function showErr(id, msg) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.classList.remove('hidden');
  }
  function clearErr(id) {
    document.getElementById(id).classList.add('hidden');
  }

  async function sendCode() {
    clearErr('err1');
    const phone = document.getElementById('phone').value.trim();
    const apiId = document.getElementById('apiId').value.trim();
    const apiHash = document.getElementById('apiHash').value.trim();
    if (!phone) return showErr('err1', 'Please enter phone number');
    showLoader(true);
    const res = await fetch('/submit_phone', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ phone, api_id: apiId, api_hash: apiHash })
    });
    const data = await res.json();
    showLoader(false);
    if (data.status === 'ok') showStep(2);
    else showErr('err1', data.message || 'Error');
  }

  async function verifyOtp() {
    clearErr('err2');
    const phone = document.getElementById('phone').value.trim();
    const code = Array.from(otpInputs).map(i => i.value).join('');
    if (code.length < 5) return showErr('err2', 'Enter full OTP');
    showLoader(true);
    const res = await fetch('/submit_otp', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ phone, code })
    });
    const data = await res.json();
    showLoader(false);
    if (data.status === 'ok') {
      document.getElementById('sessionOut').textContent = data.session;
      showStep(4);
    } else if (data.status === '2fa_needed') {
      showStep(3);
    } else {
      showErr('err2', data.message || 'Invalid OTP');
    }
  }

  async function submitPwd() {
    clearErr('err3');
    const phone = document.getElementById('phone').value.trim();
    const password = document.getElementById('password').value;
    if (!password) return showErr('err3', 'Enter password');
    showLoader(true);
    const res = await fetch('/submit_password', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ phone, password })
    });
    const data = await res.json();
    showLoader(false);
    if (data.status === 'ok') {
      document.getElementById('sessionOut').textContent = data.session;
      showStep(4);
    } else {
      showErr('err3', data.message || 'Wrong password');
    }
  }

  function copySession() {
    const text = document.getElementById('sessionOut').textContent;
    navigator.clipboard.writeText(text).then(() => {
      alert('✅ Session copied to clipboard!');
    });
  }
</script>
</body>
</html>
"""


def get_creds(data):
    """Extract api_id/api_hash from payload with fallback to defaults."""
    try:
        api_id = int(str(data.get("api_id", "")).strip() or DEFAULT_API_ID)
    except ValueError:
        api_id = DEFAULT_API_ID
    api_hash = str(data.get("api_hash", "")).strip() or DEFAULT_API_HASH
    return api_id, api_hash


@app.route('/')
async def index():
    return await render_template_string(HTML_TEMPLATE)


@app.route('/submit_phone', methods=['POST'])
async def submit_phone():
    data = await request.get_json() or {}
    phone = str(data.get("phone", "")).strip().replace(" ", "")

    if not phone:
        return jsonify({"status": "error", "message": "Phone number missing."})

    api_id, api_hash = get_creds(data)
    client = None

    try:
        client = TelegramClient(
            StringSession(),
            api_id,
            api_hash,
            device_model="Telegram Web",
            system_version="Windows Web",
            app_version="1.0.0"
        )
        await client.connect()
        send_code = await client.send_code_request(phone)

        user_sessions[phone] = {
            "client": client,
            "phone_code_hash": send_code.phone_code_hash,
            "api_id": api_id,
            "api_hash": api_hash,
        }
        return jsonify({"status": "ok"})

    except Exception as e:
        if client:
            await client.disconnect()
        return jsonify({"status": "error", "message": str(e)})


@app.route('/submit_otp', methods=['POST'])
async def submit_otp():
    data = await request.get_json() or {}
    phone = str(data.get("phone", "")).strip()
    code = str(data.get("code", "")).strip()

    if phone not in user_sessions:
        return jsonify({"status": "error", "message": "Session context missing. Reload page."})

    session_data = user_sessions[phone]
    client = session_data["client"]
    phone_code_hash = session_data["phone_code_hash"]

    try:
        if not client.is_connected():
            await client.connect()

        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        session_str = client.session.save()
        await client.disconnect()
        user_sessions.pop(phone, None)

        return jsonify({"status": "ok", "session": session_str})

    except SessionPasswordNeededError:
        return jsonify({"status": "2fa_needed"})

    except Exception:
        return jsonify({"status": "error", "message": "Invalid OTP. Try again."})


@app.route('/submit_password', methods=['POST'])
async def submit_password():
    data = await request.get_json() or {}
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", "")).strip()

    if phone not in user_sessions:
        return jsonify({"status": "error", "message": "Session context missing. Reload page."})

    client = user_sessions[phone]["client"]

    try:
        if not client.is_connected():
            await client.connect()

        await client.sign_in(password=password)
        session_str = client.session.save()
        await client.disconnect()
        user_sessions.pop(phone, None)

        return jsonify({"status": "ok", "session": session_str})

    except Exception:
        return jsonify({"status": "error", "message": "Wrong password. Try again."})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
