import telebot
from groq import Groq
import time
import os
import random

# --- [ CONFIG FROM ENVIRONMENT VARIABLES ] ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
OWNER_ID = int(os.getenv('OWNER_ID', '7662143324'))

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_KEY)
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
            bot.reply_to(message, "Arre, kuch message toh likho!")
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

# --- [ SEND FEATURE ] ---
@bot.message_handler(commands=['send'])
def send_direct(message):
    if message.from_user.id == OWNER_ID:
        try:
            parts = message.text.split(' ', 2)
            if len(parts) < 3:
                bot.reply_to(message, "Sahi format use karo: `/send ID message`")
                return
            target_id = parts[1]
            msg_to_send = parts[2]
            
            # Typing action for direct send
            bot.send_chat_action(target_id, 'typing')
            time.sleep(1)
            
            bot.send_message(target_id, msg_to_send)
            bot.reply_to(message, f"✅ Message bhej diya target ko!")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

# --- [ ROAST FEATURE ] ---
@bot.message_handler(commands=['roast'])
def roast_user(message):
    target_user = ""
    if message.reply_to_message:
        target_user = f"@{message.reply_to_message.from_user.username}" if message.reply_to_message.from_user.username else message.reply_to_message.from_user.first_name
    else:
        bot.reply_to(message, "Kiski rail banani hai? Kisi ke message par reply karke /roast likho!")
        return

    try:
        # Long typing for dramatic effect
        bot.send_chat_action(message.chat.id, 'typing')
        time.sleep(2) 
        
        roast_prompt = [
            {"role": "system", "content": "You are Manshi, a savage Indian girl from Delhi. Use heavy Mumbai/Delhi slang. Be extremely insulting, funny, and brutal in Hinglish. Roast them so hard they want to leave the group immediately."},
            {"role": "user", "content": f"Roast this person named {target_user} very badly."}
        ]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=roast_prompt,
            temperature=1.0 
        )
        
        bot.reply_to(message.reply_to_message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Arre yaar, roast karne ka mood nahi ban raha abhi! 😂")

# --- [ LOGICAL AUTO REPLY ] ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.from_user.is_bot or message.text.startswith('/'): return

    chat_id = message.chat.id
    if message.chat.type in ['group', 'supergroup']: save_id(chat_id)

    try:
        # Real-time typing feel
        bot.send_chat_action(chat_id, 'typing')
        
        if chat_id not in chat_histories:
            chat_histories[chat_id] = [
                {"role": "system", "content": "You are Manshi, a funny and emotional Indian girl. Reply in short Hinglish. Act like a real person, never mention you are an AI or a bot."}
            ]

        chat_histories[chat_id].append({"role": "user", "content": message.text})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_histories[chat_id],
            temperature=0.8
        )

        response_text = completion.choices[0].message.content

        if response_text:
            # Short delay based on length to mimic human typing speed
            typing_speed = min(len(response_text) * 0.05, 3) 
            time.sleep(typing_speed)
            
            chat_histories[chat_id].append({"role": "assistant", "content": response_text})

            if len(chat_histories[chat_id]) > 10:
                chat_histories[chat_id] = [chat_histories[chat_id][0]] + chat_histories[chat_id][-8:]

            bot.reply_to(message, response_text)

            if random.random() < 0.2:
                sticker_list = ["CAACAgIAAxkBAAELy_Vlz87v7Z-S9Y4S_vUv8S9Y4S_vUv8", "CAACAgIAAxkBAAELy_dlz89P_vUv8S9Y4S_vUv8S9Y4S_vUv8"]
                bot.send_sticker(chat_id, random.choice(sticker_list))

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Yrr, Manshi ka dimaag garam ho gaya hai! 😂")

if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling(skip_pending=True)