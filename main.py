import telebot
import google.generativeai as genai
import random
import time
import os

# --- CONFIG ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyDu6I8LvCycmP3qm0luG39wlS-Exzd1ztI' 
OWNER_ID = 7662143324

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

# --- ID STORAGE SYSTEM ---
ID_FILE = "groups_list.txt"
def save_id(chat_id):
    try:
        if not os.path.exists(ID_FILE): open(ID_FILE, 'w').close()
        with open(ID_FILE, "r+") as f:
            ids = f.read().splitlines()
            if str(chat_id) not in ids:
                f.write(f"{chat_id}\n")
    except: pass

# --- COMMANDS ---
@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"Chat ID: `{message.chat.id}`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return
        with open(ID_FILE, "r") as f:
            for gid in f.read().splitlines():
                try: bot.send_message(gid, text); time.sleep(0.3)
                except: pass
        bot.reply_to(message, "✅ Sabko bhej diya!")

@bot.message_handler(commands=['send'])
def send_msg(message):
    if message.from_user.id == OWNER_ID:
        try:
            parts = message.text.split(' ', 2)
            bot.send_message(parts[1], parts[2])
            bot.reply_to(message, "✅ Message Sent!")
        except: bot.reply_to(message, "Format: `/send ID Message`")

# --- 100% AUTO REPLY ENGINE ---

@bot.message_handler(func=lambda message: True)
def auto_reply(message):
    # Do not reply to other bots
    if message.from_user.is_bot: return
    
    # Save Group ID automatically
    if message.chat.type in ['group', 'supergroup']:
        save_id(message.chat.id)

    try:
        # 1. Feel like a Human: Typing & Reaction
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Random Reaction (Cute vibes)
        try:
            emojis = ['❤️', '✨', '🔥', '😂', '🌸']
            bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji(random.choice(emojis))], is_big=False)
        except: pass

        # 2. AI Prompt Design
        # Personality: Desi, Friendly, 20yr old girl
        prompt = (
            f"You are Manshi, a cool and friendly 20-year-old Indian girl. "
            f"Reply to this message in natural, short Hinglish (1-2 lines max). "
            f"Be sweet but witty. User says: {message.text}"
        )

        # Gemini Configuration
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety)
        response = model.generate_content(prompt)

        # 3. Final Output Logic
        if response and response.text:
            bot.reply_to(message, response.text)
        else:
            # Fallback if Gemini blocks the Hinglish slang
            bot.reply_to(message, "Arre, abhi thoda busy hoon, baad mein baat karein? 😉")

    except Exception as e:
        print(f"Error: {e}")
        # Final emergency reply so bot never stays silent
        bot.reply_to(message, "Hmm, sahi hai! 😂")

if __name__ == "__main__":
    print("Manshi Auto-Reply is Online!")
    bot.infinity_polling(skip_pending=True)