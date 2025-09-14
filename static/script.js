document.addEventListener('DOMContentLoaded', () => {

// --- HOST CONFIGURATION (AUTOMATIC) ---
// This code automatically detects if the app is running locally or on the live server.
// You no longer need to change this manually.
let HOST;
let API_PROTOCOL;
let WS_PROTOCOL;

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // We are on the local development machine
    HOST = 'localhost:8000';
    API_PROTOCOL = 'http:';
    WS_PROTOCOL = 'ws:';
} else {
    // We are on the live, deployed server (Render)
    HOST = 'mescon.onrender.com';
    API_PROTOCOL = 'https:';
    WS_PROTOCOL = 'wss:';
}

const API_BASE_URL = `${API_PROTOCOL}//${HOST}`;
const WS_BASE_URL = `${WS_PROTOCOL}//${HOST}`;


    // --- DOM ELEMENT REFERENCES --- //
    const body = document.body;
    const loginSection = document.getElementById('login-section');
    const verifySection = document.getElementById('verify-section');
    const chatSection = document.getElementById('chat-section');
    const sendOtpForm = document.getElementById('send-otp-form');
    const mobileInput = document.getElementById('mobile');
    const mobileForVerifySpan = document.getElementById('mobile-for-verify');
    const verifyOtpForm = document.getElementById('verify-otp-form');
    const otpInput = document.getElementById('otp');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const sendBtnIcon = document.getElementById('send-btn-icon');
    const messagesContainer = document.getElementById('messages');
    const chatListContainer = document.getElementById('chat-list-container');
    const chatHeader = document.getElementById('chat-header');
    const welcomeScreen = document.getElementById('welcome-screen');
    const activeChatScreen = document.getElementById('active-chat-screen');
    const searchInput = document.getElementById('search-input');
    const myAvatarImg = document.getElementById('my-avatar');
    // Modals
    const contactModal = document.getElementById('contact-modal');
    const addContactBtn = document.getElementById('add-contact-btn');
    const cancelContactModalBtn = document.getElementById('cancel-contact-modal');
    const contactForm = document.getElementById('contact-form');
    const contactNumberInput = document.getElementById('contact-number');
    const contactNameInput = document.getElementById('contact-name');
    const contactModalTitle = document.getElementById('contact-modal-title');
    const profileModal = document.getElementById('profile-modal');
    const profileBtn = document.getElementById('profile-btn');
    const cancelProfileModalBtn = document.getElementById('cancel-profile-modal');
    const profileForm = document.getElementById('profile-form');
    const profileNumberP = document.getElementById('profile-number');
    const profileNameInput = document.getElementById('profile-name');
    const profileAvatarInput = document.getElementById('profile-avatar');
    // Call Elements
    const callScreen = document.getElementById('call-screen');
    const callDragHandle = document.getElementById('call-drag-handle');
    const callWindowTitle = document.getElementById('call-window-title');
    const videoCallContainer = document.getElementById('video-call-container');
    const voiceCallContainer = document.getElementById('voice-call-container');
    const localVideo = document.getElementById('local-video');
    const remoteVideo = document.getElementById('remote-video');
    const hangUpBtn = document.getElementById('hang-up-btn');
    const voiceCallAvatar = document.getElementById('voice-call-avatar');
    const voiceCallName = document.getElementById('voice-call-name');
    const voiceCallStatus = document.getElementById('voice-call-status');
    const incomingCallModal = document.getElementById('incoming-call-modal');
    const callerAvatar = document.getElementById('caller-avatar');
    const callerName = document.getElementById('caller-name');
    const callTypeText = document.getElementById('call-type-text');
    const acceptCallBtn = document.getElementById('accept-call-btn');
    const declineCallBtn = document.getElementById('decline-call-btn');
    const minimizeCallBtn = document.getElementById('minimize-call-btn');
    const maximizeCallBtn = document.getElementById('maximize-call-btn');

    // --- APP STATE --- //
    let websocket;
    let activeChatId = null;
    let contacts = [];
    let allMessages = {};
    let isEditingContact = false;
    // WebRTC State
    let peerConnection;
    let localStream;
    let remoteStream;
    let incomingCallData = null;
    const iceServers = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
        ]
    };

    // --- AUTHENTICATION LOGIC --- //
    sendOtpForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const mobile = mobileInput.value;
        try {
            const response = await fetch(`${API_BASE_URL}/auth/send-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mobile: mobile })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to send OTP.');
            showNotification(`An OTP has been sent to your number.`);
            mobileForVerifySpan.textContent = mobile;
            loginSection.style.display = 'none';
            verifySection.style.display = 'block';
        } catch (error) {
            console.error('Send OTP Error:', error);
            showNotification(`Error: ${error.message}`, true);
        }
    });

    verifyOtpForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const mobile = mobileForVerifySpan.textContent;
        const otp = otpInput.value;
        try {
            const response = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mobile: mobile, otp: otp })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to verify OTP.');
            localStorage.setItem('access_token', data.access_token);
            verifySection.style.display = 'none';
            chatSection.style.display = 'flex';
            body.classList.add('chat-active');
            initializeChat();
        } catch (error) {
            console.error('Verify OTP Error:', error);
            showNotification(`Error: ${error.message}`, true);
        }
    });

    // --- CHAT INITIALIZATION --- //
    async function initializeChat() {
        await loadInitialData();
        renderChatList();
        connectWebSocket();
        setupEventListeners();
    }

    function connectWebSocket() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            showNotification('Authentication token not found. Please log in again.', true);
            return;
        }
        websocket = new WebSocket(`${WS_BASE_URL}/chat/ws?token=${token}`);
        websocket.onopen = () => {
            console.log('WebSocket connection established.');
            displaySystemMessage('You are now connected.');
        };
        websocket.onmessage = (event) => {
            const msgData = JSON.parse(event.data);
            switch (msgData.type) {
                case 'chat_message':
                    handleChatMessage(msgData);
                    break;
                case 'webrtc_offer':
                    handleOffer(msgData);
                    break;
                case 'webrtc_answer':
                    handleAnswer(msgData);
                    break;
                case 'webrtc_ice_candidate':
                    handleIceCandidate(msgData);
                    break;
                case 'call_ended':
                    endCall(false);
                    break;
                case 'call_declined':
                    showNotification("Call declined.");
                    endCall(false);
                    break;
            }
        };
        websocket.onclose = () => {
            console.log('WebSocket connection closed. Reconnecting...');
            displaySystemMessage('Connection lost. Reconnecting...');
            setTimeout(connectWebSocket, 5000);
        };
        websocket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            websocket.close();
        };
    }

    function handleChatMessage(msgData) {
        console.log('Message from server:', msgData);
        const myNumber = jwt_decode(localStorage.getItem('access_token')).sub;
        const contactId = msgData.sender_id === myNumber ? msgData.recipient_id : msgData.sender_id;

        if (!allMessages[contactId]) {
            allMessages[contactId] = { messages: [], unread: 0 };
        }

        const senderType = msgData.sender_id === myNumber ? 'me' : 'them';

        allMessages[contactId].messages.push({
            text: msgData.text,
            sender: senderType,
            timestamp: msgData.timestamp
        });

        if (senderType === 'them' && contactId !== activeChatId) {
            allMessages[contactId].unread++;
        }
        if (contactId === activeChatId) {
            renderMessages(activeChatId);
        }
        renderChatList();
    }


    // --- EVENT LISTENERS & UI LOGIC --- //
    function setupEventListeners() {
        messageForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const text = messageInput.value.trim();
            if (websocket && text && activeChatId) {
                const messagePayload = JSON.stringify({ type: 'chat_message', recipient_id: activeChatId, text: text });
                websocket.send(messagePayload);
                messageInput.value = '';
                updateSendButtonIcon();
                messageInput.focus();
            }
        });
        messageInput.addEventListener('input', updateSendButtonIcon);
        chatListContainer.addEventListener('click', (e) => {
            const chatItem = e.target.closest('[data-contact-id]');
            if (chatItem) handleSelectChat(chatItem.dataset.contactId);
        });
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const filteredContacts = contacts.filter(c => c.name.toLowerCase().includes(searchTerm));
            renderChatList(filteredContacts);
        });
        window.addEventListener('resize', handleResize);
        addContactBtn.addEventListener('click', openContactModalForAdd);
        cancelContactModalBtn.addEventListener('click', () => contactModal.classList.add('hidden'));
        contactForm.addEventListener('submit', handleSaveContact);
        profileBtn.addEventListener('click', openProfileModal);
        cancelProfileModalBtn.addEventListener('click', () => profileModal.classList.add('hidden'));
        profileForm.addEventListener('submit', handleSaveProfile);
        chatHeader.addEventListener('click', (e) => {
            if (e.target.closest('#edit-contact-btn')) openContactModalForEdit();
            if (e.target.closest('#delete-contact-btn')) handleDeleteContact();
            if (e.target.closest('#video-call-btn')) startCall(true); // isVideo = true
            if (e.target.closest('#voice-call-btn')) startCall(false); // isVideo = false
        });
        hangUpBtn.addEventListener('click', () => endCall(true));
        acceptCallBtn.addEventListener('click', handleAcceptCall);
        declineCallBtn.addEventListener('click', handleDeclineCall);

        // Call Window Controls
        minimizeCallBtn.addEventListener('click', () => {
            callScreen.classList.toggle('minimized');
        });
        maximizeCallBtn.addEventListener('click', () => {
            callScreen.classList.toggle('maximized');
            if(callScreen.classList.contains('maximized')) {
                callScreen.style.top = '50%';
                callScreen.style.left = '50%';
            }
            callDragHandle.style.cursor = callScreen.classList.contains('maximized') ? 'default' : 'move';
        });

        // Draggable Call Window Logic
        let isDragging = false;
        let offsetX, offsetY;
        callDragHandle.addEventListener('mousedown', (e) => {
            if (callScreen.classList.contains('maximized')) return;
            isDragging = true;
            offsetX = e.clientX - callScreen.offsetLeft;
            offsetY = e.clientY - callScreen.offsetTop;
            callDragHandle.style.cursor = 'grabbing';
        });
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            callScreen.style.left = `${e.clientX - offsetX}px`;
            callScreen.style.top = `${e.clientY - offsetY}px`;
        });
        document.addEventListener('mouseup', () => {
            isDragging = false;
            callDragHandle.style.cursor = 'move';
        });
    }

    // --- MODAL & CONTACTS LOGIC ---
    function openContactModalForAdd() {
        isEditingContact = false;
        contactModalTitle.textContent = 'Add New Contact';
        contactForm.reset();
        contactNumberInput.disabled = false;
        contactModal.classList.remove('hidden');
    }

    function openContactModalForEdit() {
        isEditingContact = true;
        const contact = contacts.find(c => c.id === activeChatId);
        if (!contact) return;
        contactModalTitle.textContent = 'Edit Contact';
        contactNumberInput.value = contact.id;
        contactNumberInput.disabled = true;
        contactNameInput.value = contact.name;
        contactModal.classList.remove('hidden');
    }

    async function openProfileModal() {
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${API_BASE_URL}/api/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Failed to fetch profile.');
            const profile = await response.json();
            profileNumberP.textContent = profile.id;
            profileNameInput.value = profile.name;
            profileAvatarInput.value = profile.avatar;
            profileModal.classList.remove('hidden');
        } catch (error) {
            console.error('Profile Error:', error);
            showNotification(`Error: ${error.message}`, true);
        }
    }

    async function handleSaveProfile(event) {
        event.preventDefault();
        const name = profileNameInput.value;
        const avatar = profileAvatarInput.value;
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${API_BASE_URL}/api/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name, avatar })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to save profile.');
            showNotification(data.message);
            myAvatarImg.src = avatar;
            profileModal.classList.add('hidden');
        } catch (error) {
            console.error('Save Profile Error:', error);
            showNotification(`Error: ${error.message}`, true);
        }
    }

    async function handleSaveContact(event) {
        event.preventDefault();
        const number = contactNumberInput.value;
        const name = contactNameInput.value;
        const token = localStorage.getItem('access_token');
        const url = isEditingContact ? `${API_BASE_URL}/api/contacts/${number}` : `${API_BASE_URL}/api/contacts`;
        const method = isEditingContact ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ number, name })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to save contact.');
            showNotification(data.message);
            contactModal.classList.add('hidden');
            await loadInitialData();
            renderChatList();
            if (isEditingContact) {
                const updatedContact = contacts.find(c => c.id === activeChatId);
                if (updatedContact) renderChatHeader(updatedContact);
            }
        } catch (error) {
            console.error('Save Contact Error:', error);
            showNotification(`Error: ${error.message}`, true);
        }
    }

    async function handleDeleteContact() {
        if (!activeChatId || !confirm(`Are you sure you want to delete this contact?`)) return;
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${API_BASE_URL}/api/contacts/${activeChatId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Failed to delete contact.');
            showNotification(data.message);
            await loadInitialData();
            handleBackToList();
        } catch (error) {
            console.error('Delete Contact Error:', error);
            showNotification(`Error: ${error.message}`, true);
        }
    }

    // --- UI RENDER FUNCTIONS ---
    function handleSelectChat(contactId) {
        activeChatId = contactId;
        if (allMessages[contactId]) {
            allMessages[contactId].unread = 0;
        }
        const contact = contacts.find(c => c.id === contactId);
        renderChatList();
        renderChatHeader(contact);
        renderMessages(activeChatId);
        welcomeScreen.style.display = 'none';
        activeChatScreen.style.display = 'flex';
        if (window.innerWidth < 768) {
            const chatListPanel = document.getElementById('chat-list-panel');
            const chatWindowPanel = document.getElementById('chat-window-panel');
            chatListPanel.classList.add('hidden');
            chatWindowPanel.classList.remove('hidden');
            chatWindowPanel.classList.add('flex');
        }
    }

    function handleBackToList() {
        activeChatId = null;
        const chatListPanel = document.getElementById('chat-list-panel');
        const chatWindowPanel = document.getElementById('chat-window-panel');
        chatListPanel.classList.remove('hidden');
        if (window.innerWidth >= 768) {
            chatWindowPanel.classList.add('md:flex');
        } else {
            chatWindowPanel.classList.add('hidden');
        }
        welcomeScreen.style.display = 'flex';
        activeChatScreen.style.display = 'none';
        renderChatList();
    }

    function renderMessages(contactId) {
        messagesContainer.innerHTML = '';
        const conversation = allMessages[contactId];
        if (!conversation || !conversation.messages) return;
        conversation.messages.forEach(msg => {
            const isMe = msg.sender === 'me';
            const bubble = document.createElement('div');
            bubble.className = `flex ${isMe ? 'justify-end' : 'justify-start'} mb-4`;
            bubble.innerHTML = `
                <div class="rounded-lg px-4 py-2 max-w-sm ${isMe ? 'bg-teal-800 text-white' : 'bg-gray-700 text-white'}">
                    <p class="break-words">${msg.text}</p>
                    <div class="flex justify-end items-center mt-1">
                        <p class="text-xs text-gray-400 mr-1">${formatTimestamp(msg.timestamp)}</p>
                    </div>
                </div>`;
            messagesContainer.appendChild(bubble);
        });
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function renderChatHeader(contact) {
        chatHeader.innerHTML = `
            <button id="back-to-list-btn" class="text-white mr-2 md:hidden"><i class="fa-solid fa-arrow-left"></i></button>
            <img src="${contact.avatar}" alt="${contact.name}" class="w-10 h-10 rounded-full mr-4">
            <div class="flex-1"><h3 class="text-lg font-semibold text-white">${contact.name}</h3><p class="text-sm text-gray-400">${contact.online ? 'Online' : 'Offline'}</p></div>
            <div class="flex items-center space-x-4">
                <button id="voice-call-btn" title="Voice Call" class="text-gray-400 hover:text-white"><i class="fa-solid fa-phone"></i></button>
                <button id="video-call-btn" title="Video Call" class="text-gray-400 hover:text-white"><i class="fa-solid fa-video"></i></button>
                <button id="edit-contact-btn" title="Edit Contact" class="text-gray-400 hover:text-white"><i class="fa-solid fa-pen-to-square"></i></button>
                <button id="delete-contact-btn" title="Delete Contact" class="text-gray-400 hover:text-white"><i class="fa-solid fa-trash"></i></button>
            </div>
        `;
        document.getElementById('back-to-list-btn').addEventListener('click', handleBackToList);
    }

    function renderChatList(contactsToRender = contacts) {
        chatListContainer.innerHTML = '';
        contactsToRender.forEach(contact => {
            const conversation = allMessages[contact.id] || { messages: [], unread: 0 };
            const lastMsg = conversation.messages.length > 0 ? conversation.messages[conversation.messages.length - 1] : { text: 'No messages yet', timestamp: null };
            const unreadCount = conversation.unread || 0;
            const item = document.createElement('div');
            item.className = `flex items-center p-3 cursor-pointer hover:bg-gray-800 ${contact.id === activeChatId ? 'bg-gray-700' : ''}`;
            item.dataset.contactId = contact.id;
            item.innerHTML = `
                <img src="${contact.avatar}" alt="${contact.name}" class="w-12 h-12 rounded-full mr-4">
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-center">
                        <p class="text-lg font-medium text-white truncate">${contact.name}</p>
                        <p class="text-xs text-gray-400">${lastMsg.timestamp ? formatTimestamp(lastMsg.timestamp, true) : ''}</p>
                    </div>
                    <div class="flex justify-between items-center mt-1">
                        <p class="text-sm text-gray-400 truncate">${lastMsg.text}</p>
                        ${unreadCount > 0 ? `<span class="bg-green-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">${unreadCount}</span>` : ''}
                    </div>
                </div>`;
            chatListContainer.appendChild(item);
        });
    }

    // --- WebRTC LOGIC ---
    async function createPeerConnection() {
        peerConnection = new RTCPeerConnection(iceServers);
        remoteStream = new MediaStream();
        remoteVideo.srcObject = remoteStream;

        if (localStream) {
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        }

        peerConnection.ontrack = event => {
            event.streams[0].getTracks().forEach(track => {
                remoteStream.addTrack(track);
            });
        };

        peerConnection.onicecandidate = event => {
            if (event.candidate) {
                websocket.send(JSON.stringify({
                    type: 'webrtc_ice_candidate',
                    recipient_id: activeChatId,
                    candidate: event.candidate
                }));
            }
        };
    }

    async function startCall(isVideo) {
        const constraints = { video: isVideo, audio: true };
        try {
            localStream = await navigator.mediaDevices.getUserMedia(constraints);
            if (isVideo) {
                localVideo.srcObject = localStream;
            }

            const contact = contacts.find(c => c.id === activeChatId);
            showCallUI(isVideo, contact, true);

            await createPeerConnection();

            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);

            websocket.send(JSON.stringify({
                type: 'webrtc_offer',
                recipient_id: activeChatId,
                offer: offer,
                callType: isVideo ? 'video' : 'voice'
            }));
        } catch (error) {
            console.error("Error starting call:", error);
            showNotification("Could not start call. Check camera/mic permissions.", true);
            endCall(false);
        }
    }

    function handleOffer(data) {
        if (peerConnection) {
            console.log("Ignoring new call offer while already in a call.");
            return;
        }
        const contact = contacts.find(c => c.id === data.sender_id);
        if (!contact) return;

        incomingCallData = data;
        callerAvatar.src = contact.avatar;
        callerName.textContent = contact.name;
        callTypeText.textContent = `Incoming ${data.callType} call...`;
        incomingCallModal.classList.remove('hidden');
    }

    async function handleAcceptCall() {
        if (!incomingCallData) return;
        const data = incomingCallData;
        const callType = data.callType || 'video';
        const constraints = { video: (callType === 'video'), audio: true };

        try {
            localStream = await navigator.mediaDevices.getUserMedia(constraints);
            if (callType === 'video') {
                localVideo.srcObject = localStream;
            }

            handleSelectChat(data.sender_id);
            const contact = contacts.find(c => c.id === data.sender_id);
            showCallUI(callType === 'video', contact, false);

            await createPeerConnection();
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));

            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);

            websocket.send(JSON.stringify({
                type: 'webrtc_answer',
                recipient_id: data.sender_id,
                answer: answer
            }));
        } catch (error) {
             console.error("Error answering call:", error);
             showNotification("Could not answer call. Check camera/mic permissions.", true);
             endCall(false);
        } finally {
            incomingCallModal.classList.add('hidden');
            incomingCallData = null;
        }
    }

    function handleDeclineCall() {
        if (!incomingCallData) return;
        websocket.send(JSON.stringify({
            type: 'call_declined',
            recipient_id: incomingCallData.sender_id
        }));
        incomingCallModal.classList.add('hidden');
        incomingCallData = null;
    }

    async function handleAnswer(data) {
        if (peerConnection) {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
            voiceCallStatus.textContent = "In call...";
        }
    }

    async function handleIceCandidate(data) {
        if (peerConnection && data.candidate) {
            await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
    }

    function showCallUI(isVideo, contact, isOutgoing = false) {
        if (isVideo) {
            videoCallContainer.classList.remove('hidden');
            voiceCallContainer.classList.add('hidden');
        } else {
            voiceCallContainer.classList.remove('hidden');
            videoCallContainer.classList.add('hidden');
            voiceCallAvatar.src = contact.avatar;
            voiceCallName.textContent = contact.name;
            voiceCallStatus.textContent = isOutgoing ? "Ringing..." : "In call...";
        }
        callScreen.classList.remove('hidden', 'minimized', 'maximized');
        callScreen.classList.add('flex');
    }

    function endCall(notifyPeer) {
        if (notifyPeer && activeChatId) {
             websocket.send(JSON.stringify({
                type: 'call_ended',
                recipient_id: activeChatId
            }));
        }
        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        localVideo.srcObject = null;
        remoteVideo.srcObject = null;
        callScreen.classList.add('hidden');
        callScreen.classList.remove('flex');
    }

    // --- UTILITY FUNCTIONS ---
    function handleResize() {
        if (window.innerWidth >= 768) {
            const chatListPanel = document.getElementById('chat-list-panel');
            const chatWindowPanel = document.getElementById('chat-window-panel');
            chatListPanel.classList.remove('hidden');
            chatWindowPanel.classList.remove('hidden');
            chatWindowPanel.classList.add('flex');
        } else {
            if (activeChatId) {
                const chatListPanel = document.getElementById('chat-list-panel');
                const chatWindowPanel = document.getElementById('chat-window-panel');
                chatListPanel.classList.add('hidden');
                chatWindowPanel.classList.remove('hidden');
                chatWindowPanel.classList.add('flex');
            } else {
                const chatListPanel = document.getElementById('chat-list-panel');
                const chatWindowPanel = document.getElementById('chat-window-panel');
                chatListPanel.classList.remove('hidden');
                chatWindowPanel.classList.add('hidden');
            }
        }
    }

    function displaySystemMessage(message) {
        const el = document.createElement('div');
        el.className = 'text-center text-sm text-gray-500 my-2 italic';
        el.textContent = message;
        messagesContainer.appendChild(el);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function updateSendButtonIcon() {
        if (messageInput.value.trim()) {
            sendBtnIcon.className = 'fa-solid fa-paper-plane text-2xl';
        } else {
            sendBtnIcon.className = 'fa-solid fa-microphone text-2xl';
        }
    }

    function showNotification(message, isError = false) {
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.className = 'fixed top-5 right-5 p-4 rounded-lg shadow-lg text-white z-50';
        notification.classList.add(isError ? 'bg-red-600' : 'bg-blue-600');
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 4000);
    }

    function formatTimestamp(isoString, isShort = false) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const timeFormat = { hour: 'numeric', minute: 'numeric', hour12: true };
        if (date.toDateString() === today.toDateString()) {
            return isShort ? date.toLocaleTimeString([], timeFormat) : `Today, ${date.toLocaleTimeString([], timeFormat)}`;
        }
        if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        }
        return isShort ? date.toLocaleDateString() : date.toLocaleDateString();
    }

    // A simple function to decode JWTs without an external library
    function jwt_decode(token) {
        try {
            return JSON.parse(atob(token.split('.')[1]));
        } catch (e) {
            return null;
        }
    }

    async function loadInitialData() {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        try {
            const usersResponse = await fetch(`${API_BASE_URL}/api/users`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!usersResponse.ok) throw new Error('Failed to fetch user list.');
            contacts = await usersResponse.json();

            const profileResponse = await fetch(`${API_BASE_URL}/api/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
             if (!profileResponse.ok) throw new Error('Failed to fetch profile.');
            const profile = await profileResponse.json();
            myAvatarImg.src = profile.avatar;

            const historyResponse = await fetch(`${API_BASE_URL}/chat/history`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!historyResponse.ok) throw new Error('Failed to fetch chat history.');
            const history = await historyResponse.json();

            allMessages = {};
            for (const contactId in history) {
                allMessages[contactId] = { messages: history[contactId], unread: 0 };
            }

        } catch (error) {
            console.error(error);
            showNotification("Could not load initial data.", true);
            contacts = [];
            allMessages = {};
        }
    }
});