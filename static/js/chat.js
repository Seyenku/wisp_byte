/**
 * WispChat - Chat Interface JavaScript
 * Bootstrap 5 Integration
 */

// Global state
const chatState = {
    currentUserId: null,
    currentUsername: null,
    activeChatId: null,
    activeChatName: null,
    ws: null,
    isMobile: window.innerWidth <= 768,
    typingTimeout: null,
    unreadCounts: new Map()
};

// DOM Elements
const elements = {
    contactsPanel: document.getElementById('contacts-panel'),
    chatPanel: document.getElementById('chat-panel'),
    emptyChatState: document.getElementById('empty-chat-state'),
    activeChatContainer: document.getElementById('active-chat-container'),
    messagesContainer: document.getElementById('messages-container'),
    messageForm: document.getElementById('message-form'),
    messageInput: document.getElementById('message-input'),
    sendBtn: document.getElementById('send-btn'),
    chatAvatar: document.getElementById('chat-avatar'),
    chatName: document.getElementById('chat-name'),
    chatStatus: document.getElementById('chat-status'),
    chatsList: document.getElementById('chats-list'),
    friendsList: document.getElementById('friends-list'),
    contactSearch: document.getElementById('contact-search'),
    typingIndicator: document.getElementById('typing-indicator-container'),
    toastContainer: document.getElementById('toast-container'),
    userAvatarInitials: document.getElementById('user-avatar-initials'),
    currentUsername: document.getElementById('current-username'),
    currentUserStatus: document.getElementById('current-user-status')
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    checkMobileView();
});

function initializeApp() {
    // Get user data from meta tags or API
    const userData = getCurrentUserData();
    if (userData) {
        chatState.currentUserId = userData.id;
        chatState.currentUsername = userData.username;
        updateUserProfile(userData);
    }
    
    // Initialize WebSocket connection
    connectWebSocket();
    
    // Load initial data
    loadChats();
    loadFriends();
    
    // Setup theme
    initializeTheme();
}

function getCurrentUserData() {
    // This should be populated from backend template
    // For now, return mock data
    return {
        id: 1,
        username: 'User',
        status: 'online'
    };
}

// ============================================
// WebSocket Connection
// ============================================

function showWsBanner(message, variant = 'warning') {
    const banner = document.getElementById('ws-banner');
    const text = document.getElementById('ws-banner-text');
    if (!banner || !text) return;
    text.textContent = message;
    banner.classList.toggle('success', variant === 'success');
    banner.classList.add('visible');
}

function hideWsBanner(delay = 0) {
    const banner = document.getElementById('ws-banner');
    if (!banner) return;
    setTimeout(() => banner.classList.remove('visible'), delay);
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    try {
        chatState.ws = new WebSocket(wsUrl);

        chatState.ws.onopen = () => {
            console.log('WebSocket connected');
            if (chatState.wasDisconnected) {
                showWsBanner('Соединение восстановлено', 'success');
                hideWsBanner(1500);
                chatState.wasDisconnected = false;
            }
            chatState.reconnectAttempt = 0;
        };

        chatState.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };

        chatState.ws.onclose = () => {
            console.log('WebSocket disconnected');
            chatState.wasDisconnected = true;
            chatState.reconnectAttempt = (chatState.reconnectAttempt || 0) + 1;
            startReconnectCountdown(3);
        };

        chatState.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        startReconnectCountdown(3);
    }
}

function startReconnectCountdown(seconds) {
    let remaining = seconds;
    const update = () => showWsBanner(`Соединение потеряно. Переподключение через ${remaining}…`);
    update();
    const interval = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
            clearInterval(interval);
            connectWebSocket();
        } else {
            update();
        }
    }, 1000);
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'new_message':
            handleNewMessage(data);
            break;
        case 'typing':
            handleTypingIndicator(data);
            break;
        case 'online_status':
            handleOnlineStatus(data);
            break;
        case 'friend_request':
            handleFriendRequest(data);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
    // Message form submission
    elements.messageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });
    
    // Message input handling
    elements.messageInput.addEventListener('input', () => {
        autoResizeTextarea();
        updateSendButton();
        sendTypingIndicator();
    });
    
    // Contact search
    elements.contactSearch.addEventListener('input', (e) => {
        filterContacts(e.target.value);
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            elements.contactSearch.focus();
        }
    });
    
    // Window resize
    window.addEventListener('resize', () => {
        checkMobileView();
    });
    
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', (e) => {
            setTheme(e.target.value);
        });
    }
    
    // Profile save button
    const saveProfileBtn = document.getElementById('save-profile-btn');
    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', saveProfile);
    }
    
    // Friend request button
    const sendFriendRequestBtn = document.getElementById('send-friend-request-btn');
    if (sendFriendRequestBtn) {
        sendFriendRequestBtn.addEventListener('click', sendFriendRequest);
    }
}

