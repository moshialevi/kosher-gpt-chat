class ChatApp {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatForm = document.getElementById('chatForm');
        this.statusIndicator = document.getElementById('statusIndicator');
        
        this.isTyping = false;
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateStatus('מוכן', 'success');
    }
    
    bindEvents() {
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.messageInput.addEventListener('input', () => {
            this.sendButton.disabled = !this.messageInput.value.trim();
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;
        
        // הוספת הודעת המשתמש
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        
        // עדכון סטטוס
        this.updateStatus('מקבל תשובה...', 'typing');
        this.isTyping = true;
        
        try {
            // יצירת הודעת תשובה ריקה
            const responseMessageDiv = this.addMessage('', 'assistant');
            const responseContent = responseMessageDiv.querySelector('.message-content');
            
            // שליחת בקשה עם סטרימינג
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    streaming: true 
                })
            });
            
            if (response.ok) {
                if (response.headers.get('content-type')?.includes('text/event-stream')) {
                    // סטרימינג
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    try {
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            
                            const chunk = decoder.decode(value);
                            const lines = chunk.split('\n');
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    const data = line.slice(6);
                                    if (data.trim() === '') continue;
                                    
                                    try {
                                        const parsed = JSON.parse(data);
                                        
                                        if (parsed.error) {
                                            responseContent.textContent = parsed.error;
                                            this.updateStatus('שגיאה', 'error');
                                            break;
                                        } else if (parsed.done) {
                                            this.updateStatus('תשובה הושלמה', 'success');
                                            break;
                                        } else if (parsed.content) {
                                            responseContent.textContent += parsed.content;
                                            // גלילה לתחתית
                                            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                                        }
                                    } catch (e) {
                                        console.error('Error parsing JSON:', e);
                                    }
                                }
                            }
                        }
                    } finally {
                        reader.releaseLock();
                    }
                } else {
                    // תשובה רגילה (ללא סטרימינג)
                    const data = await response.json();
                    
                    if (data.blocked) {
                        // הודעה נחסמה
                        responseContent.textContent = 'ההודעה שלך נחסמה בשל תוכן לא צנוע. אנא שמור על שפה נקייה וטובה.';
                        responseMessageDiv.className = 'message error';
                        this.updateStatus('הודעה נחסמה', 'error');
                    } else {
                        // תשובה תקינה
                        responseContent.textContent = data.response;
                        this.updateStatus('תשובה התקבלה', 'success');
                    }
                }
            } else {
                // שגיאה בשרת
                responseContent.textContent = 'אירעה שגיאה בשרת. אנא נסה שוב מאוחר יותר.';
                responseMessageDiv.className = 'message error';
                this.updateStatus('שגיאה בשרת', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage(
                'אירעה שגיאה בתקשורת עם השרת. אנא בדוק את החיבור שלך.',
                'error'
            );
            this.updateStatus('שגיאת תקשורת', 'error');
        } finally {
            this.isTyping = false;
            this.updateStatus('מוכן', 'success');
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);
        
        // גלילה לתחתית
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // אנימציה להודעה חדשה
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        messageDiv.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 100);
        
        return messageDiv;
    }
    
    updateStatus(text, type) {
        const statusText = this.statusIndicator.querySelector('.status-text');
        statusText.textContent = text;
        
        // הסרת כל הקלאסים הקודמים
        this.statusIndicator.className = 'status-indicator';
        
        // הוספת הקלאס החדש
        if (type) {
            this.statusIndicator.classList.add(type);
        }
    }
    
    // פונקציה להוספת הודעת טעינה
    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'message-content';
        typingContent.innerHTML = '<span class="typing-dots">מקליד</span><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>';
        
        typingDiv.appendChild(typingContent);
        this.chatMessages.appendChild(typingDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    // פונקציה להסרת אינדיקטור הטעינה
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
}

// אתחול האפליקציה כשהדף נטען
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});

// הוספת אנימציה לנקודות הטעינה
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: inline-block;
    }
    
    .dot {
        animation: typing 1.4s infinite;
        display: inline-block;
    }
    
    .dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    .dot:nth-child(4) {
        animation-delay: 0.6s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            opacity: 0;
        }
        30% {
            opacity: 1;
        }
    }
`;
document.head.appendChild(style); 