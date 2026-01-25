import telebot
import google.generativeai as genai
import random
import time

# --- CONFIG ---
# Maine wahi tokens use kiye hain jo aapne upar diye the
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyBa1VEEiERuBXVMG9pI-zucTsBSDKNCIQw' 
OWNER_ID = 7662143324

# --- SETUP ---
bot = telebot.TeleBot(BOT_TOKEN)

# Gemini Configuration with Safety Settings (Taaki reply block na ho)
genai.configure(api_key=GEMINI_KEY)

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=safety_settings
)

group_ids = set()

# 1. Broadcast Command (Only for you)
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "Message toh likho! Example: /broadcast Hello Guys")
            return
        
        send_count = 0
        for cid in list(group_ids):
            try:
                bot.send_message(cid, text)
                send_count += 1
                time.sleep(0.3) # Spam protection
            except:
                pass
        bot.reply_to(message, f"✅ Done! {send_count} groups mein message bhej diya.")

# 2. Main AI Logic & Reaction
@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    # Group ID save karna broadcast ke liye
    if message.chat.type in ['group', 'supergroup']:
        group_ids.add(message.chat.id)

    try:
        # A. Reaction (Turant confirmation ke liye)
        emo = ['❤️', '🔥', '✨', '😎', '💯', '🌸', '👀']
        bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji(random.choice(emo))])
        
        # B. AI Response
        # System instructions taaki Manshi ki tarah behave kare
        prompt = (
            f"Context: You are a cool, friendly Indian girl named Manshi. "
            f"You talk in short, natural Hinglish. User says: {message.text}"
        )
        
        response = model.generate_content(prompt)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Hmm... samajh nahi aaya, phir se bolo? 😅")

    except Exception as e:
        print(f"Error occurred: {e}")
        # Agar error aaye toh bot crash nahi hoga, bas log mein dikhega

# --- START BOT ---
if __name__ == "__main__":
    print("Manshi AI is Online and Safe!")
    # skip_pending=True isse purane 409 Conflict errors nahi aayenge
    bot.infinity_polling(skip_pending=True)