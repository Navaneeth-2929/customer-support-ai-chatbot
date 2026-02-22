# app.py
from flask import Flask, request, jsonify, render_template_string
import json
import random
import re
from datetime import datetime
from textblob import TextBlob
import os

app = Flask(__name__)

# Load responses
try:
    with open('responses.json', 'r') as f:
        responses = json.load(f)
    print("✅ Responses loaded successfully!")
    print(f"📊 Loaded intents: {list(responses.keys())}")
except FileNotFoundError:
    print("❌ responses.json not found! Creating default responses...")
    responses = {
        "greeting": {
            "patterns": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "responses": ["Hello! 👋 How can I help you today?"]
        },
        "return": {
            "patterns": ["return", "refund", "exchange", "send back"],
            "responses": ["You can return items within 30 days of purchase."]
        },
        "default": {
            "responses": ["I'm not sure about that. Can you rephrase?"]
        }
    }

# Store conversation contexts
conversations = {}

# Company information
COMPANY_NAME = "Your Company"
BOT_NAME = "SupportBot"
SUPPORT_EMAIL = "support@yourcompany.com"
SUPPORT_PHONE = "1-800-123-4567"

# HTML template (keep the same as before - it's long so I'll omit it here)
# ... (keep your existing HTML template here)

def analyze_sentiment(message):
    """Analyze the sentiment of user message"""
    try:
        blob = TextBlob(message)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.3:
            return 'positive'
        elif polarity < -0.3:
            return 'negative'
        else:
            return 'neutral'
    except:
        return 'neutral'

