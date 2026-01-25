import telebot
import google.generativeai as genai
import random
import time
import os

# --- CONFIG ---
BOT_TOKEN = '8386752629:AAFtI0gvAVD171v4qb44EW_cg2sYeDjDT0E'
GEMINI_KEY = 'AIzaSyBa1VEEiERuBXVMG9pI-zucTsBSDKNCIQw' 
OWNER_ID = 7662143324

# --- INITIALIZATION ---
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Group ID Storage System
ID_FILE = "groups_list.txt"

def load_ids():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_id(chat_id):
    ids = load_ids()
    if str(chat_id) not in ids:
        with open(ID_FILE, "a") as f:
            f.write(f"{chat_id}\n")

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Hi! Main Manshi hoon. Mujhe group mein add karo aur main wahan sabse baatein karungi! ✨")

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"Is chat ki ID: `{message.chat.id}`")

@bot.message_handler(commands=['broadcast'])
def broadcast_all(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "Usage: `/broadcast Hello everyone`")
            return
        gids = load_ids()
        success = 0
        for gid in gids:
            try:
                bot.send_message(gid, text)
                success += 1
                time.sleep(0.5)
            except: pass
        bot.reply_to(message, f"✅ Broadcast sent to {success} groups.")

@bot.message_handler(commands=['send'])
def send_specific(message):
    if message.from_user.id == OWNER_ID:
        try:
            parts = message.text.split(' ', 2)
            target_id = parts[1]
            msg_text = parts[2]
            bot.send_message(target_id, msg_text)
            bot.reply_to(message, f"✅ Message sent to {target_id}")
        except:
            bot.reply_to(message, "Usage: `/send [ChatID] [Message]`")

# --- MAIN AUTO REPLY LOGIC ---

@bot.message_handler(func=lambda message: True)
def auto_reply(message):
    # 1. Group ID Save Karein (Agar group hai)
    if message.chat.type in ['group', 'supergroup']:
        save_id(message.chat.id)

    # 2. Don't reply to other bots
    if message.from_user.is_bot:
        return

    try:
        # A. Random Reaction (70% chance)
        if random.random() < 0.7:
            try:
                bot.set_message_reaction(message.chat.id, message.message_id, [telebot.types.ReactionTypeEmoji(random.choice(['❤️','🔥','✨','😂']))], is_big=False)
            except: pass

        # B. Typing Status (Human-like feeling)
        bot.send_chat_action(message.chat.id, 'typing')
        time.sleep(random.uniform(1.5, 3.0)) # 1.5 se 3 second ka wait

        # C. Gemini AI Response
        system_prompt = (
            "You are Manshi, a cool, 20-year-old Indian girl. You are friendly, "
            "sometimes funny, and talk in short natural Hinglish. Keep it real, "
            "don't act like a robot. User says: "
        )
        
        response = model.generate_content(system_prompt + message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Achha? Phir se bolo...")

    except Exception as e:
        print(f"Log Error: {e}")

# --- START BOT ---
if __name__ == "__main__":
    print("--- Manshi Pro AI is Active ---")
    bot.infinity_polling(skip_pending=True)