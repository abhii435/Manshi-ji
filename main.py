import telebot
from groq import Groq
import time
import os
import random
import json

# --- [ CONFIG ] ---
# Apne Environment Variables set karein ya yahan direct keys dalein
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

# --- [ MANSHI'S PERSONALITY ] ---
MANSHI_BIO = """
Tera naam Manshi hai. Tu Delhi/Hyd ki 20 saal ki bold ladki hai.
- Short & accurate replies de (Max 5-8 words).
- AI ki tarah baat mat kar. Real ladki ban.
- Nakhra dikha, flirt kar, aur 'Hau', 'Nakko', 'Lite lo', 'Kamine', 'Baby' use kar.
- Har reply ke end mein chota sawal puch (e.g., 'Aur?', 'Suno?', 'Bolo?').
"""

# --- [ COMMANDS ] ---

@bot.message_handler(commands=['groups'])
def list_groups(message):
    if message.from_user.id == OWNER_ID:
        if not os.path.exists(ID_FILE): return bot.reply_to(message, "Abhi koi ID saved nahi hai.")
        with open(ID_FILE, "r") as f: ids = f.read().splitlines()
        bot.reply_to(message, "📍 **Manshi yahan active hai:**\n\n" + "\n".join([f"`{i}`" for i in ids]), parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return bot.reply_to(message, "Bhejnu kya hai? Kuch likho!")
        with open(ID_FILE, "r") as f: ids = f.read().splitlines()
        count = 0
        for gid in ids:
            try:
                bot.send_message(gid, text)
                count += 1
                time.sleep(0.3)
            except: pass
        bot.reply_to(message, f"✅ {count} Groups/Users ko broadcast bhej diya!")

@bot.message_handler(commands=['send'])
def send_direct(message):
    if message.from_user.id == OWNER_ID:
        try:
            parts = message.text.split(' ', 2)
            bot.send_message(parts[1], parts[2])
            bot.reply_to(message, "✅ Message bhej diya!")
        except: bot.reply_to(message, "Format: /send <id> <msg>")

# --- [ MAIN INTERACTION ] ---

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    global chat_histories
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.lower()

    if is_blocked(user_id): return
    
    # Save ID for both Personal & Group Broadcasts
    save_id(chat_id)

    # Jailbreak check
    if any(key in text for key in JAILBREAK_KEYWORDS):
        block_user(user_id)
        return bot.reply_to(message, "Hoshiyari nakko! Manshi ko jailbreak karoge? Block ho jao ab. 👋")

    if text.startswith('/'): return

    # Chup & Roast
    if "chup" in text:
        silent_until[chat_id] = time.time() + 300
        return bot.reply_to(message, "Thik hai, 5 min shant hoon. 🙄")
    if chat_id in silent_until and time.time() < silent_until[chat_id]: return

    if "roast" in text:
        return bot.reply_to(message, random.choice(["Shakal dekhi hai? Lite lo!", "Zyada dimaag nakko chalao baby.", "Kamine! Tujhse na ho payega."]))

    # --- Chat with Groq AI ---
    try:
        bot.send_chat_action(chat_id, 'typing')
        m_key = f"{chat_id}_{user_id}"
        
        if m_key not in chat_histories:
            chat_histories[m_key] = [{"role": "system", "content": MANSHI_BIO}]

        chat_histories[m_key].append({"role": "user", "content": message.text})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=chat_histories[m_key],
            temperature=0.9,
            max_tokens=30
        )

        res = completion.choices[0].message.content
        if any(w in res.lower() for w in ["ai model", "robot", "language model"]):
            res = "Main Manshi hoon, ye robot wali baatein lite lo! Suno?"

        chat_histories[m_key].append({"role": "assistant", "content": res})
        
        # Keep History Short but Persistent
        if len(chat_histories[m_key]) > 10:
            chat_histories[m_key] = [chat_histories[m_key][0]] + chat_histories[m_key][-8:]

        save_memory(chat_histories)
        bot.reply_to(message, res)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Manshi is Online...")
    bot.infinity_polling(skip_pending=True)
