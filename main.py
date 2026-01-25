import telebot
import google.generativeai as genai
import time
import os
import random

# --- [ CONFIG ] ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyDu6I8LvCycmP3qm0luG39wlS-Exzd1ztI' 
OWNER_ID = 7662143324

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
ID_FILE = "groups_list.txt"

# Memory management
chat_histories = {}

# --- [ UTILS ] ---
def save_id(chat_id):
    if not os.path.exists(ID_FILE):
        with open(ID_FILE, "w") as f: f.write("")
    with open(ID_FILE, "r+") as f:
        ids = f.read().splitlines()
        if str(chat_id) not in ids:
            f.write(f"{chat_id}\n")

# --- [ BROADCAST ] ---
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "Kuch likho toh sahi!")
            return
        
        count = 0
        if os.path.exists(ID_FILE):
            with open(ID_FILE, "r") as f:
                for gid in f.read().splitlines():
                    try:
                        bot.send_message(gid, text)
                        count += 1
                        time.sleep(0.3)
                    except: pass
        bot.reply_to(message, f"✅ {count} groups mein broadcast bhej diya!")

# --- [ LOGICAL AUTO REPLY ] ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.from_user.is_bot or message.text.startswith('/'): return
    
    chat_id = message.chat.id
    if message.chat.type in ['group', 'supergroup']: save_id(chat_id)

    try:
        bot.send_chat_action(chat_id, 'typing')
        
        # Initialize memory if not exists
        if chat_id not in chat_histories:
            chat_histories[chat_id] = []
            
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Logical Instruction: No repetition, human-like flow
        prompt = (
            f"User name: {message.from_user.first_name}. "
            "You are Manshi, a funny and emotional Indian girl. "
            "Rules: 1. Don't repeat previous lines. 2. Give short, fresh Hinglish replies. "
            "3. Act like a real person, not a bot. 4. If user says 'hi', don't just say 'hi', say something more."
            f"\nUser says: {message.text}"
        )
        
        # Start chat with history
        convo = model.start_chat(history=chat_histories[chat_id])
        response = convo.send_message(prompt)
        
        if response.text:
            # Update memory and keep it limited to last 10 messages to avoid confusion
            chat_histories[chat_id] = convo.history[-10:]
            bot.reply_to(message, response.text)
            
            # --- Random Sticker Logic (Feelings) ---
            if random.random() < 0.3: # 30% chance to send sticker
                sticker_list = [
                    "CAACAgIAAxkBAAELy_Vlz87v7Z-S9Y4S_vUv8S9Y4S_vUv8", # Happy
                    "CAACAgIAAxkBAAELy_dlz89P_vUv8S9Y4S_vUv8S9Y4S_vUv8"  # Fun
                ]
                bot.send_sticker(chat_id, random.choice(sticker_list))
        else:
            bot.reply_to(message, "Arre, kuch logical bolo na! 😉")

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Abhi mood nahi hai baat karne ka! 😂")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)