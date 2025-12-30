// components.js - Placeholder for future modular JS components
// Example: A function to create a chat message element
function createChatMessageElement(role, content) {
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
    return messageDiv;
}
