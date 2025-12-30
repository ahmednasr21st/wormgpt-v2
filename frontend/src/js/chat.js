// chat.js
const API_BASE_URL = 'http://localhost:5000/api'; // Replace with your backend URL
let currentChatId = null;
let currentModel = 'free'; // Default model for the user

document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html'; // Redirect if not logged in
        return;
    }

    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const newChatBtn = document.getElementById('newChatBtn');
    const chatHistoryDiv = document.getElementById('chatHistory');
    const currentChatTitle = document.getElementById('currentChatTitle');
    const currentModelDisplay = document.getElementById('currentModelDisplay');
    const fileUploadInput = document.getElementById('fileUploadInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');


    // Fetch user plan and set currentModel
    await fetchUserPlan();
    await loadChatHistory();
    // Initially start a new chat if no history or first load
    if (!currentChatId && chatHistoryDiv.children.length === 0) {
        startNewChat();
    } else if (!currentChatId && chatHistoryDiv.children.length > 0) {
        // If there's history but no active chat, load the first one
        chatHistoryDiv.children[0].click(); // Simulate click on the first chat
    }


    chatForm.addEventListener('submit', handleSendMessage);
    newChatBtn.addEventListener('click', startNewChat);
    messageInput.addEventListener('input', () => {
        // Auto-resize textarea
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
    fileUploadInput.addEventListener('change', updateFileNameDisplay);

    function updateFileNameDisplay() {
        if (fileUploadInput.files.length > 0) {
            const fileNames = Array.from(fileUploadInput.files).map(f => f.name).join(', ');
            fileNameDisplay.textContent = fileNames;
            fileNameDisplay.classList.remove('hidden');
        } else {
            fileNameDisplay.classList.add('hidden');
        }
    }

    async function fetchUserPlan() {
        try {
            const response = await fetch(`${API_BASE_URL}/user/plan`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                currentModel = data.plan_model; // e.g., 'free', 'pro', 'vip'
                updateModelDisplay(currentModel);
            } else {
                console.error('Failed to fetch user plan:', await response.json());
                currentModel = 'free'; // Default to free if fetching fails
                updateModelDisplay(currentModel);
            }
        } catch (error) {
            console.error('Error fetching user plan:', error);
            currentModel = 'free';
            updateModelDisplay(currentModel);
        }
    }

    function updateModelDisplay(modelName) {
        let displayModel = 'Free Tier';
        let badgeClass = 'free';
        if (modelName === 'pro') {
            displayModel = 'Pro Protocol';
            badgeClass = 'pro';
        } else if (modelName === 'vip') {
            displayModel = 'VIP Exoskeleton';
            badgeClass = 'vip';
        }
        currentModelDisplay.textContent = `Model: ${displayModel}`;
        currentModelDisplay.className = `model-badge ${badgeClass}`;
    }


    async function loadChatHistory() {
        try {
            const response = await fetch(`${API_BASE_URL}/chat/history`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const chats = await response.json();
                chatHistoryDiv.innerHTML = ''; // Clear existing history
                if (chats.length > 0) {
                    chats.forEach(chat => addChatToHistory(chat));
                    // Automatically load the latest chat
                    if (chats[0] && chats[0].id) {
                        currentChatId = chats[0].id;
                        currentChatTitle.textContent = chats[0].title;
                        await loadChatMessages(currentChatId);
                        activateChatHistoryItem(currentChatId);
                    }
                } else {
                    currentChatTitle.textContent = 'New Chat';
                    chatMessages.innerHTML = '';
                    currentChatId = null;
                }
            } else {
                console.error('Failed to load chat history:', await response.json());
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    function addChatToHistory(chat) {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-history-item';
        chatItem.dataset.chatId = chat.id;
        chatItem.innerHTML = `
            <i class="fas fa-comment"></i>
            <span>${chat.title}</span>
            <div class="chat-actions">
                <i class="fas fa-edit edit-chat-btn" title="Edit Chat"></i>
                <i class="fas fa-trash delete-chat-btn" title="Delete Chat"></i>
            </div>
        `;
        chatItem.addEventListener('click', (e) => {
            // Prevent activating chat when clicking edit/delete buttons
            if (!e.target.classList.contains('fa-edit') && !e.target.classList.contains('fa-trash')) {
                currentChatId = chat.id;
                currentChatTitle.textContent = chat.title;
                loadChatMessages(chat.id);
                activateChatHistoryItem(chat.id);
            }
        });
        chatItem.querySelector('.edit-chat-btn').addEventListener('click', (e) => editChatTitle(e, chat.id, chat.title));
        chatItem.querySelector('.delete-chat-btn').addEventListener('click', (e) => deleteChat(e, chat.id));
        chatHistoryDiv.prepend(chatItem); // Add newest chat to top
    }

    function activateChatHistoryItem(chatId) {
        document.querySelectorAll('.chat-history-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeItem = document.querySelector(`.chat-history-item[data-chat-id="${chatId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    async function loadChatMessages(chatId) {
        chatMessages.innerHTML = ''; // Clear existing messages
        try {
            const response = await fetch(`${API_BASE_URL}/chat/${chatId}/messages`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const messages = await response.json();
                messages.forEach(msg => appendMessage(msg.role, msg.content, false));
                scrollToBottom();
            } else {
                console.error('Failed to load chat messages:', await response.json());
            }
        } catch (error) {
            console.error('Error loading chat messages:', error);
        }
    }

    async function startNewChat() {
        currentChatId = null;
        chatMessages.innerHTML = '';
        currentChatTitle.textContent = 'New Chat';
        activateChatHistoryItem(null); // Deactivate all
        messageInput.value = '';
        fileUploadInput.value = '';
        fileNameDisplay.classList.add('hidden');
        messageInput.style.height = 'auto'; // Reset textarea height
    }

    async function handleSendMessage(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        const files = fileUploadInput.files;

        if (!message && files.length === 0) return;

        appendMessage('user', message);
        scrollToBottom();

        const formData = new FormData();
        formData.append('message', message);
        if (currentChatId) {
            formData.append('chat_id', currentChatId);
        }

        Array.from(files).forEach(file => {
            formData.append('files', file);
        });

        messageInput.value = ''; // Clear input immediately
        fileUploadInput.value = ''; // Clear file input
        fileNameDisplay.classList.add('hidden');
        messageInput.style.height = 'auto'; // Reset textarea height

        // Show typing indicator
        const typingIndicator = appendTypingIndicator();
        scrollToBottom();

        try {
            const response = await fetch(`${API_BASE_URL}/chat/send`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            removeTypingIndicator(typingIndicator);

            if (response.ok) {
                const data = await response.json();
                if (!currentChatId && data.chat_id) {
                    currentChatId = data.chat_id;
                    currentChatTitle.textContent = data.chat_title || 'New Chat'; // Use generated title
                    addChatToHistory({ id: currentChatId, title: data.chat_title || 'New Chat' });
                    activateChatHistoryItem(currentChatId);
                } else if (currentChatId && data.chat_title && currentChatTitle.textContent === 'New Chat') {
                    // Update title if it was "New Chat" and a title was generated
                    currentChatTitle.textContent = data.chat_title;
                    const historyItem = document.querySelector(`.chat-history-item[data-chat-id="${currentChatId}"] span`);
                    if (historyItem) historyItem.textContent = data.chat_title;
                }
                appendMessage('ai', data.response);
                scrollToBottom();
            } else {
                const errorData = await response.json();
                appendMessage('system-error', `Error: ${errorData.message || 'Failed to get response.'}`);
                scrollToBottom();
            }
        } catch (error) {
            removeTypingIndicator(typingIndicator);
            console.error('Send message error:', error);
            appendMessage('system-error', 'An error occurred while communicating with the AI.');
            scrollToBottom();
        }
    }

    function appendMessage(role, content, scrollToView = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        const avatarSrc = role === 'user' ? `https://api.dicebear.com/7.x/initials/svg?seed=U` : 'public/wormgpt-logo.png';
        const avatarClass = role === 'ai' ? 'message-avatar ai-avatar' : 'message-avatar';

        messageDiv.innerHTML = `
            <img src="${avatarSrc}" alt="${role === 'user' ? 'User' : 'AI'} Avatar" class="${avatarClass}">
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        if (scrollToView) scrollToBottom();
    }

    function appendTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message ai-message typing-indicator'; // Reuse ai-message styling
        indicatorDiv.innerHTML = `
            <img src="public/wormgpt-logo.png" alt="AI Avatar" class="message-avatar ai-avatar">
            <div class="message-content">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        chatMessages.appendChild(indicatorDiv);
        return indicatorDiv;
    }

    function removeTypingIndicator(indicator) {
        if (indicator && chatMessages.contains(indicator)) {
            chatMessages.removeChild(indicator);
        }
    }


    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function editChatTitle(e, chatId, currentTitle) {
        e.stopPropagation(); // Prevent activating chat
        const spanElement = e.target.closest('.chat-history-item').querySelector('span');
        const originalText = spanElement.textContent;
        spanElement.contentEditable = true;
        spanElement.focus();
        spanElement.classList.add('editing'); // Add a class for visual feedback

        const saveChanges = async () => {
            spanElement.contentEditable = false;
            spanElement.classList.remove('editing');
            const newTitle = spanElement.textContent.trim();
            if (newTitle === "" || newTitle === originalText) {
                spanElement.textContent = originalText; // Revert if empty or no change
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/chat/${chatId}/title`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ title: newTitle })
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('Failed to update chat title:', errorData.message);
                    spanElement.textContent = originalText; // Revert on error
                } else {
                    if (currentChatId === chatId) {
                        currentChatTitle.textContent = newTitle;
                    }
                }
            } catch (error) {
                console.error('Error updating chat title:', error);
                spanElement.textContent = originalText; // Revert on error
            }
        };

        spanElement.addEventListener('blur', saveChanges, { once: true });
        spanElement.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault(); // Prevent new line
                spanElement.blur(); // Trigger blur to save
            }
        });
    }

    async function deleteChat(e, chatId) {
        e.stopPropagation(); // Prevent activating chat
        if (!confirm('Are you sure you want to delete this chat history? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/chat/${chatId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const chatItemToRemove = document.querySelector(`.chat-history-item[data-chat-id="${chatId}"]`);
                if (chatItemToRemove) {
                    chatItemToRemove.remove();
                }
                if (currentChatId === chatId) {
                    startNewChat(); // If deleted chat was active, start a new one
                }
                loadChatHistory(); // Reload history to ensure consistency
            } else {
                console.error('Failed to delete chat:', await response.json());
                alert('Failed to delete chat.');
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
            alert('An error occurred while deleting chat.');
        }
    }
});
