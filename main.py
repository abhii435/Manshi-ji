import telebot
import google.generativeai as genai
import random
import time
import os
import requests

# --- [ CONFIGURATION ] ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyDu6I8LvCycmP3qm0luG39wlS-Exzd1ztI' 
OWNER_ID = 7662143324

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

# Memory Storage
chat_histories = {} 
ID_FILE = "groups_list.txt"

# --- [ UTILS ] ---
def save_id(chat_id):
    try:
        if not os.path.exists(ID_FILE): open(ID_FILE, 'w').close()
        with open(ID_FILE, "r+") as f:
            ids = f.read().splitlines()
            if str(chat_id) not in ids:
                f.write(f"{chat_id}\n")
    except: pass

# --- [ COMMAND HANDLERS ] ---

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"📍 Chat ID: `{message.chat.id}`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return
        with open(ID_FILE, "r") as f:
            for gid in f.read().splitlines():
                try: bot.send_message(gid, text); time.sleep(0.3)
                except: pass
        bot.reply_to(message, "✅ Broadcast Successful!")

@bot.message_handler(commands=['send'])
def send_msg(message):
    if message.from_user.id == OWNER_ID:
        try:
            _, target, msg = message.text.split(' ', 2)
            bot.send_message(target, msg)
            bot.reply_to(message, "✅ Message Delivered!")
        except: bot.reply_to(message, "Format: `/send ID Message`")

@bot.message_handler(commands=['draw'])
def draw(message):
    prompt = message.text.replace('/draw', '').strip()
    if not prompt:
        bot.reply_to(message, "Kya banau? Example: `/draw space cat`")
        return
    bot.send_chat_action(message.chat.id, 'upload_photo')
    img_url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={random.randint(1,9999)}"
    bot.send_photo(message.chat.id, img_url, caption=f"Ye lo baby tumhare liye: {prompt}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for user in message.new_chat_members:
        bot.reply_to(message, f"Swagat karo {user.first_name} ka! ✨ Manshi ke group mein aa gaye ho, ab maze karo! 😉")

# --- [ THE BRAIN: AUTO-REPLY + MEMORY ] ---

@bot.message_handler(func=lambda message: True)
def auto_reply(message):
    if message.from_user.is_bot or message.text.startswith('/'): return
    
    chat_id = message.chat.id
    if message.chat.type in ['group', 'supergroup']: save_id(chat_id)

    # Initialize history if not present
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    try:
        bot.send_chat_action(chat_id, 'typing')
        
        # Safety Settings (Unfiltered)
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

        model = genai.GenerativeModel(model_name="gemini-1.5-flash", safety_settings=safety)
        
        # Start chat with memory
        convo = model.start_chat(history=chat_histories[chat_id])
        
        # Human-like Prompt
        full_prompt = (
            f"You are Manshi, a 20yo cool Indian girl. Reply to {message.from_user.first_name} "
            f"in very short, witty Hinglish. Remember previous context. "
            f"Message: {message.text}"
        )
        
        response = convo.send_message(full_prompt)
        
        if response.text:
            # Update memory (keeping last 12 exchanges)
            chat_histories[chat_id] = convo.history[-12:]
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Achha? Phir se bolna... 😉")

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Hmm, sahi hai! 😂")

if __name__ == "__main__":
    print("🚀 Manshi High-Class Bot is LIVE!")
    bot.infinity_polling(skip_pending=True)