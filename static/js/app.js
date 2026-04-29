/* ============================================
   WispChat Application - Enhanced
   Particle Nebula, Micro-interactions, Glassmorphism
   ============================================ */

// --- Global State ---
let token = localStorage.getItem('token');
let currentChatUser = null;
let ws = null;
let myUsername = "";
let localDB = null;
let searchTimeout = null;

// --- Canvas Nebula System ---
class NebulaSystem {
    constructor() {
        this.canvas = document.getElementById('nebula-canvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.connections = [];
        this.mouse = { x: 0, y: 0 };
        this.targetMouse = { x: 0, y: 0 };
        this.init();
    }

    init() {
        this.resize();
        this.createParticles();
        this.bindEvents();
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        const count = Math.min(80, Math.floor((this.canvas.width * this.canvas.height) / 15000));
        this.particles = [];
        
        // Create particle layers
        for (let i = 0; i < count; i++) {
            const layer = i < count * 0.4 ? 0 : i < count * 0.7 ? 1 : 2;
            const depth = [0.3, 0.6, 1][layer];
            
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radius: Math.max(1, (Math.random() * 2 + 1) * depth),
                vx: (Math.random() - 0.5) * 0.3 * depth,
                vy: (Math.random() - 0.5) * 0.2 * depth,
                alpha: Math.random() * 0.5 + 0.2,
                baseAlpha: Math.random() * 0.5 + 0.2,
                hue: layer === 0 ? 160 : layer === 1 ? 280 : 320,
                pulseSpeed: Math.random() * 0.02 + 0.01,
                pulseOffset: Math.random() * Math.PI * 2,
                layer: layer,
                depth: depth
            });
        }
    }

    bindEvents() {
        window.addEventListener('resize', () => this.resize());
        document.addEventListener('mousemove', (e) => {
            this.targetMouse.x = e.clientX;
            this.targetMouse.y = e.clientY;
        });
        
        // Smooth mouse following
        this.smoothMouse();
    }

    smoothMouse() {
        this.mouse.x += (this.targetMouse.x - this.mouse.x) * 0.05;
        this.mouse.y += (this.targetMouse.y - this.mouse.y) * 0.05;
        requestAnimationFrame(() => this.smoothMouse());
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        const time = Date.now() * 0.001;

        // Draw connections
        this.drawConnections(time);
        
        // Update and draw particles
        this.particles.forEach(p => {
            this.updateParticle(p, time);
            this.drawParticle(p, time);
        });

        requestAnimationFrame(() => this.animate());
    }

    drawConnections(time) {
        const maxDist = 120;
        this.ctx.strokeStyle = 'rgba(6, 214, 160, 0.08)';
        this.ctx.lineWidth = 1;

        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const p1 = this.particles[i];
                const p2 = this.particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < maxDist) {
                    const alpha = (1 - dist / maxDist) * 0.15 * Math.min(p1.alpha, p2.alpha);
                    this.ctx.strokeStyle = `rgba(6, 214, 160, ${alpha})`;
                    this.ctx.beginPath();
                    this.ctx.moveTo(p1.x, p1.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.stroke();
                }
            }
        }

        // Mouse connections
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            const dx = p.x - this.mouse.x;
            const dy = p.y - this.mouse.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 150) {
                const alpha = (1 - dist / 150) * 0.1;
                this.ctx.strokeStyle = `rgba(6, 214, 160, ${alpha})`;
                this.ctx.beginPath();
                this.ctx.moveTo(p.x, p.y);
                this.ctx.lineTo(this.mouse.x, this.mouse.y);
                this.ctx.stroke();
            }
        }
    }

    updateParticle(p, time) {
        // Movement
        p.x += p.vx;
        p.y += p.vy;

        // Mouse repulsion/attraction
        const dx = p.x - this.mouse.x;
        const dy = p.y - this.mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < 100) {
            const force = (100 - dist) / 100 * 0.5;
            p.vx += (dx / dist) * force * 0.1;
            p.vy += (dy / dist) * force * 0.1;
        }

        // Boundary wrap
        if (p.x < -50) p.x = this.canvas.width + 50;
        if (p.x > this.canvas.width + 50) p.x = -50;
        if (p.y < -50) p.y = this.canvas.height + 50;
        if (p.y > this.canvas.height + 50) p.y = -50;

        // Pulsing alpha
        p.alpha = p.baseAlpha + Math.sin(time * p.pulseSpeed + p.pulseOffset) * 0.3;
        p.alpha = Math.max(0.1, Math.min(0.8, p.alpha));

        // Velocity damping
        p.vx *= 0.99;
        p.vy *= 0.99;
    }

    drawParticle(p, time) {
        const gradient = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 2);
        const hue = p.hue;
        
        if (p.layer === 0) {
            gradient.addColorStop(0, `hsla(${hue}, 80%, 60%, ${p.alpha})`);
            gradient.addColorStop(0.5, `hsla(${hue}, 70%, 50%, ${p.alpha * 0.5})`);
            gradient.addColorStop(1, `hsla(${hue}, 60%, 40%, 0)`);
        } else if (p.layer === 1) {
            gradient.addColorStop(0, `hsla(${hue}, 70%, 65%, ${p.alpha})`);
            gradient.addColorStop(0.5, `hsla(${hue}, 60%, 45%, ${p.alpha * 0.4})`);
            gradient.addColorStop(1, `hsla(${hue}, 50%, 35%, 0)`);
        } else {
            gradient.addColorStop(0, `hsla(${hue}, 60%, 70%, ${p.alpha})`);
            gradient.addColorStop(0.5, `hsla(${hue}, 50%, 50%, ${p.alpha * 0.3})`);
            gradient.addColorStop(1, `hsla(${hue}, 40%, 40%, 0)`);
        }

        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius * 2, 0, Math.PI * 2);
        this.ctx.fill();
    }
}