def extract_name(message):
    """Extract name from common patterns"""
    message = message.lower()
    
    patterns = [
        r'my name is (\w+)',
        r'i am (\w+)',
        r'i\'m (\w+)',
        r'call me (\w+)',
        r'this is (\w+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            for group in match.groups():
                if group:
                    return group.capitalize()
    return None

def extract_order_number(message):
    """Extract order number from message"""
    patterns = [
        r'order\s*#?\s*(\d{5,})',
        r'#(\d{5,})',
        r'ORD[-]?(\d{5,})',
        r'tracking\s*#?\s*(\d{5,})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def match_intent(message):
    """
    Enhanced intent matching with priority and better pattern matching
    """
    message = message.lower().strip()
    
    # Priority 1: Check for name introduction first
    if extract_name(message):
        return 'name_intro'
    
    # Priority 2: Check for order tracking
    if extract_order_number(message):
        return 'order_tracking'
    
    # Priority 3: Check for exact matches first
    # Split message into words for better matching
    words = set(message.split())
    
    # Define priority intents (these should be checked first)
    priority_intents = ['return', 'refund', 'shipping', 'payment', 'contact']
    
    # First check priority intents with exact word matching
    for intent in priority_intents:
        if intent in responses:
            for pattern in responses[intent].get('patterns', []):
                # Check if the pattern words are in the message
                pattern_words = set(pattern.split())
                if pattern_words.issubset(words):
                    return intent
    
    # Then check all other intents
    for intent, data in responses.items():
        if intent == 'default' or intent in priority_intents:
            continue
            
        for pattern in data.get('patterns', []):
            # Check for word boundary matches
            if re.search(r'\b' + re.escape(pattern) + r'\b', message):
                return intent
            # Check if pattern is in message
            if pattern in message:
                return intent
    
    # Priority 4: If no match found, check if it's a greeting
    greeting_patterns = ['hello', 'hi', 'hey', 'greetings']
    if any(greeting in message for greeting in greeting_patterns):
        return 'greeting'
    
    return 'default'

def get_quick_replies(intent):
    """Get quick replies based on intent"""
    quick_replies_map = {
        'greeting': ['Store hours', 'Return policy', 'Shipping info', 'Contact us'],
        'hours': ['Weekend hours', 'Holiday hours', 'Location hours'],
        'return': ['Start a return', 'Return policy', 'Exchange item', 'Refund status'],
        'shipping': ['Track my order', 'Shipping cost', 'Delivery time', 'Free shipping'],
        'payment': ['Credit card', 'PayPal', 'Installments', 'Gift card'],
        'contact': [SUPPORT_PHONE, 'Email support', 'Live chat', 'Call me'],
        'thanks': ['You\'re welcome!', 'Any other questions?', 'Have a great day!'],
        'goodbye': ['Thanks for chatting!', 'Come back soon!', 'Rate your experience'],
        'default': ['Store hours', 'Return policy', 'Shipping info', 'Contact us']
    }
    
    return quick_replies_map.get(intent, quick_replies_map['default'])

def get_personalized_response(intent, session_data, user_message):
    """Get response with personalization"""
    
    # Handle name introduction
    if intent == 'name_intro':
        name = extract_name(user_message)
        if name:
            session_data['name'] = name
            return f"Nice to meet you, {name}! 🎉 How can I help you today?"
    
    # Handle order tracking
    if intent == 'order_tracking':
        order_number = extract_order_number(user_message)
        if order_number:
            session_data['last_order'] = order_number
            return f"Let me check order #{order_number} for you... 📦 It's currently being processed and will ship within 2 business days."
    
    # Handle specific intents
    if intent != 'default' and intent in responses:
        response = random.choice(responses[intent]['responses'])
        print(f"🔍 Matched intent: {intent}")  # Debug print
    else:
        response = random.choice(responses['default']['responses'])
        print(f"🔍 No match, using default")
    
    # Personalize with name if we know it
    if session_data.get('name') and random.random() > 0.5:
        response = f"{session_data['name']}, {response[0].lower() + response[1:]}"
    
    return response

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Customer Service Chatbot</title>
        <link rel="icon" type="image/x-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .chat-container {
                width: 100%;
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            
            .chat-header h2 {
                margin-bottom: 5px;
                font-size: 24px;
            }
            
            .chat-header p {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .chat-messages { 
                height: 400px; 
                overflow-y: auto; 
                padding: 20px; 
                background-color: #f8f9fa;
            }
            
            .message-wrapper {
                margin: 10px 0;
                display: flex;
                flex-direction: column;
            }
            
            .user-wrapper {
                align-items: flex-end;
            }
            
            .bot-wrapper {
                align-items: flex-start;
            }
            
            .message {
                padding: 12px 18px;
                border-radius: 20px;
                max-width: 70%;
                word-wrap: break-word;
                position: relative;
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .user-message { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 5px;
            }
            
            .bot-message { 
                background-color: white;
                color: #333;
                border-bottom-left-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .timestamp {
                font-size: 0.7em;
                margin-top: 5px;
                color: #999;
            }
            
            .user-timestamp {
                text-align: right;
            }
            
            .input-area {
                padding: 20px;
                background-color: white;
                border-top: 1px solid #eee;
            }
            
            .input-container {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
            }
            
            #user-input { 
                flex: 1;
                padding: 12px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 30px;
                font-size: 14px;
                outline: none;
                transition: all 0.3s;
            }
            
            #user-input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .btn {
                padding: 12px 25px;
                border: none;
                border-radius: 30px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-secondary {
                background-color: #f0f0f0;
                color: #666;
            }
            
            .btn-secondary:hover {
                background-color: #e0e0e0;
            }
            
            .quick-replies {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 10px;
            }
            
            .quick-reply-btn {
                padding: 8px 16px;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 20px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.3s;
            }
            
            .quick-reply-btn:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: transparent;
            }
            
            .typing-indicator {
                display: flex;
                gap: 5px;
                padding: 12px 18px;
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                width: fit-content;
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                background-color: #999;
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }
            
            .typing-dot:nth-child(1) { animation-delay: 0s; }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
            
            .status-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 20px;
                background-color: #f8f9fa;
                border-top: 1px solid #eee;
                font-size: 13px;
                color: #666;
            }
            
            .sentiment-indicator {
                padding: 4px 10px;
                border-radius: 15px;
                font-size: 12px;
            }
            
            .sentiment-positive { background-color: #d4edda; color: #155724; }
            .sentiment-neutral { background-color: #fff3cd; color: #856404; }
            .sentiment-negative { background-color: #f8d7da; color: #721c24; }
            
            #clear-btn {
                background: none;
                border: none;
                color: #999;
                cursor: pointer;
                font-size: 13px;
                text-decoration: underline;
            }
            
            #clear-btn:hover {
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h2>🤖 Customer Service Chatbot</h2>
                <p>Ask me anything about our products and services!</p>
            </div>
            
            <div class="chat-messages" id="chatbox"></div>
            
            <div class="input-area">
                <div class="input-container">
                    <input type="text" id="user-input" placeholder="Type your message..." autofocus>
                    <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                </div>
                
                <div class="quick-replies" id="quick-replies"></div>
            </div>
            
            <div class="status-bar">
                <span id="welcome-message">👋 Welcome!</span>
                <span id="sentiment-display" class="sentiment-indicator">😐 Neutral</span>
                <button id="clear-btn" onclick="clearChat()">Clear Chat</button>
            </div>
        </div>
        
        <script>
            let sessionId = Math.random().toString(36).substring(7);
            let isTyping = false;
            let currentSentiment = 'neutral';
            
            function addMessage(sender, message, isHtml = false) {
                const chatbox = document.getElementById('chatbox');
                const wrapper = document.createElement('div');
                wrapper.className = `message-wrapper ${sender === 'user' ? 'user-wrapper' : 'bot-wrapper'}`;
                
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;
                
                if (isHtml) {
                    messageDiv.innerHTML = message;
                } else {
                    messageDiv.textContent = message;
                }
                
                const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const timeDiv = document.createElement('div');
                timeDiv.className = `timestamp ${sender === 'user' ? 'user-timestamp' : ''}`;
                timeDiv.textContent = timestamp;
                
                messageDiv.appendChild(timeDiv);
                wrapper.appendChild(messageDiv);
                chatbox.appendChild(wrapper);
                chatbox.scrollTop = chatbox.scrollHeight;
            }
            
            function showTyping() {
                if (!isTyping) {
                    isTyping = true;
                    const chatbox = document.getElementById('chatbox');
                    const wrapper = document.createElement('div');
                    wrapper.className = 'message-wrapper bot-wrapper';
                    wrapper.id = 'typing-wrapper';
                    
                    const typingDiv = document.createElement('div');
                    typingDiv.className = 'typing-indicator';
                    typingDiv.innerHTML = `
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    `;
                    
                    wrapper.appendChild(typingDiv);
                    chatbox.appendChild(wrapper);
                    chatbox.scrollTop = chatbox.scrollHeight;
                }
            }
            
            function hideTyping() {
                const typingWrapper = document.getElementById('typing-wrapper');
                if (typingWrapper) {
                    typingWrapper.remove();
                }
                isTyping = false;
            }
            
            function showQuickReplies(replies) {
                const container = document.getElementById('quick-replies');
                container.innerHTML = '';
                
                replies.forEach(reply => {
                    const btn = document.createElement('button');
                    btn.className = 'quick-reply-btn';
                    btn.textContent = reply;
                    btn.onclick = () => {
                        document.getElementById('user-input').value = reply;
                        sendMessage();
                    };
                    container.appendChild(btn);
                });
            }
            
            function updateSentiment(sentiment) {
                currentSentiment = sentiment;
                const display = document.getElementById('sentiment-display');
                display.className = 'sentiment-indicator';
                
                if (sentiment === 'positive') {
                    display.className += ' sentiment-positive';
                    display.innerHTML = '😊 Positive';
                } else if (sentiment === 'negative') {
                    display.className += ' sentiment-negative';
                    display.innerHTML = '😠 Negative';
                } else {
                    display.className += ' sentiment-neutral';
                    display.innerHTML = '😐 Neutral';
                }
            }
            
            function clearChat() {
                document.getElementById('chatbox').innerHTML = '';
                addMessage('bot', 'Chat cleared! How can I help you? 👋');
                sessionId = Math.random().toString(36).substring(7);
            }
            
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const message = input.value.trim();
                if (!message) return;
                
                input.value = '';
                
                addMessage('user', message);
                showTyping();
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: message,
                            session_id: sessionId,
                            sentiment: currentSentiment
                        })
                    });
                    
                    const data = await response.json();
                    
                    hideTyping();
                    
                    if (data.formatted_response) {
                        addMessage('bot', data.formatted_response, true);
                    } else {
                        addMessage('bot', data.response);
                    }
                    
                    if (data.sentiment) {
                        updateSentiment(data.sentiment);
                    }
                    
                    if (data.quick_replies) {
                        showQuickReplies(data.quick_replies);
                    }
                    
                    if (data.name) {
                        document.getElementById('welcome-message').textContent = `👋 Hello, ${data.name}!`;
                    }
                    
                } catch (error) {
                    hideTyping();
                    addMessage('bot', 'Sorry, I encountered an error. Please try again.');
                    console.error('Error:', error);
                }
            }
            
            document.getElementById('user-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            window.onload = function() {
                addMessage('bot', 'Hello! 👋 Welcome to our customer support! How can I help you today?');
                showQuickReplies(['Store hours', 'Return policy', 'Shipping info', 'Contact us']);
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    current_sentiment = data.get('sentiment', 'neutral')
    
    # Get or create session data
    if session_id not in conversations:
        conversations[session_id] = {
            'name': None,
            'message_count': 0,
            'last_intent': None,
            'last_order': None,
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    
    session_data = conversations[session_id]
    session_data['message_count'] += 1
    
    # Store message
    session_data['messages'].append({
        'role': 'user',
        'message': user_message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Analyze sentiment
    sentiment = analyze_sentiment(user_message)
    
    # Check for negative sentiment - offer human agent
    if sentiment == 'negative' and session_data['message_count'] > 3:
        response = "I notice you seem frustrated. Would you like me to connect you with a human agent? 🤝"
        return jsonify({
            'response': response,
            'sentiment': sentiment,
            'quick_replies': ['Yes please', 'No thanks', 'Continue chat'],
            'session_id': session_id
        })
    
    # Get intent and response
    intent = match_intent(user_message)
    session_data['last_intent'] = intent
    
    print(f"📝 User message: '{user_message}'")
    print(f"🎯 Matched intent: '{intent}'")
    
    # Get personalized response
    response = get_personalized_response(intent, session_data, user_message)
    
    # Store bot response
    session_data['messages'].append({
        'role': 'bot',
        'message': response,
        'timestamp': datetime.now().isoformat()
    })
    
    # Get quick replies
    quick_replies = get_quick_replies(intent)
    
    return jsonify({
        'response': response,
        'intent': intent,
        'sentiment': sentiment,
        'quick_replies': quick_replies,
        'name': session_data.get('name'),
        'session_id': session_id
    })

@app.route('/history/<session_id>')
def get_history(session_id):
    """Get conversation history"""
    if session_id in conversations:
        return jsonify({
            'history': conversations[session_id].get('messages', []),
            'session_data': {
                'name': conversations[session_id].get('name'),
                'message_count': conversations[session_id].get('message_count'),
                'created_at': conversations[session_id].get('created_at')
            }
        })
    return jsonify({'history': [], 'session_data': {}})

@app.route('/clear/<session_id>')
def clear_session(session_id):
    """Clear conversation session"""
    if session_id in conversations:
        del conversations[session_id]
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 CHATBOT IS STARTING...")
    print("=" * 50)
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📊 Loaded {len(responses)} intent categories")
    print(f"📍 Open http://localhost:5000 in your browser")
    print(f"📝 Press Ctrl+C to stop")
    print("=" * 50)
    app.run(debug=True, port=5000)