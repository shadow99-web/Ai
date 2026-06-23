import discord
from discord.ext import commands
import aiohttp
import os
from flask import Flask
from threading import Thread

# --- 🌐 WEB SERVER GATEWAY FOR RENDER FREE TIER ---
app = Flask('')

@app.route('/')
def home():
    return "Official NAMING Bot is active and healthy!"

def run_flask_server():
    # Render automatically sets the PORT environment variable.
    # If not present, it defaults to 10000.
    port = int(os.environ.get("PORT", 10000))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"⚠️ Flask initialization suppressed: {e}")

def keep_alive():
    # Run the web server in a separate background thread so it doesn't block the Discord client
    server_thread = Thread(target=run_flask_server, daemon=True)
    server_thread.start()

# --- ⚙️ DISCORD APPLICATION CONFIGURATION ---
BOT_TOKEN = os.getenv("OFFICIAL_BOT_TOKEN")
TARGET_BOT_ID = 716390085896962058  # Pokétwo's official User ID
API_PREDICT_URL = "https://discordbotnhihun-naming.hf.space/predict"

intents = discord.Intents.default()
intents.message_content = True  # Required to read embed details
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--------------------------------------------------")
    print(f"✅ Official Application Online: {bot.user.name}")
    print(f"--------------------------------------------------")

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return

    if message.author.id == TARGET_BOT_ID:
        low_content = message.content.lower()
        
        if "wild pokémon has appeared" in low_content:
            if message.embeds:
                embed = message.embeds[0]
                img_url = embed.image.url if embed.image else None
                
                if img_url:
                    print(f"👁️ Spawn detected! Querying Hugging Face ONNX Space...")
                    async with aiohttp.ClientSession() as session:
                        payload = {"imageUrl": img_url}
                        try:
                            async with session.post(API_PREDICT_URL, json=payload, timeout=5.0) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    if data.get("status") is True:
                                        final_output = data["name"].capitalize()
                                        await message.channel.send(f"📊 **AI Identification:** That looks like a **{final_output}**")
                        except Exception as e:
                            print(f"🛑 Error connecting to Space: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ Fatal: OFFICIAL_BOT_TOKEN environment variable is missing!")
    else:
        # Start the web server listener first to pass Render's boot check
        keep_alive()
        # Launch the Discord application gateway
        bot.run(BOT_TOKEN)

