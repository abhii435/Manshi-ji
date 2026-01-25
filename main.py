import telebot
import google.generativeai as genai
import random

# --- CONFIG ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyBa1VEEiERuBXVMG9pI-zucTsBSDKNCIQw' 
OWNER_ID = 7662143324

# Setup
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

group_ids = set()

# Broadcast Command (For Owner)
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "Message likho! Example: /broadcast Join Karo")
            return
        for cid in list(group_ids):
            try: bot.send_message(cid, text)
            except: pass
        bot.reply_to(message, "✅ Done!")

# Auto Reply & Reaction
@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    if message.chat.type in ['group', 'supergroup']:
        group_ids.add(message.chat.id)
    try:
        # 1. Reaction
        emo = ['❤️', '🔥', '😂', '😎', '💯']
        bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji(random.choice(emo))])
        
        # 2. AI Reply (Hinglish Style)
        prompt = f"User: {message.text}. Reply like a cool desi friend in Hinglish. Short answer."
        res = model.generate_content(prompt)
        bot.reply_to(message, res.text)
    except: pass

bot.infinity_polling()
