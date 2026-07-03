import os
from quart import Quart, render_template_string, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

app = Quart(__name__)

# Core Credentials
API_ID = int(os.environ.get("API_ID", 23483842))
API_HASH = os.environ.get("API_HASH", "63f3942db5bb0bd6ab36352ca52e773b")

# In-memory storage for temporary tracking
user_sessions = {}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StringGen · Secure Telegram Session</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          'tg-blue': '#0088cc',
          'tg-dark': '#0f172a',
          'tg-surface': '#1e293b',
        },
        fontFamily: {
          sans: ['Inter', 'sans-serif'],
          mono: ['JetBrains Mono', 'monospace'],
        }
      }
    }
  }
</script>
<style>
  html, body { background: #0f172a; }
  .hidden { display: none !important; }
  .otp-box::-webkit-outer-spin-button,
  .otp-box::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
  .spinner {
    width: 18px; height: 18px; border-radius: 9999px;
    border: 2px solid rgba(255,255,255,0.15);
    border-top-color: #0088cc;
    animation: spin 0.7s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body class="font-sans text-slate-200 min-h-screen">

<div class="min-h-screen w-full flex justify-center p-5">
  <div class="w-full max-w-[420px] flex flex-col relative overflow-hidden">

    <!-- Background glow -->
    <div class="pointer-events-none absolute -top-24 -left-24 w-72 h-72 bg-tg-blue/20 blur-[100px] rounded-full"></div>

    <!-- Header -->
    <header class="relative z-10 mb-8 pt-2">
      <div class="flex items-center gap-3 mb-6">
        <div class="size-10 bg-tg-blue rounded-xl flex items-center justify-center shadow-lg shadow-tg-blue/25">
          <span class="text-white font-bold text-xl">S</span>
        </div>
        <div>
          <h1 class="text-lg font-bold leading-tight text-white">StringGen</h1>
          <p class="text-xs text-slate-400">Secure Telegram Session</p>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="flex gap-1.5" id="progress-bar">
        <div class="h-1 flex-1 bg-tg-blue rounded-full" data-step="1"></div>
        <div class="h-1 flex-1 bg-slate-700 rounded-full" data-step="2"></div>
        <div class="h-1 flex-1 bg-slate-700 rounded-full" data-step="3"></div>
        <div class="h-1 flex-1 bg-slate-700 rounded-full" data-step="4"></div>
      </div>
    </header>

    <!-- Main -->
    <main class="relative z-10 flex-1 flex flex-col">

      <div class="mb-6">
        <h2 class="text-xl font-semibold text-white mb-2" id="step-title">Connect Account</h2>
        <p class="text-sm text-slate-400" id="status-text">
          Enter your phone number with country code.
        </p>
      </div>

      <!-- Step 1: Phone -->
      <div id="step-phone" class="space-y-4">
        <div class="bg-tg-surface border border-slate-700 rounded-xl p-3 focus-within:border-tg-blue transition-colors">
          <span class="text-xs text-slate-500 block mb-0.5">Phone Number</span>
          <input
            type="tel"
            id="phone"
            placeholder="+919876543210"
            class="bg-transparent w-full focus:outline-none font-medium placeholder:text-slate-600 text-white"
          >
        </div>

        <button
          id="phoneBtn"
          onclick="sendPhone()"
          class="w-full bg-tg-blue hover:bg-tg-blue/90 text-white font-semibold py-4 rounded-xl transition-all active:scale-[0.98] shadow-lg shadow-tg-blue/25 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          Send Code
        </button>
      </div>

      <!-- Step 2: OTP -->
      <div id="step-otp" class="hidden space-y-4">
        <div class="flex justify-between gap-2">
          <input type="text" inputmode="numeric" maxlength="1" class="otp-box size-[52px] rounded-xl bg-tg-surface border border-slate-700 text-center font-mono text-xl text-white focus:outline-none focus:border-tg-blue focus:ring-2 focus:ring-tg-blue/40 transition-all">
          <input type="text" inputmode="numeric" maxlength="1" class="otp-box size-[52px] rounded-xl bg-tg-surface border border-slate-700 text-center font-mono text-xl text-white focus:outline-none focus:border-tg-blue focus:ring-2 focus:ring-tg-blue/40 transition-all">
          <input type="text" inputmode="numeric" maxlength="1" class="otp-box size-[52px] rounded-xl bg-tg-surface border border-slate-700 text-center font-mono text-xl text-white focus:outline-none focus:border-tg-blue focus:ring-2 focus:ring-tg-blue/40 transition-all">
          <input type="text" inputmode="numeric" maxlength="1" class="otp-box size-[52px] rounded-xl bg-tg-surface border border-slate-700 text-center font-mono text-xl text-white focus:outline-none focus:border-tg-blue focus:ring-2 focus:ring-tg-blue/40 transition-all">
          <input type="text" inputmode="numeric" maxlength="1" class="otp-box size-[52px] rounded-xl bg-tg-surface border border-slate-700 text-center font-mono text-xl text-white focus:outline-none focus:border-tg-blue focus:ring-2 focus:ring-tg-blue/40 transition-all">
        </div>

        <button
          id="otpBtn"
          onclick="sendOtp()"
          class="w-full bg-tg-blue hover:bg-tg-blue/90 text-white font-semibold py-4 rounded-xl transition-all active:scale-[0.98] shadow-lg shadow-tg-blue/25 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          Verify OTP
        </button>
      </div>

      <!-- Step 3: 2FA -->
      <div id="step-2fa" class="hidden space-y-4">
        <div class="bg-tg-surface border border-slate-700 rounded-xl p-3 focus-within:border-tg-blue transition-colors">
          <span class="text-xs text-slate-500 block mb-0.5">2FA Password</span>
          <input
            type="password"
            id="password"
            placeholder="Enter your 2FA password"
            class="bg-transparent w-full focus:outline-none font-medium placeholder:text-slate-600 text-white"
          >
        </div>

        <button
          id="passBtn"
          onclick="sendPassword()"
          class="w-full bg-tg-blue hover:bg-tg-blue/90 text-white font-semibold py-4 rounded-xl transition-all active:scale-[0.98] shadow-lg shadow-tg-blue/25 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          Submit Password
        </button>
      </div>

      <!-- Step 4: Success -->
      <div id="step-success" class="hidden">
        <div class="bg-tg-surface border border-slate-700 rounded-2xl p-5">
          <div class="size-14 bg-emerald-500/15 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg class="size-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <h3 class="text-center text-lg font-bold text-white mb-1">Session Generated</h3>
          <p class="text-center text-xs text-slate-400 mb-4">Your string session is ready. Keep it private.</p>

          <div
            id="token-box"
            class="bg-tg-dark rounded-lg p-3 font-mono text-[11px] leading-relaxed break-all border border-slate-800 text-slate-300 max-h-40 overflow-y-auto mb-3"
          ></div>

          <button
            class="w-full bg-slate-100 hover:bg-white text-tg-dark font-bold py-3 rounded-xl transition-all active:scale-[0.98]"
            onclick="copySession()"
          >
            Copy Session
          </button>

          <div class="mt-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg">
            <p class="text-[11px] text-rose-300 leading-snug">
              <span class="font-bold uppercase">Warning:</span>
              This string grants full account access. Never share it.
            </p>
          </div>
        </div>
      </div>

      <!-- Loader -->
      <div id="loader" class="hidden mt-4 flex items-center justify-center gap-2 text-tg-blue text-sm">
        <span class="spinner"></span>
        <span>Processing...</span>
      </div>

      <!-- Error -->
      <div id="error-msg" class="hidden mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg items-start gap-3">
        <div class="size-2 rounded-full bg-red-500 mt-1.5 shrink-0"></div>
        <p class="text-xs text-red-300 leading-snug flex-1"></p>
      </div>

    </main>

    <!-- Footer -->
    <footer class="relative z-10 mt-10 pt-6 text-center">
      <p class="text-[10px] text-slate-500 uppercase tracking-widest">
        End-to-end encrypted · No data stored
      </p>
    </footer>

  </div>
</div>

<script>
let currentPhone = "";

function showError(msg) {
  const box = document.getElementById("error-msg");
  box.querySelector("p").innerText = msg;
  box.classList.remove("hidden");
  box.classList.add("flex");
}

function clearError() {
  const box = document.getElementById("error-msg");
  box.classList.add("hidden");
  box.classList.remove("flex");
}

function setLoading(status) {
  const loader = document.getElementById("loader");
  if (status) { loader.classList.remove("hidden"); loader.classList.add("flex"); }
  else { loader.classList.add("hidden"); loader.classList.remove("flex"); }
}

function setProgress(step) {
  document.querySelectorAll("#progress-bar div").forEach((el, i) => {
    el.className = "h-1 flex-1 rounded-full " + (i < step ? "bg-tg-blue" : "bg-slate-700");
  });
}

function setStep(title, status) {
  document.getElementById("step-title").innerText = title;
  document.getElementById("status-text").innerText = status;
}

async function safeAPI(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return await res.json();
}

async function sendPhone() {
  const phone = document.getElementById("phone").value.trim();
  if (!phone) return;
  currentPhone = phone;
  clearError();
  setLoading(true);
  try {
    const res = await safeAPI("/submit_phone", { phone });
    if (res.status === "ok") {
      document.getElementById("step-phone").classList.add("hidden");
      document.getElementById("step-otp").classList.remove("hidden");
      setStep("Verification", "Check Telegram for the 5-digit code.");
      setProgress(2);
      const first = document.querySelector(".otp-box");
      if (first) first.focus();
    } else {
      showError(res.message || "Something went wrong.");
    }
  } catch (err) {
    showError("Network error.");
  }
  setLoading(false);
}

async function sendOtp() {
  const inputs = document.querySelectorAll(".otp-box");
  const otp = Array.from(inputs).map(i => i.value.trim()).join("");
  if (otp.length !== 5) { showError("Enter complete OTP."); return; }
  clearError();
  setLoading(true);
  try {
    const res = await safeAPI("/submit_otp", { phone: currentPhone, code: otp });
    if (res.status === "ok") {
      showSuccess(res.session);
    } else if (res.status === "2fa_needed") {
      document.getElementById("step-otp").classList.add("hidden");
      document.getElementById("step-2fa").classList.remove("hidden");
      setStep("Two-Factor Auth", "Enter your Telegram 2FA password.");
      setProgress(3);
    } else {
      showError(res.message || "Invalid OTP.");
    }
  } catch (err) {
    showError("Network error.");
  }
  setLoading(false);
}

async function sendPassword() {
  const password = document.getElementById("password").value.trim();
  if (!password) return;
  clearError();
  setLoading(true);
  try {
    const res = await safeAPI("/submit_password", { phone: currentPhone, password });
    if (res.status === "ok") showSuccess(res.session);
    else showError(res.message || "Wrong password.");
  } catch (err) {
    showError("Network error.");
  }
  setLoading(false);
}

function showSuccess(sessionStr) {
  document.getElementById("step-phone").classList.add("hidden");
  document.getElementById("step-otp").classList.add("hidden");
  document.getElementById("step-2fa").classList.add("hidden");
  document.getElementById("step-success").classList.remove("hidden");
  setStep("All Set", "Your StringSession is ready below.");
  setProgress(4);
  document.getElementById("token-box").innerText = sessionStr;
}

async function copySession() {
  const text = document.getElementById("token-box").innerText.trim();
  if (!text) { alert("No session found!"); return; }
  try {
    await navigator.clipboard.writeText(text);
    alert("Session copied!");
  } catch {
    try {
      const t = document.createElement("textarea");
      t.value = text; document.body.appendChild(t);
      t.select(); document.execCommand("copy");
      document.body.removeChild(t);
      alert("Session copied!");
    } catch {
      alert("Copy failed. Copy manually.");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll(".otp-box");
  inputs.forEach((input, index) => {
    input.addEventListener("input", (e) => {
      let value = e.target.value.replace(/\D/g, '');
      if (value.length > 1) {
        inputs.forEach(i => i.value = "");
        value.slice(0, 5).split("").forEach((c, i) => { if (inputs[i]) inputs[i].value = c; });
        const next = Math.min(value.length, inputs.length) - 1;
        if (next >= 0) inputs[next].focus();
        return;
      }
      e.target.value = value;
      if (value && index < inputs.length - 1) inputs[index + 1].focus();
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && index > 0) inputs[index - 1].focus();
    });
    input.addEventListener("paste", (e) => {
      e.preventDefault();
      const pasted = (e.clipboardData.getData("text") || "").replace(/\D/g, '').slice(0, 5);
      inputs.forEach(i => i.value = "");
      pasted.split("").forEach((c, i) => { if (inputs[i]) inputs[i].value = c; });
      const last = Math.min(pasted.length, inputs.length) - 1;
      if (last >= 0) inputs[last].focus();
    });
  });
});
</script>

</body>
</html>
"""

@app.route('/')
async def index():
    return await render_template_string(HTML_TEMPLATE)


@app.route('/submit_phone', methods=['POST'])
async def submit_phone():
    data = await request.get_json() or {}
    phone = str(data.get("phone", "")).strip().replace(" ", "")

    if not phone:
        return jsonify({"status": "error", "message": "Phone number missing."})

    client = None
    try:
        client = TelegramClient(
            StringSession(), API_ID, API_HASH,
            device_model="Telegram Web",
            system_version="Windows Web",
            app_version="1.0.0",
        )
        await client.connect()
        send_code = await client.send_code_request(phone)
        user_sessions[phone] = {
            "client": client,
            "phone_code_hash": send_code.phone_code_hash,
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