let nebula = null;

// Initialize nebulas after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        nebula = new NebulaSystem();
    });
} else {
    nebula = new NebulaSystem();
}

// --- Scroll Reveal System ---
class ScrollReveal {
    constructor() {
        this.observer = null;
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        this.observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            // Observe glass panels
            document.querySelectorAll('.glass-panel, .glass-panel-light').forEach(el => {
                this.observer.observe(el);
            });
        }
    }
}

let scrollReveal = new ScrollReveal();

// --- Micro-interactions ---
function addMicroInteractions() {
    // Button hover effects (existing buttons)
    document.querySelectorAll('.btn-glass').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // User item pulse on online
    setInterval(() => {
        document.querySelectorAll('.status-dot').forEach(dot => {
            const parent = dot.closest('.user-item');
            if (parent && parent.classList.contains('active')) {
                dot.style.boxShadow = `0 0 ${8 + Math.sin(Date.now() * 0.005) * 4}px rgba(6, 214, 160, 0.5)`;
            }
        });
    }, 100);

    // Input focus glow effects
    document.querySelectorAll('input').forEach(input => {
        input.addEventListener('focus', function() {
            const glassParent = this.closest('.glass-panel, .glass-panel-light');
            if (glassParent) {
                glassParent.style.boxShadow = '0 8px 32px rgba(6, 214, 160, 0.1)';
            }
        });
        input.addEventListener('blur', function() {
            const glassParent = this.closest('.glass-panel, .glass-panel-light');
            if (glassParent) {
                glassParent.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3)';
            }
        });
    });
}

// Wait for DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addMicroInteractions);
} else {
    addMicroInteractions();
}

// --- Original Application Code (with enhancements) ---

// --- Local DB Initialization ---
function initLocalDB(username) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open("ChatDB_" + username, 2);
        request.onerror = event => reject("Ошибка доступа к локальной БД");
        request.onsuccess = event => { localDB = event.target.result; resolve(); };
        
        request.onupgradeneeded = event => {
            localDB = event.target.result;
            let store;
            if (!localDB.objectStoreNames.contains("messages")) {
                store = localDB.createObjectStore("messages", { keyPath: "id", autoIncrement: true });
            } else {
                store = event.currentTarget.transaction.objectStore("messages");
            }
            
            if (!store.indexNames.contains("chat_with")) store.createIndex("chat_with", "chat_with", { unique: false });
            if (!store.indexNames.contains("timestamp")) store.createIndex("timestamp", "timestamp", { unique: false });
            if (!store.indexNames.contains("cid")) store.createIndex("cid", "cid", { unique: true });
        };
    });
}

