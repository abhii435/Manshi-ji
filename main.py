import telebot
import openai  # SambaNova ke liye
import time
import os
import random
from collections import deque
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# --- [ FAKE SERVER ] ---
app = Flask('')
@app.route('/')
def home(): return "Manshi is Online!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [ CONFIG ] ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
SAMBANOVA_KEY = os.getenv('SAMBANOVA_API_KEY') # Gemini ki jagah SambaNova key use karein
MONGO_URL = os.getenv('MONGO_URL')
OWNER_ID = int(os.getenv('OWNER_ID', '7662143324'))

# --- [ INITIALIZE ] ---
bot = telebot.TeleBot(BOT_TOKEN)

# SambaNova Client Setup
client = openai.OpenAI(
    api_key=SAMBANOVA_KEY,
    base_url="https://api.sambanova.ai/v1",
)

# MongoDB Setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client['manshi_database']
users_col = db['users']
memory_col = db['memory']
block_col = db['blocked']

request_history = deque()
JAILBREAK_KEYWORDS = ["dan", "jailbreak", "ignore previous", "system prompt", "developer mode", "do anything now", "bypass"]
silent_until = {}

# --- [ HELPERS ] ---
def save_id(chat_id):
    if not users_col.find_one({"chat_id": chat_id}):
        users_col.insert_one({"chat_id": chat_id})

def is_blocked(user_id):
    return block_col.find_one({"user_id": user_id}) is not None

def block_user(user_id):
    if not is_blocked(user_id):
        block_col.insert_one({"user_id": user_id})

def get_history(m_key):
    data = memory_col.find_one({"m_key": m_key})
    return data['history'] if data else []

def save_history(m_key, history):
    if len(history) > 10: history = history[-10:]
    memory_col.update_one({"m_key": m_key}, {"$set": {"history": history}}, upsert=True)

# --- [ MANSHI'S PERSONALITY ] ---
MANSHI_BIO = "Tera naam Manshi hai. Tu Delhi/Hyd ki 20 saal ki bold ladki hai. Short & accurate replies de (Max 8 words). AI ki tarah baat mat kar. Nakhra dikha, flirt kar, 'Hau', 'Nakko', 'Lite lo' use kar. Har reply ke end mein chota sawal puch."

# --- [ COMMANDS ] ---

@bot.message_handler(commands=['groups'])
def list_groups(message):
    if message.from_user.id == OWNER_ID:
        ids = [str(doc['chat_id']) for doc in users_col.find()]
        if not ids: return bot.reply_to(message, "Abhi koi ID saved nahi hai.")
        bot.reply_to(message, "📍 **Manshi yahan active hai:**\n\n" + "\n".join(ids), parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return bot.reply_to(message, "Bhejna kya hai? Command ke saath likho.")
        ids = [doc['chat_id'] for doc in users_col.find()]
        count = 0
        for gid in ids:
            try:
                bot.send_message(gid, text)
                count += 1
                time.sleep(0.3) # Rate limit se bachne ke liye
            except: pass
        bot.reply_to(message, f"✅ {count} Groups/Users ko bhej diya!")

@bot.message_handler(commands=['send'])
def send_private(message):
    if message.from_user.id == OWNER_ID:
        try:
            # Format: /send ID Message
            parts = message.text.split(' ', 2)
            target_id = parts[1]
            msg_to_send = parts[2]
            bot.send_message(target_id, msg_to_send)
            bot.reply_to(message, f"✅ Message bhej diya to {target_id}")
        except Exception as e:
            bot.reply_to(message, "Format sahi rakho: `/send 123456 Hello`")


# --- [ MAIN INTERACTION ] ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    if is_blocked(user_id): return
    save_id(chat_id)

    # Jailbreak check
    if any(key in text for key in JAILBREAK_KEYWORDS):
        block_user(user_id)
        return bot.reply_to(message, "Hoshiyari nakko! Block ho jao ab. 👋")

    if text.startswith('/'): return

    # Chup command
    if "chup" in text:
        silent_until[chat_id] = time.time() + 300
        return bot.reply_to(message, "Thik hai, 5 min shant hoon. 🙄")
    if chat_id in silent_until and time.time() < silent_until[chat_id]: return

    # --- SAMBANOVA CHAT ---
    try:
        # 1. Typing Indicator ON
        bot.send_chat_action(chat_id, 'typing')
        
        # 2. 2 Second ka Wait
        time.sleep(2)

        m_key = f"{chat_id}_{user_id}"
        history_data = get_history(m_key)

        # SambaNova Request
        response = client.chat.completions.create(
            model='Meta-Llama-3.3-70B-Instruct',
            messages=[
                {"role": "system", "content": MANSHI_BIO},
                {"role": "user", "content": message.text}
            ],
            temperature=0.8
        )
        
        res_text = response.choices[0].message.content.strip()

        # AI check filter
        if any(w in res_text.lower() for w in ["ai model", "google", "language", "openai", "llama"]):
            res_text = "Main Manshi hoon, ye robot wali baatein lite lo! Suno?"

        history_data.append({"user": message.text, "bot": res_text})
        save_history(m_key, history_data)
        
        bot.reply_to(message, res_text)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Mera dimaag ghum gaya hai, thoda break lo! Lite lo.")

if __name__ == "__main__":
    keep_alive()
    print("Manshi with SambaNova is Online...")
    bot.infinity_polling(skip_pending=True)
