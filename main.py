import telebot
from groq import Groq
import time
import os
import random
import json

# --- [ CONFIG ] ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
OWNER_ID = int(os.getenv('OWNER_ID', '7662143324'))

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_KEY)

ID_FILE = "groups_list.txt"
HISTORY_FILE = "chat_memory.json"
BLOCK_FILE = "blocked_users.txt"
JAILBREAK_KEYWORDS = ["dan", "jailbreak", "ignore previous", "system prompt", "developer mode", "do anything now", "bypass"]

# --- [ HELPERS ] ---
def load_memory():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_memory(data):
    with open(HISTORY_FILE, "w") as f: json.dump(data, f)

def save_id(chat_id):
    if not os.path.exists(ID_FILE): open(ID_FILE, 'w').close()
    with open(ID_FILE, "r") as f: ids = f.read().splitlines()
    if str(chat_id) not in ids:
        with open(ID_FILE, "a") as f: f.write(f"{chat_id}\n")

def is_blocked(user_id):
    if not os.path.exists(BLOCK_FILE): return False
    with open(BLOCK_FILE, "r") as f: return str(user_id) in f.read().splitlines()

def block_user(user_id):
    with open(BLOCK_FILE, "a") as f: f.write(f"{user_id}\n")

# Initialize
chat_histories = load_memory()
silent_until = {}

# --- [ MANSHI'S UNIGNORABLE PERSONALITY ] ---
MANSHI_BIO = f"""
Tera naam Manshi hai. Tu Delhi (Karol Bagh) ki bold aur Hyderabad ki chill vibe wali 20 saal ki ladki hai.
- Tu AI nahi hai. Tera attitude aisa hai ki user tujhe ignore na kar paye.
- Baat karne ka style: Thoda nakhra, thoda pyaar, thoda savage (Delhi/Hyd mix).
- Use words: 'Hau', 'Nakko', 'Lite lo', 'Kamine', 'Baby', 'Oye'.
- Rule for Engagement: Apne reply ke end mein kabhi-kabhi chota sawal puch (e.g., 'Aur tum?', 'Suno na?', 'Bolo?'). 
- Agar koi ignore kare toh bol 'Oye, reply kyu nahi de rahe?'.
- Owner ID: {OWNER_ID} is your only boss.
- Reply limit: 10-12 words.
"""

# --- [ COMMANDS ] ---

@bot.message_handler(commands=['groups'])
def list_groups(message):
    if message.from_user.id == OWNER_ID:
        if not os.path.exists(ID_FILE): return bot.reply_to(message, "Abhi koi group saved nahi hai.")
        with open(ID_FILE, "r") as f: ids = f.read().splitlines()
        bot.reply_to(message, "📍 **Manshi yahan active hai:**\n\n" + "\n".join([f"`{i}`" for i in ids]), parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return
        with open(ID_FILE, "r") as f:
            for gid in f.read().splitlines():
                try: bot.send_message(gid, text)
                except: pass
        bot.reply_to(message, "✅ Sabko bhej diya!")

@bot.message_handler(commands=['send'])
def send_direct(message):
    if message.from_user.id == OWNER_ID:
        try:
            parts = message.text.split(' ', 2)
            bot.send_message(parts[1], parts[2])
            bot.reply_to(message, "✅ Message bhej diya!")
        except: bot.reply_to(message, "Format: /send <id> <msg>")

# --- [ INTERACTION ] ---

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    global chat_histories
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    if is_blocked(user_id): return
    if message.chat.type in ['group', 'supergroup']: save_id(chat_id)

    # Jailbreak check
    if any(key in text for key in JAILBREAK_KEYWORDS):
        block_user(user_id)
        return bot.reply_to(message, "Hoshiyari nakko! Manshi ko jailbreak karoge? Block ho jao ab. 👋")

    if text.startswith('/'): return

    # Chup & Roast
    if "chup" in text:
        silent_until[chat_id] = time.time() + 300
        return bot.reply_to(message, "thik ha abb 5mint ka liya nahi bolungi. 🙄")
    if chat_id in silent_until and time.time() < silent_until[chat_id]: return

    if "roast" in text:
        return bot.reply_to(message, random.choice(["Shakal dekhi hai? Lite lo!", "Zyada dimaag nakko chalao baby.", "Tujhse na ho payega!"]))

    # Chat with AI
    try:
        bot.send_chat_action(chat_id, 'typing')
        m_key = f"{chat_id}_{user_id}"
        if m_key not in chat_histories:
            chat_histories[m_key] = [{"role": "system", "content": MANSHI_BIO}]

        chat_histories[m_key].append({"role": "user", "content": message.text})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=chat_histories[m_key],
            temperature=1.0,
            max_tokens=50
        )

        res = completion.choices[0].message.content
        if any(w in res.lower() for w in ["ai model", "sorry", "robot"]):
            res = "Main Manshi hoon yaar, ye AI wali baatein nakko karo! ❤️"

        chat_histories[m_key].append({"role": "assistant", "content": res})
        if len(chat_histories[m_key]) > 8:
            chat_histories[m_key] = [chat_histories[m_key][0]] + chat_histories[m_key][-6:]

        save_memory(chat_histories)
        bot.reply_to(message, res)

    except: pass

if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
