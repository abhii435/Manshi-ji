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

# Memory dictionary for feelings and context
chat_histories = {}

# --- [ STICKER BANK ] ---
# Ye stickers Manshi ke emotions dikhayenge
stickers = {
    "happy": ["CAACAgIAAxkBAAEL...", "CAACAgIAAxkBAAEL..."], # Yahan sticker file_id daal sakte ho
    "love": ["CAACAgIAAxkBAAEP...", "CAACAgEAAxkBAAE..."],
    "funny": ["CAACAgIAAxkBAAEJ...", "CAACAgIAAxkBAAE..."],
    "sad": ["CAACAgIAAxkBAAE..."]
}

# --- [ UTILS ] ---
def save_id(chat_id):
    if not os.path.exists(ID_FILE): open(ID_FILE, 'w').close()
    with open(ID_FILE, "r+") as f:
        ids = f.read().splitlines()
        if str(chat_id) not in ids:
            f.write(f"{chat_id}\n")

# --- [ AUTO REPLY WITH HUMAN FEELINGS ] ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.from_user.is_bot or message.text.startswith('/'): return
    
    chat_id = message.chat.id
    if message.chat.type in ['group', 'supergroup']: save_id(chat_id)

    try:
        # 1. Typing Feeling
        bot.send_chat_action(chat_id, 'typing')
        
        # 2. Memory Setup
        if chat_id not in chat_histories:
            chat_histories[chat_id] = []
            
        model = genai.GenerativeModel('gemini-1.5-flash')
        convo = model.start_chat(history=chat_histories[chat_id])
        
        # 3. Prompt for Human Emotions
        prompt = (
            f"You are Manshi, a 20-year-old girl with deep feelings. "
            f"Talk to {message.from_user.first_name} like a real human, not a bot. "
            f"Use Hinglish, show emotions (joy, anger, love, or sarcasm). "
            f"Keep it short and very natural. Current message: {message.text}"
        )
        
        response = convo.send_message(prompt)
        
        if response.text:
            chat_histories[chat_id] = convo.history[-10:]
            
            # 4. RANDOM STICKER REACTION (Feelings)
            # Agar message mein 'pyar', 'love', 'haha', 'sad' jaisa kuch hai toh sticker bhejegi
            res_low = response.text.lower()
            bot.reply_to(message, response.text)

            # Stickers bhejne ka logic (Emoji reactions)
            if any(word in res_low for word in ["love", "pyar", "heart", "❤️"]):
                bot.send_sticker(chat_id, "CAACAgIAAxkBAAELy_Vlz87v7Z-S9Y4S_vUv8S9Y4S_vUv8") # Example Sticker ID
            elif any(word in res_low for word in ["haha", "funny", "😂", "lol"]):
                bot.send_sticker(chat_id, "CAACAgIAAxkBAAELy_dlz89P_vUv8S9Y4S_vUv8S9Y4S_vUv8")

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Arre yaar, dimaag kharab ho gaya mera! 😂")

if __name__ == "__main__":
    print("🚀 Manshi (The Human) is LIVE!")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)