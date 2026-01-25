import telebot
import google.generativeai as genai
import random
import time

# --- CONFIG ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyBa1VEEiERuBXVMG9pI-zucTsBSDKNCIQw' 
OWNER_ID = 7662143324

# --- SETUP ---
bot = telebot.TeleBot(BOT_TOKEN)

# Gemini Configuration
genai.configure(api_key=GEMINI_KEY)

# Safety Settings: Taaki Gemini kisi bhi baat par chup na ho
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Updated Model Name to fix the 404 error
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash-latest',
    safety_settings=safety_settings
)

group_ids = set()

# 1. Broadcast Command
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "Message likho! Example: /broadcast Hello")
            return
        
        send_count = 0
        for cid in list(group_ids):
            try:
                bot.send_message(cid, text)
                send_count += 1
                time.sleep(0.3)
            except: pass
        bot.reply_to(message, f"✅ Done! {send_count} groups mein bhej diya.")

# 2. Main Chat & Reaction Logic
@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    if message.chat.type in ['group', 'supergroup']:
        group_ids.add(message.chat.id)

    try:
        # A. Reaction
        emo = ['❤️', '🔥', '✨', '😎', '💯', '🌸']
        bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji(random.choice(emo))])
        
        # B. AI Reply
        prompt = f"User: {message.text}. You are Manshi, a cool Indian girl. Reply in short, funny Hinglish."
        response = model.generate_content(prompt)
        
        if response and response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Hmm... samajh nahi aaya. 😅")

    except Exception as e:
        print(f"Error occurred: {e}")

# --- START BOT ---
if __name__ == "__main__":
    print("Manshi AI is Online on Railway!")
    # skip_pending=True fixes the 409 Conflict error
    bot.infinity_polling(skip_pending=True)