function saveMessageLocally(chatWith, sender, text, cid, status) {
    if (!localDB) return;
    const tx = localDB.transaction("messages", "readwrite");
    const store = tx.objectStore("messages");
    store.add({
        chat_with: chatWith,
        sender: sender,
        text: text,
        cid: cid,
        status: status,
        timestamp: Date.now()
    });
}

function loadLocalHistory(chatWith) {
    return new Promise((resolve) => {
        if (!localDB) return resolve([]);
        const tx = localDB.transaction("messages", "readonly");
        const store = tx.objectStore("messages");
        const index = store.index("chat_with");
        const request = index.getAll(chatWith);
        
        request.onsuccess = () => {
            let msgs = request.result.sort((a, b) => a.timestamp - b.timestamp);
            resolve(msgs);
        };
        request.onerror = () => resolve([]);
    });
}

// --- Utilities ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toastEl = document.createElement('div');
    
    let bgClass = 'bg-cyan';
    let iconClass = 'fa-circle-info';
    if (type === 'error') { bgClass = 'bg-plasma'; iconClass = 'fa-circle-xmark'; }
    if (type === 'success') { bgClass = 'bg-success'; iconClass = 'fa-circle-check'; }

    toastEl.className = `toast align-items-center border-0 ${bgClass}`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-medium">
                <i class="fa-solid ${iconClass} me-2"></i> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    container.appendChild(toastEl);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
    bsToast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

function setLoading(btnId, isLoading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    btn.disabled = isLoading;
    if (isLoading) {
        btn.dataset.oldHtml = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Загрузка...';
    } else {
        btn.innerHTML = btn.dataset.oldHtml || btn.innerHTML;
    }
}

// --- Auth ---
async function auth(endpoint) {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;
    const btnId = endpoint === '/login' ? 'btn-login' : 'btn-register';

    if(u.length < 3 || p.length < 8) {
        showToast("Логин от 3-х, пароль от 8 символов", "error");
        return;
    }

    setLoading(btnId, true);
    try {
        let options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        };

        if(endpoint === '/login') {
            options.headers['Content-Type'] = 'application/x-www-form-urlencoded';
            options.body = new URLSearchParams({ 'username': u, 'password': p });
        } else {
            options.body = JSON.stringify({ username: u, password: p });
        }

        const res = await fetch(endpoint, options);
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || "Ошибка авторизации");

        token = data.access_token;
        localStorage.setItem('token', token);
        parseMyUsername();
        await initLocalDB(myUsername);
        showApp();
        showToast("Добро пожаловать в WispChat!", "success");
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        setLoading(btnId, false);
    }
}

function logout() {
    localStorage.removeItem('token');
    if(ws) ws.close();
    location.reload();
}

function parseMyUsername() {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        myUsername = payload.sub;
        document.getElementById('my-username').innerText = myUsername;
        document.getElementById('my-avatar').innerText = myUsername.charAt(0).toUpperCase();
    } catch(e) { logout(); }
}

function showApp() {
    document.getElementById('auth-container').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');
    
    // Animate entrance
    const sidebar = document.getElementById('sidebar');
    const chatArea = document.getElementById('chat-area');
    setTimeout(() => {
        sidebar.classList.add('anim-fade-up', 'is-visible');
    }, 100);
    
    loadFriends();
    loadRequests();
    connectWS();
}

// --- API Requests ---
async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: { 'Authorization': `Bearer ${token}` }
    };
    if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }
    const res = await fetch(endpoint, options);
    if (res.status === 401) logout();
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка сервера");
    return data;
}

// --- Friends ---
async function loadFriends() {
    try {
        const friends = await apiRequest('/friends/list');
        const list = document.getElementById('friends-list');
        list.innerHTML = `
            <div class="sidebar-section-title">
                <span>Друзья</span>
                <button class="icon-btn glass-icon" onclick="loadFriends()" style="width:28px;height:28px;">
                    <i class="fa-solid fa-rotate-right" style="font-size:10px;"></i>
                </button>
            </div>`;
        
        friends.forEach(f => {
            const div = document.createElement('div');
            div.className = `user-item ${f.online ? '' : 'offline'} ${f.username === currentChatUser ? 'active' : ''}`;
            div.onclick = () => openChatFromList(f.username);
            
            const avatar = f.username.charAt(0).toUpperCase();
            const statusClass = f.online ? 'status-online' : '';
            
            div.innerHTML = `
                <div class="user-avatar-sm">${avatar}</div>
                <div class="user-info-wrap">
                    <div class="user-item-name">${f.username}</div>
                    <div class="user-item-status">
                        <span class="status-dot ${statusClass}"></span>
                        ${f.online ? 'В сети' : 'Не в сети'}
                    </div>
                </div>
            `;
            list.appendChild(div);
        });
    } catch (e) { showToast(e.message, "error"); }
}

