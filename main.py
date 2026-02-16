import telebot
import google.generativeai as genai
import time
import os
import random
from collections import deque
from pymongo import MongoClient
from flask import Flask          # <--- Naya add kiya
from threading import Thread    # <--- Naya add kiya

# --- [ FAKE SERVER FOR RENDER PORT ERROR ] ---
app = Flask('')

@app.route('/')
def home():
    return "Manshi is Online!"

def run():
    # Render port 8080 ya kisi bhi port ko scan karta hai
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [ CONFIG ] ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')
MONGO_URL = os.getenv('MONGO_URL')
OWNER_ID = int(os.getenv('OWNER_ID', '7662143324'))

# --- [ INITIALIZE ] ---
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# MongoDB Setup
client = MongoClient(MONGO_URL)
db = client['manshi_database']
users_col = db['users']
memory_col = db['memory']
block_col = db['blocked']

# Rate Limiter Global Variables
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
    if len(history) > 10:
        history = history[-10:]
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
        if not text: return bot.reply_to(message, "Bhejnu kya hai?")
        ids = [doc['chat_id'] for doc in users_col.find()]
        count = 0
        for gid in ids:
            try:
                bot.send_message(gid, text)
                count += 1
                time.sleep(0.3)
            except: pass
        bot.reply_to(message, f"✅ {count} Groups/Users ko bhej diya!")

# --- [ MAIN INTERACTION ] ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    if is_blocked(user_id): return
    save_id(chat_id)

    if any(key in text for key in JAILBREAK_KEYWORDS):
        block_user(user_id)
        return bot.reply_to(message, "Hoshiyari nakko! Block ho jao ab. 👋")

    if text.startswith('/'): return

    if "chup" in text:
        silent_until[chat_id] = time.time() + 300
        return bot.reply_to(message, "Thik hai, 5 min shant hoon. 🙄")
    if chat_id in silent_until and time.time() < silent_until[chat_id]: return

    if "roast" in text:
        return bot.reply_to(message, random.choice(["Shakal dekhi hai? Lite lo!", "Zyada dimaag nakko chalao baby.", "Kamine! Tujhse na ho payega."]))

    # --- RATE LIMITER ---
    current_time = time.time()
    while request_history and current_time - request_history[0] > 60:
        request_history.popleft()

    if len(request_history) >= 10:
        msg = bot.reply_to(message, "Arre ruko! Manshi thak gayi hai, 20 second baad aati hoon... 😴")
        time.sleep(20)
        try: bot.delete_message(chat_id, msg.message_id)
        except: pass

    # --- GEMINI CHAT ---
    try:
        bot.send_chat_action(chat_id, 'typing')
        m_key = f"{chat_id}_{user_id}"
        history_data = get_history(m_key)

        response = model.generate_content(f"Context: {MANSHI_BIO}\nUser says: {message.text}")
        res_text = response.text.strip()

        if any(w in res_text.lower() for w in ["ai model", "google", "language"]):
            res_text = "Main Manshi hoon, ye robot wali baatein lite lo! Suno?"

        history_data.append({"user": message.text, "bot": res_text})
        save_history(m_key, history_data)
        request_history.append(time.time())

        bot.reply_to(message, res_text)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Mera dimaag ghum gaya hai, thoda break lo! Lite lo.")

if __name__ == "__main__":
    keep_alive() # <--- Fake server start karega
    print("Manshi with Gemini & MongoDB is Online...")
    bot.infinity_polling(skip_pending=True)
