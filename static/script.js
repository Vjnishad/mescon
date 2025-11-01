// ==========================
// MESCON FRONTEND MAIN.JS
// ==========================

// 🔹 Environment Auto-Detection
let HOST, API_PROTOCOL, WS_PROTOCOL;
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
  HOST = "localhost:8000";
  API_PROTOCOL = "http:";
  WS_PROTOCOL = "ws:";
} else {
  HOST = "mescon.onrender.com";
  API_PROTOCOL = "https:";
  WS_PROTOCOL = "wss:";
}

const BASE_API = `${API_PROTOCOL}//${HOST}`;
const WS_BASE = `${WS_PROTOCOL}//${HOST}`;

// ==========================
// GLOBAL STATE
// ==========================
let ws = null;
let reconnectTimer = null;
let accessToken = localStorage.getItem("access_token");
let currentChatUser = null;
let localStream = null;
let peerConnection = null;

// ==========================
// UTILITY FUNCTIONS
// ==========================
function notify(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function jwtDecode(token) {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch (e) {
    return null;
  }
}

function formatTimestamp(ts) {
  const date = new Date(ts);
  const today = new Date();
  const yesterday = new Date(Date.now() - 86400000);
  if (date.toDateString() === today.toDateString())
    return "Today " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (date.toDateString() === yesterday.toDateString())
    return "Yesterday " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// ==========================
// API HELPERS
// ==========================
async function apiPost(url, body) {
  const res = await fetch(`${BASE_API}${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: accessToken ? `Bearer ${accessToken}` : undefined,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiGet(url) {
  const res = await fetch(`${BASE_API}${url}`, {
    headers: {
      Authorization: accessToken ? `Bearer ${accessToken}` : undefined,
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ==========================
// AUTHENTICATION
// ==========================
const otpForm = document.getElementById("sendOtpForm");
const verifyForm = document.getElementById("verifyOtpForm");

if (otpForm) {
  otpForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const phone = document.getElementById("phone").value;
    try {
      await apiPost("/auth/send-otp", { phone });
      notify("OTP sent successfully!", "success");
      document.querySelector(".otp-section").style.display = "block";
    } catch (err) {
      notify("Failed to send OTP", "error");
    }
  });
}

if (verifyForm) {
  verifyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const phone = document.getElementById("phone").value;
    const otp = document.getElementById("otp").value;
    try {
      const res = await apiPost("/auth/verify-otp", { phone, otp });
      accessToken = res.access_token;
      localStorage.setItem("access_token", accessToken);
      notify("Login successful!", "success");
      initApp();
    } catch {
      notify("Invalid OTP", "error");
    }
  });
}

// ==========================
// WEBSOCKET CHAT
// ==========================
function connectWebSocket() {
  if (!accessToken) return;

  ws = new WebSocket(`${WS_BASE}/chat/ws?token=${accessToken}`);

  ws.onopen = () => {
    console.log("✅ WebSocket connected");
    notify("Connected to server", "success");
    if (reconnectTimer) {
      clearInterval(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "chat") renderMessage(msg);
    if (msg.type === "webrtc_offer") handleOffer(msg);
    if (msg.type === "webrtc_answer") handleAnswer(msg);
    if (msg.type === "ice_candidate") handleIceCandidate(msg);
  };

  ws.onclose = () => {
    console.warn("❌ WebSocket disconnected, retrying...");
    reconnectTimer = setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = (err) => console.error("WebSocket error", err);
}

// ==========================
// CHAT UI
// ==========================
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatBox = document.getElementById("chatBox");

if (chatForm) {
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (text && currentChatUser && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "chat", to: currentChatUser, message: text }));
      renderMessage({ message: text, self: true, timestamp: new Date() });
      chatInput.value = "";
    }
  });
}

function renderMessage(msg) {
  const div = document.createElement("div");
  div.className = msg.self ? "msg-self" : "msg-other";
  div.innerHTML = `
    <div class="msg-text">${msg.message}</div>
    <div class="msg-time">${formatTimestamp(msg.timestamp)}</div>
  `;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ==========================
// WEBRTC HANDLERS
// ==========================
async function handleOffer(msg) {
  const pc = createPeerConnection(msg.from);
  await pc.setRemoteDescription(new RTCSessionDescription(msg.offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  ws.send(JSON.stringify({ type: "webrtc_answer", to: msg.from, answer }));
}

async function handleAnswer(msg) {
  if (peerConnection) await peerConnection.setRemoteDescription(new RTCSessionDescription(msg.answer));
}

async function handleIceCandidate(msg) {
  if (peerConnection) await peerConnection.addIceCandidate(new RTCIceCandidate(msg.candidate));
}

function createPeerConnection(remoteUser) {
  peerConnection = new RTCPeerConnection({
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
  });

  peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
      ws.send(JSON.stringify({ type: "ice_candidate", to: remoteUser, candidate: event.candidate }));
    }
  };

  peerConnection.ontrack = (event) => {
    const remoteVideo = document.getElementById("remoteVideo");
    if (remoteVideo) remoteVideo.srcObject = event.streams[0];
  };

  if (localStream) {
    localStream.getTracks().forEach((track) => peerConnection.addTrack(track, localStream));
  }

  return peerConnection;
}

// ==========================
// APP INITIALIZATION
// ==========================
async function initApp() {
  try {
    const user = await apiGet("/api/profile");
    document.getElementById("userName").textContent = user.name || "User";
    connectWebSocket();
    notify("Welcome back!", "success");
  } catch (err) {
    console.error(err);
    notify("Session expired, please log in again.", "error");
    localStorage.removeItem("access_token");
  }
}

// ==========================
// AUTO INIT ON LOGIN
// ==========================
if (accessToken) {
  initApp();
}