async function loadRequests() {
    try {
        const requests = await apiRequest('/friends/requests');
        const list = document.getElementById('requests-list');
        if (requests.length === 0) {
            list.classList.add('hidden');
            return;
        }
        list.classList.remove('hidden');
        list.innerHTML = `
            <div class="sidebar-section-title">
                <span style="color:var(--accent-plasma)">• Новые заявки</span>
            </div>`;
        
        requests.forEach(u => {
            const div = document.createElement('div');
            div.className = 'user-item user-item-pending';
            div.style.cursor = "default";
            
            const avatar = u.charAt(0).toUpperCase();
            const actionBtn = (type) => type === 'accept' 
                ? '<i class="fa-solid fa-check"></i>'
                : '<i class="fa-solid fa-xmark"></i>';
            
            div.innerHTML = `
                <div class="user-avatar-sm">${avatar}</div>
                <div class="user-info-wrap">
                    <div class="user-item-name">${u}</div>
                    <div class="user-item-status">Запрос</div>
                </div>
                <div class="user-item-actions">
                    <button class="icon-btn glass-icon" onclick="event.stopPropagation(); friendAction('/friends/accept', '${u}')" style="border-color:var(--accent-cyan);color:var(--accent-cyan);width:32px;height:32px;">${actionBtn('accept')}</button>
                    <button class="icon-btn glass-icon" onclick="event.stopPropagation(); friendAction('/friends/reject', '${u}')" style="border-color:var(--accent-plasma);color:var(--accent-plasma);width:32px;height:32px;">${actionBtn('reject')}</button>
                </div>
            `;
            list.appendChild(div);
        });
    } catch (e) { showToast(e.message, "error"); }
}

function searchUsers() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        const searchInput = document.getElementById('search-input');
        const query = searchInput.value.trim();
        const resDiv = document.getElementById('search-results');
        const friendsList = document.getElementById('friends-list');

        if (query.length < 3) {
            resDiv.classList.add('hidden');
            friendsList.classList.remove('hidden');
            return;
        }

        resDiv.classList.remove('hidden');
        resDiv.innerHTML = '<div class="sidebar-section-title">Поиск...</div>';
        friendsList.classList.add('hidden');

        try {
            const users = await apiRequest(`/friends/search?query=${encodeURIComponent(query)}`);
            resDiv.innerHTML = '<div class="sidebar-section-title">Результаты</div>';

            if(users.length === 0) {
                resDiv.innerHTML += '<div class="user-item"><span style="color:var(--fg-muted);">Ничего не найдено</span></div>';
                return;
            }

            users.forEach(u => {
                const div = document.createElement('div');
                div.className = 'user-item';
                div.style.cursor = "default";
                const avatar = u.username.charAt(0).toUpperCase();
                
                let actionBtn = '';
                if (u.status === 'none') {
                    actionBtn = `<button class="icon-btn glass-icon" onclick="friendAction('/friends/request', '${u.username}')" style="width:32px;height:32px;border-color:var(--accent-cyan);color:var(--accent-cyan);">+</button>`;
                } else if (u.status === 'friends') {
                    actionBtn = `<button class="icon-btn glass-icon" onclick="openChatFromSearch('${u.username}')" style="width:32px;height:32px;border-color:var(--accent-purple);color:var(--accent-purple);"><i class="fa-solid fa-message"></i></button>`;
                } else if (u.status === 'pending_received') {
                    actionBtn = `<div style="display:flex;gap:4px">
                        <button class="icon-btn glass-icon" onclick="friendAction('/friends/accept', '${u.username}')" style="width:26px;height:26px;border-color:var(--accent-cyan);font-size:10px;">✓</button>
                        <button class="icon-btn glass-icon" onclick="friendAction('/friends/reject', '${u.username}')" style="width:26px;height:26px;border-color:var(--accent-plasma);font-size:10px;">✕</button>
                    </div>`;
                }

                div.innerHTML = `
                    <div class="user-avatar-sm">${avatar}</div>
                    <div class="user-info-wrap">
                        <div class="user-item-name">${u.username}</div>
                    </div>
                    <div>${actionBtn}</div>
                `;
                resDiv.appendChild(div);
            });
        } catch (e) { showToast(e.message, "error"); }
    }, 400);
}

