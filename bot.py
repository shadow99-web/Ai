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
bot = commands.Bot(command_prefix="~", intents=intents)

@bot.event
async def on_ready():
    print(f"--------------------------------------------------")
    print(f"✅ BULLETPROOF NAMING BOT ONLINE: {bot.user.name}")
    print(f"--------------------------------------------------")

@bot.event
async def on_message(message):
    # 1. Ignore messages sent by your own bot to avoid loops
    if message.author.id == bot.user.id:
        return
    if message.author.id != 716390085896962058:
        return

    img_url = None
    is_spawn = False

    # 2. Text-Based Detection (Scans main message text)
    msg_content = message.content.lower() if message.content else ""
    if "wild pokémon has appeared" in msg_content or "guess the pokémon" in msg_content:
        is_spawn = True

    # 3. Deep Embed Scanning (Scans titles, descriptions, and author fields)
    if message.embeds:
        for embed in message.embeds:
            embed_title = embed.title.lower() if embed.title else ""
            embed_desc = embed.description.lower() if embed.description else ""
            author_name = embed.author.name.lower() if (embed.author and embed.author.name) else ""
            
            if (
                "wild pokémon has appeared" in embed_title or 
                "wild pokémon has appeared" in embed_desc or
                "wild pokémon has appeared" in author_name or
                "guess the pokémon" in embed_desc
            ) or (embed.description and "#" in embed.description and "catch" in embed_desc):
                is_spawn = True

            # Extract image from Embed Image section
            if embed.image and embed.image.url:
                img_url = embed.image.url
            # Fallback: Extract image from Embed Thumbnail section
            elif embed.thumbnail and embed.thumbnail.url:
                img_url = embed.thumbnail.url

    # 4. Attachment Scanning (Fallback if it's sent as a raw uploaded file)
    if not img_url and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                img_url = attachment.url
                # If a helper bot uploads a wild image, treat it as a spawn target
                if "pokemon" in attachment.filename.lower():
                    is_spawn = True

    # 5. Overriding Check: If it's a direct URL from Poketwo's asset server, it's ALWAYS a spawn
    if img_url and "cdn.poketwo.net/images/" in img_url:
        is_spawn = True

    # 6. Fire the Prediction Execution Loop
    if is_spawn and img_url:
        print(f"🎯 Valid Spawn Match Confirmed! Processing URL: {img_url}")
        
        async with aiohttp.ClientSession() as session:
            payload = {"imageUrl": img_url}
            try:
                async with session.post(API_PREDICT_URL, json=payload, timeout=5.0) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") is True:
                            final_output = data["name"].capitalize()
                            
                            # Deliver the prediction string instantly into the channel
                            await message.channel.send(f" ** <a:24445pokemonball:1519264691795394651> Name:** {final_output}")
                            print(f"✅ Automatically delivered: {final_output}")
                    else:
                        print(f"⚠️ Hugging Face returned error status code: {resp.status}")
            except Exception as e:
                print(f"🛑 Failed to reach AI pipeline: {e}")

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
                        await ctx.send(f" **Model Error:** `{data.get('error')}`")
        except Exception as e:
            await ctx.send(f" **Network Failure:** `{e}`")
            
@bot.command()
async def ping(ctx):
    # 1. Gateway / WebSocket Latency (built into the library)
    gateway_ping = round(bot.latency * 1000)
    
    # 2. API / REST Latency
    start_time = time.perf_counter()
    # Trigger a minor API action (typing status) to see how fast Discord responds
    async with ctx.typing():
        end_time = time.perf_counter()
    api_ping = round((end_time - start_time) * 1000)
    
    # 3. Client / Round-trip Latency
    # Measure how long it takes to send the message and get it back
    start_msg = time.perf_counter()
    message = await ctx.send("🏓 Pinging...")
    end_msg = time.perf_counter()
    client_ping = round((end_msg - start_msg) * 1000)
    
    # Edit the message to show all three latency types
    embed = discord.Embed(title=" **Pong!**", color=discord.Color.blue())
    embed.add_field(name=" **Gateway Latency**", value=f"`{gateway_ping}ms`", inline=False)
    embed.add_field(name=" **API Latency**", value=f"`{api_ping}ms`", inline=False)
    embed.add_field(name=" **Client Latency**", value=f"`{client_ping}ms`", inline=False)
    
    await message.edit(content=None, embed=embed)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ Fatal: OFFICIAL_BOT_TOKEN environment variable is missing!")
    else:
        keep_alive()
        bot.run(BOT_TOKEN)
