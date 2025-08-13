from flask import Flask, request, jsonify, render_template, Response, stream_template
import requests
import os
import re
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# טעינת משתני הסביבה מקובץ .env
load_dotenv()

app = Flask(__name__)

# הגדרת מילים לא צנועות לסינון
INAPPROPRIATE_WORDS = [
    'סקס', 'sex', 'חזה', 'breast', 'עירום', 'nude', 'פורנוגרפיה', 'porn',
    'זין', 'penis', 'כוס', 'vagina', 'אונן', 'masturbate', 'אורגזמה', 'orgasm',
    'מזדיין', 'fuck', 'זבל', 'shit', 'כוס', 'cunt', 'זין', 'dick',
    'זונה', 'whore', 'כלב', 'bitch', 'מזדיין', 'fucker'
]

# הגדרות OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3-8b-instruct"

# קבלת API key מ-environment variable
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

def contains_inappropriate_content(text: str) -> bool:
    """
    בודק אם הטקסט מכיל מילים לא צנועות
    """
    text_lower = text.lower()
    
    for word in INAPPROPRIATE_WORDS:
        if word.lower() in text_lower:
            return True
    
    # בדיקה נוספת עם regex למילים חלקיות
    inappropriate_patterns = [
        r'\b(?:sex|fuck|shit|dick|porn|nude)\b',
        r'\b(?:סקס|זין|כוס|זונה|עירום)\b'
    ]
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False

def get_gpt_response(message: str) -> str:
    """
    מקבל תשובה מ-GPT דרך OpenRouter API (ללא סטרימינג)
    """
    if not OPENROUTER_API_KEY:
        return "שגיאה: API key לא מוגדר. אנא הגדר את OPENROUTER_API_KEY"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Kosher GPT Chat"
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": """אתה עוזר חכם ומועיל שמדבר בעברית. 
                תמיד תן תשובות מקצועיות, ידידותיות ומועילות.
                שמור על שפה נקייה וצנועה בכל התשובות שלך.
                אם מישהו שואל על נושאים לא צנועים, הסבר בעדינות שזה לא מתאים לשיחה."""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        else:
            return "לא הצלחתי לקבל תשובה מה-GPT. אנא נסה שוב."
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter API: {e}")
        return f"שגיאה בתקשורת עם GPT: {str(e)}"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "אירעה שגיאה לא צפויה. אנא נסה שוב."

def stream_gpt_response(message: str):
    """
    מקבל תשובה מ-GPT דרך OpenRouter API עם סטרימינג
    """
    if not OPENROUTER_API_KEY:
        yield f"data: {json.dumps({'error': 'API key לא מוגדר'}, ensure_ascii=False)}\n\n"
        return
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Kosher GPT Chat"
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": """אתה עוזר חכם ומועיל שמדבר בעברית. 
                תמיד תן תשובות מקצועיות, ידידותיות ומועילות.
                שמור על שפה נקייה וצנועה בכל התשובות שלך.
                אם מישהו שואל על נושאים לא צנועים, הסבר בעדינות שזה לא מתאים לשיחה."""
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=60, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_line = line[6:]  # הסרת 'data: '
                    if data_line.strip() == '[DONE]':
                        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                        break
                    
                    try:
                        json_data = json.loads(data_line)
                        if 'choices' in json_data and len(json_data['choices']) > 0:
                            choice = json_data['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content:
                                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        continue
                        
    except requests.exceptions.RequestException as e:
        error_msg = f"שגיאה בתקשורת עם GPT: {str(e)}"
        yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_msg = f"אירעה שגיאה לא צפויה: {str(e)}"
        yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"

@app.route('/')
def index():
    """
    דף הבית - מציג את ממשק הצ'אט
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    נקודת קצה לקבלת הודעות צ'אט עם סטרימינג
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'הודעה חסרה'}), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({'error': 'הודעה ריקה'}), 400
        
        # בדיקת תוכן לא צנוע
        if contains_inappropriate_content(user_message):
            return jsonify({
                'blocked': True,
                'message': 'ההודעה נחסמה בשל תוכן לא צנוע'
            }), 200
        
        # בדיקה אם המשתמש רוצה סטרימינג
        streaming = data.get('streaming', True)
        
        if streaming:
            return Response(
                stream_gpt_response(user_message),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        else:
            # תשובה רגילה ללא סטרימינג
            gpt_response = get_gpt_response(user_message)
            return jsonify({
                'blocked': False,
                'response': gpt_response
            }), 200
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'שגיאה פנימית בשרת'}), 500

@app.route('/health')
def health_check():
    """
    בדיקת בריאות השרת
    """
    return jsonify({
        'status': 'healthy',
        'api_key_configured': bool(OPENROUTER_API_KEY),
        'model': OPENROUTER_MODEL
    }), 200

@app.errorhandler(404)
def not_found(error):
    """
    טיפול בשגיאות 404
    """
    return jsonify({'error': 'הדף לא נמצא'}), 404

@app.errorhandler(500)
def internal_error(error):
    """
    טיפול בשגיאות פנימיות
    """
    return jsonify({'error': 'שגיאה פנימית בשרת'}), 500

if __name__ == '__main__':
    # הגדרת משתני סביבה אם לא מוגדרים
    if not OPENROUTER_API_KEY:
        print("אזהרה: OPENROUTER_API_KEY לא מוגדר!")
        print("אנא הגדר את המשתנה: export OPENROUTER_API_KEY='your_api_key_here'")
        print("או צור קובץ .env עם התוכן: OPENROUTER_API_KEY=your_api_key_here")
    
    print("מתחיל שרת Flask...")
    print(f"דגם GPT: {OPENROUTER_MODEL}")
    print("פתח את הדפדפן בכתובת: http://localhost:5000")
    
    # הפעלה עם פורט דינמי לאינטרנט
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 