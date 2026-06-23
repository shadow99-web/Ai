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
    port = int(os.environ.get("PORT", 10000))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"⚠️ Flask initialization suppressed: {e}")

def keep_alive():
    server_thread = Thread(target=run_flask_server, daemon=True)
    server_thread.start()

# --- ⚙️ DISCORD APPLICATION CONFIGURATION ---
BOT_TOKEN = os.getenv("OFFICIAL_BOT_TOKEN")
API_PREDICT_URL = "https://discordbotnhihun-naming.hf.space/predict"

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--------------------------------------------------")
    print(f"✅ Official Application Online: {bot.user.name}")
    print(f"--------------------------------------------------")

@bot.event
async def on_message(message):
    # 1. Ignore messages sent by your own bot to prevent processing loops
    if message.author.id == bot.user.id:
        return

    # 2. Check if the message contains any embeds
    if message.embeds:
        for embed in message.embeds:
            img_url = embed.image.url if embed.image else None
            
            # 3. CRITICAL: Check if the image belongs to Pokétwo's asset server
            # This triggers the AI no matter who or what sent/forwarded the embed!
            if img_url and "cdn.poketwo.net/images/" in img_url:
                print(f"🎯 Valid Pokétwo asset signature matched: {img_url}")
                print(f"📡 Querying Hugging Face Space...")
                
                async with aiohttp.ClientSession() as session:
                    payload = {"imageUrl": img_url}
                    try:
                        async with session.post(API_PREDICT_URL, json=payload, timeout=5.0) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if data.get("status") is True:
                                    final_output = data["name"].capitalize()
                                    
                                    # 4. Post the target prediction right into the active channel
                                    await message.channel.send(f"📊 **AI Identification:** That looks like a **{final_output}**")
                                    print(f"✅ Prediction delivered: {final_output}")
                                    return # Stop looping through embeds once handled
                    except Exception as e:
                        print(f"🛑 Error connecting to Space: {e}")

    # Process manually typed utility commands (like !test)
    await bot.process_commands(message)

# --- 🧪 MANUAL TESTING COMMAND ---
@bot.command(name="test")
async def test_api(ctx, url: str = None):
    """Manually test the AI prediction pipeline with a custom image URL."""
    if not url:
        await ctx.send("❌ **Usage:** `!test <image_url>`")
        return

    await ctx.send("⏳ **Processing request...** Contacting Hugging Face Space.")
    async with aiohttp.ClientSession() as session:
        payload = {"imageUrl": url}
        try:
            async with session.post(API_PREDICT_URL, json=payload, timeout=6.0) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") is True:
                        name = data["name"].capitalize()
                        confidence = data["confidence"]
                        
                        embed = discord.Embed(title="🧪 AI Diagnostic Test Success", color=discord.Color.green())
                        embed.add_field(name="Predicted Species", value=f"**{name}**", inline=False)
                        embed.add_field(name="Model Confidence", value=confidence, inline=False)
                        embed.set_thumbnail(url=url)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"⚠️ **Model Error:** `{data.get('error')}`")
        except Exception as e:
            await ctx.send(f"🛑 **Network Failure:** `{e}`")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ Fatal: OFFICIAL_BOT_TOKEN environment variable is missing!")
    else:
        keep_alive()
        bot.run(BOT_TOKEN)