function openChatFromSearch(username) {
    document.getElementById('search-input').value = '';
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('friends-list').classList.remove('hidden');
    openChat(username);
}

async function friendAction(endpoint, target_username) {
    try {
        const data = await apiRequest(endpoint, 'POST', { target_username });
        showToast(data.message, "success");
        searchUsers(); 
        loadFriends(); 
        loadRequests();
    } catch (e) { showToast(e.message, "error"); }
}

// --- Remove Friend Modal ---
let userToRemove = null;

function confirmRemoveFriend() {
    if (!currentChatUser) return;
    userToRemove = currentChatUser;
    document.getElementById('remove-target-name').innerText = userToRemove;
    document.getElementById('modalOverlay').classList.remove('hidden');
    document.getElementById('overlay').classList.add('active');
}

document.getElementById('modalCancel').addEventListener('click', () => {
    document.getElementById('modalOverlay').classList.add('hidden');
    document.getElementById('overlay').classList.remove('active');
});

document.getElementById('modalConfirm').addEventListener('click', () => {
    executeRemoveFriend();
    document.getElementById('modalOverlay').classList.add('hidden');
    document.getElementById('overlay').classList.remove('active');
});

document.getElementById('overlay').addEventListener('click', () => {
    document.getElementById('modalOverlay').classList.add('hidden');
    document.getElementById('overlay').classList.remove('active');
});

async function executeRemoveFriend() {
    if (!userToRemove) return;
    try {
        const data = await apiRequest('/friends/remove', 'POST', { target_username: userToRemove });
        showToast(data.message, "success");
        if (currentChatUser === userToRemove) closeChat();
        loadFriends();
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        userToRemove = null;
    }
}

// --- Chat & WebSocket ---
function openChatFromList(friendUsername) {
    if (window.innerWidth < 768) {
        document.getElementById('sidebar').classList.add('mobile-hidden');
        document.getElementById('chat-area').classList.add('mobile-visible');
    }
    openChat(friendUsername);
}

async function openChat(friendUsername) {
    currentChatUser = friendUsername;
    document.getElementById('no-chat-selected').classList.add('hidden');
    document.getElementById('active-chat').classList.remove('hidden');
    document.getElementById('chat-title').innerText = friendUsername;
    document.getElementById('chat-avatar').innerText = friendUsername.charAt(0).toUpperCase();
    document.getElementById('messages').innerHTML = '';

    document.querySelectorAll('#friends-list .user-item').forEach(el => el.classList.remove('active'));

    const history = await loadLocalHistory(friendUsername);
    history.forEach(msg => {
        appendMessage(msg.sender === myUsername ? 'me' : 'them', msg.text, msg.cid, msg.status);
        if (msg.sender !== myUsername && msg.status !== 'read') {
            updateMessageStatus(msg.cid, "read");
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: "read", to: friendUsername, cid: msg.cid }));
            }
        }
    });
}

function closeChat() {
    currentChatUser = null;
    document.getElementById('no-chat-selected').classList.remove('hidden');
    document.getElementById('active-chat').classList.add('hidden');
    if (window.innerWidth < 768) {
        document.getElementById('sidebar').classList.remove('mobile-hidden');
        document.getElementById('chat-area').classList.remove('mobile-visible');
    }
}

