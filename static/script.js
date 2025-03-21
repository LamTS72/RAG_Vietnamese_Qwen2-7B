document.addEventListener('DOMContentLoaded', () => {
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const chatMessages = document.getElementById('chat-messages');
    const welcomeScreen = document.getElementById('welcome-screen');
    const newChatBtn = document.querySelector('.new-chat-btn');
    const sidebarHistory = document.querySelector('.sidebar-history');
    
    let chatHistory = [];
    let currentChatId = generateId();
    
    // Auto-resize textarea as user types
    questionInput.addEventListener('input', () => {
        questionInput.style.height = 'auto';
        questionInput.style.height = (questionInput.scrollHeight) + 'px';
    });
    
    // Handle form submission
    questionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Add user message to UI
        addMessageToUI('user', question);
        
        // Clear input and reset height
        questionInput.value = '';
        questionInput.style.height = 'auto';
        
        // Hide welcome screen if visible
        if (welcomeScreen.style.display !== 'none') {
            welcomeScreen.style.display = 'none';
            chatMessages.style.display = 'block';
        }
        
        // Add loading indicator
        const loadingMsgId = addLoadingMessage();
        
        try {
            // Call API to get response
            const response = await fetchAnswer(question);
            
            // Remove loading indicator
            removeLoadingMessage(loadingMsgId);
            
            // Add assistant message to UI
            addMessageToUI('assistant', response.answer);
            
            // Update chat history
            updateChatHistory(question, response.answer);
            
        } catch (error) {
            // Remove loading indicator
            removeLoadingMessage(loadingMsgId);
            
            // Add error message
            addMessageToUI('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
            console.error('Error:', error);
        }
    });
    
    // Handle new chat button
    newChatBtn.addEventListener('click', () => {
        startNewChat();
    });
    
    // Function to fetch answer from API
    async function fetchAnswer(question) {
        const response = await fetch('/generative_ai', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });
        
        if (!response.ok) {
            throw new Error(`API responded with status: ${response.status}`);
        }
        
        return response.json();
    }
    
    // Function to add message to UI
    function addMessageToUI(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatarIcon = sender === 'user' ? 'fa-user' : 'fa-robot';
        const avatarClass = sender === 'user' ? 'user-avatar-icon' : '';
        
        messageDiv.innerHTML = `
            <div class="message-avatar ${avatarClass}">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">${formatMessage(content)}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to add loading indicator
    function addLoadingMessage() {
        const loadingId = generateId();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message';
        loadingDiv.id = loadingId;
        
        loadingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return loadingId;
    }
    
    // Function to remove loading indicator
    function removeLoadingMessage(id) {
        const loadingElement = document.getElementById(id);
        if (loadingElement) {
            loadingElement.remove();
        }
    }
    
    // Function to update chat history
    function updateChatHistory(question, answer) {
        // Add to current chat
        if (!chatHistory.some(chat => chat.id === currentChatId)) {
            const newChat = {
                id: currentChatId,
                title: truncateText(question, 30),
                messages: []
            };
            chatHistory.unshift(newChat);
            updateSidebarHistory();
        }
        
        // Find current chat
        const currentChat = chatHistory.find(chat => chat.id === currentChatId);
        
        // Add messages
        currentChat.messages.push({ 
            sender: 'user', 
            content: question 
        });
        
        currentChat.messages.push({ 
            sender: 'assistant', 
            content: answer 
        });
        
        // Save to localStorage
        saveChatsToLocalStorage();
    }
    
    // Function to update sidebar history
    function updateSidebarHistory() {
        sidebarHistory.innerHTML = '';
        
        chatHistory.forEach(chat => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.dataset.chatId = chat.id;
            
            historyItem.innerHTML = `
                <i class="fas fa-comment"></i>
                <span>${chat.title}</span>
            `;
            
            historyItem.addEventListener('click', () => {
                loadChat(chat.id);
            });
            
            sidebarHistory.appendChild(historyItem);
        });
    }
    
    // Function to load chat
    function loadChat(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (!chat) return;
        
        // Set current chat
        currentChatId = chatId;
        
        // Clear chat messages
        chatMessages.innerHTML = '';
        
        // Hide welcome screen
        welcomeScreen.style.display = 'none';
        chatMessages.style.display = 'block';
        
        // Add messages
        chat.messages.forEach(msg => {
            addMessageToUI(msg.sender, msg.content);
        });
    }
    
    // Function to start new chat
    function startNewChat() {
        currentChatId = generateId();
        chatMessages.innerHTML = '';
        welcomeScreen.style.display = 'flex';
        chatMessages.style.display = 'none';
    }
    
    // Helper function to format message with line breaks
    function formatMessage(text) {
        return text.replace(/\n/g, '<br>');
    }
    
    // Helper function to truncate text
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    // Helper function to generate ID
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    }
    
    // Load chats from localStorage
    function loadChatsFromLocalStorage() {
        const savedChats = localStorage.getItem('rag-chat-history');
        if (savedChats) {
            chatHistory = JSON.parse(savedChats);
            updateSidebarHistory();
        }
    }
    
    // Save chats to localStorage
    function saveChatsToLocalStorage() {
        localStorage.setItem('rag-chat-history', JSON.stringify(chatHistory));
    }
    
    // Initialize
    loadChatsFromLocalStorage();
}); 