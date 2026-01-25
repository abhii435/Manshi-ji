import telebot
import google.generativeai as genai
import random
import time

# --- CONFIG ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyBa1VEEiERuBXVMG9pI-zucTsBSDKNCIQw' 
OWNER_ID = 7662143324

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)

# Anti-Block Safety Settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', safety_settings=safety_settings)

# Global set for group IDs
group_ids = set()

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "Message likho! Example: /broadcast Hello")
            return
        
        if not group_ids:
            bot.reply_to(message, "Abhi koi group ID save nahi hai. Pehle groups mein ek message karo!")
            return

        send_count = 0
        for cid in list(group_ids):
            try:
                bot.send_message(cid, text)
                send_count += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"Broadcast failed for {cid}: {e}")
        
        bot.reply_to(message, f"✅ Broadcast Done! Total {send_count} groups mein bhej diya gaya.")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    # ID save karna
    if message.chat.type in ['group', 'supergroup']:
        group_ids.add(message.chat.id)

    try:
        # Reaction
        emo = ['❤️', '🔥', '✨', '🌸', '💯']
        bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji(random.choice(emo))])
        
        # AI Reply
        prompt = f"You are Manshi, a cool girl. Reply in short Hinglish: {message.text}"
        response = model.generate_content(prompt)
        
        if response and response.text:
            bot.reply_to(message, response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Manshi is Online!")
    bot.infinity_polling(skip_pending=True)