// ============================================
// Mobile View Handling
// ============================================

function checkMobileView() {
    const wasMobile = chatState.isMobile;
    chatState.isMobile = window.innerWidth <= 768;
    
    if (wasMobile !== chatState.isMobile) {
        // Reset view on resize
        if (!chatState.isMobile) {
            elements.contactsPanel.classList.remove('mobile-hidden');
            elements.chatPanel.classList.remove('mobile-visible');
        }
    }
}

function showContacts() {
    if (chatState.isMobile) {
        elements.chatPanel.classList.remove('active');
        elements.contactsPanel.style.transform = 'translateX(0)';
    }
}

function showChat() {
    if (chatState.isMobile) {
        elements.chatPanel.classList.add('active');
    }
}

// ============================================
// Chat Functions
// ============================================

function renderSkeletons(container, count = 4) {
    if (!container) return;
    const skeletons = Array.from({ length: count }).map((_, i) => `
        <div class="skeleton-item" aria-hidden="true">
            <div class="skeleton-shape skeleton-avatar"></div>
            <div class="skeleton-lines">
                <div class="skeleton-shape skeleton-line ${i % 2 ? 'medium' : 'long'}"></div>
                <div class="skeleton-shape skeleton-line short"></div>
            </div>
        </div>
    `).join('');
    container.innerHTML = skeletons;
}

function loadChats() {
    renderSkeletons(elements.chatsList, 4);

    // Simulated API latency (replace with real fetch)
    setTimeout(() => {
        const mockChats = [
            { id: 1, name: 'Алексей Иванов', lastMessage: 'Привет! Как дела?', time: '10:42', unread: 2, avatar: null },
            { id: 2, name: 'Мария Петрова', lastMessage: 'Документ отправил', time: 'Вчера', unread: 0, avatar: null },
            { id: 3, name: 'Рабочий чат', lastMessage: 'Встреча в 15:00', time: 'Вчера', unread: 5, avatar: null }
        ];
        renderChats(mockChats);
    }, 600);
}

