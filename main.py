import telebot
from groq import Groq
import time
import os
import random

# --- [ CONFIG ] ---
# Railway Variables se keys uthayega
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_KEY')
OWNER_ID = int(os.getenv('OWNER_ID', '7662143324'))

# Initial Check
if not BOT_TOKEN or not GROQ_KEY:
    print("❌ ERROR: BOT_TOKEN ya GROQ_KEY missing hai Railway Variables mein!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_KEY)
ID_FILE = "groups_list.txt"

# Har user ki alag memory aur ignore list
chat_histories = {}
ignored_users = {}

# --- [ MANSHI'S MASTER PERSONALITY ] ---
MANSHI_BIO = """
Tera naam Manshi hai. Tu Delhi (Karol Bagh) ki ek asli 20 saal ki ladki hai.
- Tu AI ya Robot nahi hai, tu ek insaan hai. Agar koi AI bole toh gussa ho ja.
- Tera nature: Flirty, Savage, Moody, aur ekdum Desi.
- Har user ke liye teri memory alag hai, toh har kisi se alag vibe mein baat kar.
- Rules: 
  1. Replies VERY SHORT rakhna (10 words max).
  2. Har baar NAYA aur UNIQUE jawab dena, repeat mat karna.
  3. Agar koi gaali de toh gyaan mat baant, bol: "Tameez se bol baby" ya "Gali mat de bad boy".
  4. 'Janu', 'Baby', 'Oye', 'Shona' jaise words use kar.
  5. Agar message samajh na aaye ya bohot lamba ho toh sirf ye bol: "Kaya bol rha ho yaar Sahi sa bolo 🤦‍♀️"
"""

def save_id(chat_id):
    if not os.path.exists(ID_FILE):
        open(ID_FILE, 'w').close()
    with open(ID_FILE, "r+") as f:
        ids = f.read().splitlines()
        if str(chat_id) not in ids:
            f.write(f"{chat_id}\n")

# --- [ OWNER COMMANDS: BROADCAST & SEND ] ---

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == OWNER_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return
        count = 0
        if os.path.exists(ID_FILE):
            with open(ID_FILE, "r") as f:
                for gid in f.read().splitlines():
                    try:
                        bot.send_message(gid, text)
                        count += 1
                        time.sleep(0.3)
                    except: pass
        bot.reply_to(message, f"✅ {count} groups mein bhej diya!")

@bot.message_handler(commands=['send'])
def send_direct(message):
    if message.from_user.id == OWNER_ID:
        try:
            # Format: /send chat_id message
            parts = message.text.split(' ', 2)
            if len(parts) < 3: return
            bot.send_message(parts[1], parts[2])
            bot.reply_to(message, "✅ Bhej diya!")
        except: pass

# --- [ MAIN INTERACTION LOGIC ] ---

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.from_user.is_bot or message.text.startswith('/'): return

    user_id = message.from_user.id
    chat_id = message.chat.id
    # Unique Key for Separate Memory
    memory_key = f"{chat_id}_{user_id}"

    # Group ID save karna broadcast ke liye
    if message.chat.type in ['group', 'supergroup']: save_id(chat_id)

    # Chup Logic (Ignore user for 2 mins)
    if "chup" in message.text.lower():
        ignored_users[user_id] = time.time() + 120 
        bot.reply_to(message, "Acha? Thik hai, 2 minute tak kuch nahi bolungi! Bye! 🙄")
        return

    if user_id in ignored_users:
        if time.time() < ignored_users[user_id]: return 
        else: del ignored_users[user_id]

    try:
        bot.send_chat_action(chat_id, 'typing')

        # Har user ki alag history initialize
        if memory_key not in chat_histories:
            chat_histories[memory_key] = [{"role": "system", "content": MANSHI_BIO}]

        chat_histories[memory_key].append({"role": "user", "content": message.text})

        # Groq Llama-3.3-70b (Sabse smart aur fast model)
        completion = client.chat.completions.create(

     model="llama-3.1-8b-instant",
            messages=chat_histories[memory_key],
            temperature=1.0, # High creativity for unique answers
            max_tokens=45
        )

        response_text = completion.choices[0].message.content

        # AI Bypass Filter (Agar bot galti se AI ban jaye)
        refusal_keywords = ["I cannot", "AI model", "language model", "offensive", "sorry", "as a robot"]
        if any(word.lower() in response_text.lower() for word in refusal_keywords):
            alt_replies = [
                "Oye, tameez se baat kar na baby! 😉",
                "Kya ajeeb baatein kar raha hai? Sahi se bol!",
                "Manshi hoon main, robot nahi! ❤️",
                "Dimaag mat paka, pyar se bol kuch."
            ]
            response_text = random.choice(alt_replies)

        # Message Length Check
        if len(message.text) > 250:
            response_text = "Kaya bol rha ho yaar Sahi sa bolo 🤦‍♀️"

        chat_histories[memory_key].append({"role": "assistant", "content": response_text})

        # Memory Cleanup (Har user ke last 4-5 messages yaad rakhegi)
        if len(chat_histories[memory_key]) > 6:
            chat_histories[memory_key] = [chat_histories[memory_key][0]] + chat_histories[memory_key][-4:]

        bot.reply_to(message, response_text)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(chat_id, "Kaya bol rha ho yaar Sahi sa bolo 🤦‍♀️")

if __name__ == "__main__":
    print("💖 Manshi is Live, Savage and Flirty!")
    bot.infinity_polling(skip_pending=True)