function connectWS() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${protocol}://${window.location.host}/ws?token=${token}`);

    ws.onopen = () => resendPendingMessages();

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.system) {
            if (data.system === "friend_request") {
                showToast(`Новая заявка от ${data.from}`, "info");
                loadRequests();
                return;
            }
            if (currentChatUser) appendSystemMessage(data.system);
            loadFriends();
            return;
        }

        if (data.action === "ack") {
            updateMessageStatus(data.cid, "sent");
            return;
        }

        if (data.action === "read") {
            updateMessageStatus(data.cid, "read");
            return;
        }

        if (data.action === "message" && data.from) {
            saveMessageLocally(data.from, data.from, data.text, data.cid, "read");
            if (data.from === currentChatUser) {
                appendMessage('them', data.text, data.cid, "read");
                ws.send(JSON.stringify({ action: "read", to: data.from, cid: data.cid }));
            } else {
                showToast(`Новое сообщение от ${data.from}`, "info");
                loadFriends();
            }
        }
    };

    ws.onclose = (e) => {
        if(e.code === 4401 || e.code === 4403) logout();
        setTimeout(connectWS, 3000);
    };
}

function sendMessage() {
    const input = document.getElementById("msg-input");
    const text = input.value.trim();
    if (!text || !currentChatUser) return;

    const cid = Date.now().toString() + Math.random().toString(36).substr(2, 5);
    saveMessageLocally(currentChatUser, myUsername, text, cid, "pending");
    appendMessage('me', text, cid, "pending");
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "message", to: currentChatUser, text: text, cid: cid }));
    }
    input.value = "";
    input.focus();
}

function resendPendingMessages() {
    if (!localDB || !ws || ws.readyState !== WebSocket.OPEN) return;
    const tx = localDB.transaction("messages", "readonly");
    const store = tx.objectStore("messages");
    const request = store.getAll();

    request.onsuccess = () => {
        const msgs = request.result;
        const pendingMsgs = msgs.filter(m => m.status === 'pending' && m.sender === myUsername);
        pendingMsgs.forEach(msg => {
            ws.send(JSON.stringify({ action: "message", to: msg.chat_with, text: msg.text, cid: msg.cid }));
        });
    };
}

function updateMessageStatus(cid, newStatus) {
    if (!localDB) return;
    const tx = localDB.transaction("messages", "readwrite");
    const store = tx.objectStore("messages");
    const index = store.index("cid");
    const request = index.get(cid);

    request.onsuccess = () => {
        const data = request.result;
        if (data) {
            const states = { 'pending': 0, 'sent': 1, 'read': 2 };
            if (states[newStatus] > states[data.status]) {
                data.status = newStatus;
                store.put(data);
            }
            
            const msgElement = document.getElementById(`msg-${cid}`);
            if (msgElement) {
                const statusSpan = msgElement.querySelector('.msg-status');
                if (statusSpan) {
                    let iconHtml = '';
                    if (newStatus === 'sent') iconHtml = '<i class="fa-solid fa-check"></i>';
                    else if (newStatus === 'read') iconHtml = '<i class="fa-solid fa-check-double" style="color:var(--accent-cyan)"></i>';
                    else iconHtml = '<i class="fa-regular fa-clock"></i>';
                    
                    statusSpan.className = `msg-status status-${newStatus}`;
                    statusSpan.innerHTML = iconHtml;
                }
            }
        }
    };
}

function handleEnter(e) { if (e.key === "Enter") sendMessage(); }

function appendMessage(type, text, cid, status) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `msg msg-${type}`;
    msgDiv.id = `msg-${cid}`;
    
    let statusHtml = '';
    if (type === 'me') {
        let iconHtml = '<i class="fa-regular fa-clock"></i>';
        if (status === 'sent') iconHtml = '<i class="fa-solid fa-check"></i>';
        else if (status === 'read') iconHtml = '<i class="fa-solid fa-check-double"></i>';
        
        statusHtml = `<span class="msg-status status-${status}">${iconHtml}</span>`;
    }
    
    const safeText = document.createElement('div');
    safeText.innerText = text;
    
    msgDiv.innerHTML = `${safeText.innerHTML}${statusHtml}`;
    
    const box = document.getElementById("messages");
    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
}

function appendSystemMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `msg msg-sys`;
    msgDiv.innerText = text;
    const box = document.getElementById("messages");
    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
}

// --- Mobile Back Button ---
window.addEventListener('resize', () => {
    if (window.innerWidth >= 768) {
        document.getElementById('sidebar').classList.remove('mobile-hidden');
        document.getElementById('chat-area').classList.remove('mobile-visible');
    }
});

// Auto-login if token exists
if (token) {
    parseMyUsername();
    initLocalDB(myUsername).then(() => {
        showApp();
    });
}