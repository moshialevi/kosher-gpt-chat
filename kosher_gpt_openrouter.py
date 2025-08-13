import requests

# 🔑 שים פה את המפתח שלך מ־OpenRouter
API_KEY = "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"  # ← תכניס כאן את המפתח שלך

# כתובת ה־API של OpenRouter
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# רשימת מילים שאינן כשרות
blacklist = ["סקס", "חזה", "מין", "תשוקה", "עירום", "פורנ", "אירוטי"]

def is_kosher(prompt):
    for word in blacklist:
        if word in prompt.lower():
            return False
    return True

def ask_gpt(question):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "אתה עוזר אינטיליגנטי לקהל חרדי. "
        "אל תענה על נושאים לא צנועים או לא הולמים. "
        "ענה בעברית תקנית בלבד. אל תערבב אנגלית ועברית."
    )

    data = {
        "model": "meta-llama/llama-3-8b-instruct",  # מודל חינמי ויציב
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        print("❌ שגיאה מהשרת:", response.status_code, response.text)
        return None

# צ'אט פשוט
while True:
    user_input = input("שאל שאלה (או 'יציאה' כדי לצאת): ")

    if user_input.lower() in ["יציאה", "exit", "quit"]:
        print("ביי מוישי 👋")
        break

    if not is_kosher(user_input):
        print("⚠️ השאלה הזו אינה מתאימה לצ'אט כשר.")
        continue

    answer = ask_gpt(user_input)
    if answer:
        print("GPT:", answer)
