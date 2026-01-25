import telebot
import google.generativeai as genai
import random
import time
import os

# --- CONFIG ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyBa1VEEiERuBXVMG9pI-zucTsBSDKNCIQw' 
OWNER_ID = 7662143324

bot = telebot.TeleBot(BOT_TOKEN)

# --- GEMINI SETUP ---
try:
    genai.configure(api_key=GEMINI_KEY)
    # Model configuration with no safety blocks
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
except Exception as e:
    print(f"Gemini Init Error: {e}")

# --- GROUP ID STORAGE ---
ID_FILE = "groups_list.txt"
def save_id(chat_id):
    try:
        with open(ID_FILE, "a+") as f:
            f.seek(0)
            ids = f.read().splitlines()
            if str(chat_id) not in ids:
                f.write(f"{chat_id}\n")
    except: pass

# --- SMART FALLBACK MESSAGES ---
fallback_replies = [
    "Hmm, sahi keh rahe ho! 😂", "Achha? Phir kya hua?", "Arre waah, ye mast tha!",
    "Mujhe bhi aisa hi lagta hai... ✨", "Bolte raho, main sun rahi hoon. 😉",
    "Haha, tum kaafi funny ho!", "Thoda busy thi, ab bolo kya haal hai?"
]

# --- HANDLERS ---

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return
        if os.path.exists(ID_FILE):
            with open(ID_FILE, "r") as f:
                for gid in f.read().splitlines():
                    try:
                        bot.send_message(gid, text)
                        time.sleep(0.3)
                    except: pass
        bot.reply_to(message, "✅ Done!")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.from_user.is_bot: return
    if message.chat.type in ['group', 'supergroup']:
        save_id(message.chat.id)

    # 1. Action: Typing & Reaction
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji('❤')], is_big=False)
    except: pass

    # 2. AI Response Logic
    reply_sent = False
    try:
        # Prompt for Manshi's personality
        prompt = f"You are Manshi, a cool desi girl. Reply shortly in Hinglish: {message.text}"
        response = model.generate_content(prompt)
        
        if response and response.text:
            bot.reply_to(message, response.text)
            reply_sent = True
    except Exception as e:
        print(f"AI Error: {e}")

    # 3. SUPER FALLBACK: If AI fails, send a manual reply (100% guarantee)
    if not reply_sent:
        time.sleep(1)
        bot.reply_to(message, random.choice(fallback_replies))

if __name__ == "__main__":
    print("Manshi AI is Online and 100% Ready!")
    bot.infinity_polling(skip_pending=True)