function renderChats(chats) {
    if (chats.length === 0) {
        elements.chatsList.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-chat-square-text fs-3 d-block mb-2"></i>
                <small>Нет активных чатов</small>
            </div>
        `;
        return;
    }
    
    elements.chatsList.innerHTML = chats.map(chat => `
        <div class="list-group-item contact-item p-3" onclick="selectChat(${chat.id})" data-chat-id="${chat.id}"${chat.unread > 0 ? ' data-unread="true"' : ''}>
            <div class="d-flex w-100 justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    ${getAvatarHTML(chat.name, chat.avatar)}
                    <div class="ms-2">
                        <h6 class="mb-0 fw-semibold">${escapeHtml(chat.name)}</h6>
                        <small class="text-muted">${escapeHtml(chat.lastMessage)}</small>
                    </div>
                </div>
                <div class="d-flex flex-column align-items-end">
                    <small class="text-muted">${chat.time}</small>
                    ${chat.unread > 0 ? `<span class="badge badge-unread mt-1">${chat.unread}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

function selectChat(chatId) {
    chatState.activeChatId = chatId;
    chatState.unreadCounts.set(chatId, 0);

    // Update UI
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeItem = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
        activeItem.removeAttribute('data-unread');
        const badge = activeItem.querySelector('.badge-unread');
        if (badge) badge.remove();
    }
    
    // Show chat panel
    elements.emptyChatState.classList.add('d-none');
    elements.activeChatContainer.classList.remove('d-none');
    
    // Update chat header
    const chatData = getChatData(chatId);
    if (chatData) {
        elements.chatName.textContent = chatData.name;
        elements.chatAvatar.src = chatData.avatar || '';
        elements.chatAvatar.style.display = chatData.avatar ? 'block' : 'none';
        
        if (!chatData.avatar) {
            elements.chatAvatar.style.display = 'none';
        }
    }
    
    // Load messages
    loadMessages(chatId);
    
    // Show chat on mobile
    showChat();
}

function loadMessages(chatId) {
    // This should fetch from API
    // Mock data for demonstration
    const mockMessages = [
        { id: 1, sender_id: chatId, content: 'Привет! Как дела?', timestamp: '2024-01-15T10:30:00', is_own: false },
        { id: 2, sender_id: chatState.currentUserId, content: 'Привет! Всё отлично, спасибо!', timestamp: '2024-01-15T10:32:00', is_own: true },
        { id: 3, sender_id: chatId, content: 'Рад слышать! Есть минутка поговорить?', timestamp: '2024-01-15T10:33:00', is_own: false }
    ];
    
    renderMessages(mockMessages);
}

function renderMessages(messages) {
    elements.messagesContainer.innerHTML = `
        <div class="date-separator">
            <small>Сегодня</small>
        </div>
    `;
    
    messages.forEach(msg => {
        appendMessage(msg);
    });
    
    scrollToBottom();
}

function appendMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `d-flex mb-3 ${message.is_own ? 'justify-content-end' : ''}`;
    if (message.cid) messageDiv.dataset.cid = message.cid;

    const avatarHTML = !message.is_own ? `
        <img src="" alt="" class="rounded-circle me-2 align-self-end" width="30" height="30" style="object-fit: cover;">
    ` : '';

    const bubbleClass = message.is_own ? 'message-outgoing' : 'message-incoming';
    const time = formatMessageTime(message.timestamp);
    const status = message.status || (message.is_own ? 'sent' : null);
    const statusAttr = message.is_own ? ` data-status="${status}"` : '';

    messageDiv.innerHTML = `
        ${avatarHTML}
        <div class="${bubbleClass} p-2 shadow-sm message-bubble"${statusAttr}>
            <p class="mb-1">${escapeHtml(message.content)}</p>
            <small class="message-time ${message.is_own ? 'text-white-50' : 'text-muted'}">
                ${time}
                ${message.is_own ? `<span class="read-status ${status}"></span>` : ''}
            </small>
        </div>
    `;

    elements.messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function updateMessageStatus(cid, newStatus) {
    const messageDiv = document.querySelector(`[data-cid="${cid}"]`);
    if (!messageDiv) return;
    const bubble = messageDiv.querySelector('.message-outgoing');
    if (bubble) bubble.dataset.status = newStatus;
    const readStatus = messageDiv.querySelector('.read-status');
    if (readStatus) readStatus.className = `read-status ${newStatus}`;
}

function sendMessage() {
    const content = elements.messageInput.value.trim();
    if (!content || !chatState.activeChatId) return;

    const cid = `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const message = {
        type: 'send_message',
        chat_id: chatState.activeChatId,
        content: content,
        cid: cid
    };

    if (chatState.ws && chatState.ws.readyState === WebSocket.OPEN) {
        chatState.ws.send(JSON.stringify(message));
    }

    // Optimistically add message to UI with pending status
    appendMessage({
        id: Date.now(),
        cid: cid,
        sender_id: chatState.currentUserId,
        content: content,
        timestamp: new Date().toISOString(),
        is_own: true,
        status: 'pending'
    });

    // Auto-promote to "sent" after 800ms (mock; real impl waits for ws ack)
    setTimeout(() => updateMessageStatus(cid, 'sent'), 800);

    // Clear input
    elements.messageInput.value = '';
    autoResizeTextarea();
    updateSendButton();
}

function handleNewMessage(data) {
    if (data.chat_id === chatState.activeChatId) {
        appendMessage({
            id: data.id,
            sender_id: data.sender_id,
            content: data.content,
            timestamp: data.timestamp,
            is_own: data.sender_id === chatState.currentUserId
        });
    } else {
        // Update unread count
        const currentCount = chatState.unreadCounts.get(data.chat_id) || 0;
        const newCount = currentCount + 1;
        chatState.unreadCounts.set(data.chat_id, newCount);

        // Mark contact-item with pulse ring + update badge
        const chatItem = document.querySelector(`[data-chat-id="${data.chat_id}"]`);
        if (chatItem) {
            chatItem.setAttribute('data-unread', 'true');
            let badge = chatItem.querySelector('.badge-unread');
            if (!badge) {
                const right = chatItem.querySelector('.flex-column.align-items-end');
                if (right) {
                    badge = document.createElement('span');
                    badge.className = 'badge badge-unread mt-1';
                    right.appendChild(badge);
                }
            }
            if (badge) badge.textContent = newCount;
        }

        // Show notification
        showToast(`Новое сообщение от ${data.sender_name}`, 'info');
    }
}

// ============================================
// Typing Indicator
// ============================================

function sendTypingIndicator() {
    if (!chatState.activeChatId || !chatState.ws) return;
    
    clearTimeout(chatState.typingTimeout);
    
    chatState.typingTimeout = setTimeout(() => {
        const message = {
            type: 'typing',
            chat_id: chatState.activeChatId
        };
        chatState.ws.send(JSON.stringify(message));
    }, 500);
}

function handleTypingIndicator(data) {
    if (data.chat_id === chatState.activeChatId && data.user_id !== chatState.currentUserId) {
        elements.typingIndicator.classList.remove('d-none');
        
        setTimeout(() => {
            elements.typingIndicator.classList.add('d-none');
        }, 2000);
    }
}

// ============================================
// Friends Functions
// ============================================

function loadFriends() {
    renderSkeletons(elements.friendsList, 3);

    setTimeout(() => {
        const mockFriends = [
            { id: 1, username: 'alexey_ivanov', status: 'online', avatar: null },
            { id: 2, username: 'maria_petrova', status: 'away', avatar: null },
            { id: 3, username: 'dmitry_sidorov', status: 'offline', avatar: null }
        ];
        renderFriends(mockFriends);
    }, 600);
}

function renderFriends(friends) {
    if (friends.length === 0) {
        elements.friendsList.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-people fs-3 d-block mb-2"></i>
                <small>Список друзей пуст</small>
            </div>
        `;
        return;
    }
    
    // Group by status
    const online = friends.filter(f => f.status === 'online');
    const away = friends.filter(f => f.status === 'away');
    const offline = friends.filter(f => f.status === 'offline');
    
    let html = '';
    
    if (online.length > 0) {
        html += '<div class="px-3 py-2"><small class="text-muted text-uppercase" style="font-size: 0.75rem;">Онлайн</small></div>';
        html += online.map(friend => renderFriendItem(friend)).join('');
    }
    
    if (away.length > 0) {
        html += '<div class="px-3 py-2"><small class="text-muted text-uppercase" style="font-size: 0.75rem;">Отошли</small></div>';
        html += away.map(friend => renderFriendItem(friend)).join('');
    }
    
    if (offline.length > 0) {
        html += '<div class="px-3 py-2"><small class="text-muted text-uppercase" style="font-size: 0.75rem;">Оффлайн</small></div>';
        html += offline.map(friend => renderFriendItem(friend)).join('');
    }
    
    elements.friendsList.innerHTML = html;
}

function renderFriendItem(friend) {
    return `
        <div class="list-group-item contact-item p-3" onclick="startChatWithFriend(${friend.id})">
            <div class="d-flex align-items-center">
                ${getAvatarHTML(friend.username, friend.avatar)}
                <div class="ms-2 flex-grow-1">
                    <h6 class="mb-0 fw-semibold">${escapeHtml(friend.username)}</h6>
                    <small class="${getStatusColor(friend.status)}">
                        <span class="status-indicator status-${friend.status}"></span>
                        ${getStatusText(friend.status)}
                    </small>
                </div>
            </div>
        </div>
    `;
}

function startChatWithFriend(friendId) {
    // Navigate to chat with this friend
    selectChat(friendId);
}

function sendFriendRequest() {
    const usernameInput = document.getElementById('friend-username');
    const username = usernameInput.value.trim();
    
    if (!username) return;
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('addFriendModal'));
    modal.hide();
    
    // Send request via WebSocket or API
    if (chatState.ws && chatState.ws.readyState === WebSocket.OPEN) {
        chatState.ws.send(JSON.stringify({
            type: 'friend_request',
            username: username
        }));
    }
    
    showToast(`Запрос отправлен пользователю ${username}`, 'success');
    usernameInput.value = '';
}

// ============================================
// Utility Functions
// ============================================

function getAvatarHTML(name, avatarUrl) {
    if (avatarUrl) {
        return `<img src="${avatarUrl}" alt="${name}" class="rounded-circle me-2" width="40" height="40" style="object-fit: cover;">`;
    }
    const initial = name.charAt(0).toUpperCase();
    return `<div class="avatar-placeholder me-2">${initial}</div>`;
}

function getStatusColor(status) {
    switch (status) {
        case 'online': return 'text-success';
        case 'away': return 'text-warning';
        default: return 'text-muted';
    }
}

function getStatusText(status) {
    switch (status) {
        case 'online': return 'Онлайн';
        case 'away': return 'Отошел';
        default: return 'Оффлайн';
    }
}

function formatMessageTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function autoResizeTextarea() {
    const textarea = elements.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

function updateSendButton() {
    const hasContent = elements.messageInput.value.trim().length > 0;
    elements.sendBtn.disabled = !hasContent;
}

function scrollToBottom() {
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function filterContacts(query) {
    const searchTerm = query.toLowerCase();
    document.querySelectorAll('.contact-item').forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'info') {
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-primary';
    
    const toastHTML = `
        <div id="${toastId}" class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-info-circle me-2"></i>
                <strong class="me-auto">WispChat</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${escapeHtml(message)}
            </div>
        </div>
    `;
    
    elements.toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.remove();
        }
    }, 3000);
}

// ============================================
// Theme Management
// ============================================

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    document.getElementById('theme-toggle').value = savedTheme;
}

function setTheme(theme) {
    const html = document.documentElement;
    
    if (theme === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        html.setAttribute('data-bs-theme', prefersDark ? 'dark' : 'light');
    } else {
        html.setAttribute('data-bs-theme', theme);
    }
    
    localStorage.setItem('theme', theme);
}

// ============================================
// Profile Management
// ============================================

function updateUserProfile(userData) {
    elements.currentUsername.textContent = userData.username;
    elements.userAvatarInitials.textContent = userData.username.charAt(0).toUpperCase();
    
    const modalUsername = document.getElementById('modal-username');
    const modalUserId = document.getElementById('modal-user-id');
    const modalAvatarInitials = document.getElementById('modal-avatar-initials');
    const profileUsername = document.getElementById('profile-username');
    
    if (modalUsername) modalUsername.textContent = userData.username;
    if (modalUserId) modalUserId.textContent = userData.id;
    if (modalAvatarInitials) modalAvatarInitials.textContent = userData.username.charAt(0).toUpperCase();
    if (profileUsername) profileUsername.value = userData.username;
}

function saveProfile() {
    const username = document.getElementById('profile-username').value.trim();
    const status = document.getElementById('profile-status').value;
    
    if (!username) return;
    
    // Save via API
    console.log('Saving profile:', { username, status });
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
    modal.hide();
    
    showToast('Профиль сохранен', 'success');
}

// ============================================
// Online Status Handling
// ============================================

function handleOnlineStatus(data) {
    // Update friend status in the list
    const friendItem = document.querySelector(`[data-friend-id="${data.user_id}"]`);
    if (friendItem) {
        const statusElement = friendItem.querySelector('.status-indicator');
        if (statusElement) {
            statusElement.className = `status-indicator status-${data.status}`;
        }
    }
}

// Helper function to get chat data (mock)
function getChatData(chatId) {
    const mockChats = {
        1: { name: 'Алексей Иванов', avatar: null },
        2: { name: 'Мария Петрова', avatar: null },
        3: { name: 'Рабочий чат', avatar: null }
    };
    return mockChats[chatId];
}
