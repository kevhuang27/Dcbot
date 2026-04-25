import discord
from discord.ext import commands, tasks
import feedparser
import os
import http.server
import socketserver
import threading

# --- 防休眠設定 ---
def keep_alive():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")
    with socketserver.TCPServer(("", 10000), Handler) as httpd:
        httpd.serve_forever()
threading.Thread(target=keep_alive, daemon=True).start()

# --- 機器人設定 ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 這裡填入你的頻道 ID
TARGET_CHANNEL_ID = 1488022986265989252

@bot.event
async def on_ready():
    print(f'✅ {bot.user} 已上線！')
    if not check_twitter.is_running():
        check_twitter.start()

@bot.command()
async def hello(ctx):
    await ctx.send('你好！我是你的 Discord 助手。')

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 延遲：{round(bot.latency * 1000)}ms')

@tasks.loop(minutes=10)
async def check_twitter():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel: return
    try:
        # 以 ZUTOMAYO 為例
        feed = feedparser.parse("https://rsshub.app/twitter/user/zutomayo")
        if feed.entries:
            await channel.send(f"📢 **推特更新囉！**\n{feed.entries[0].link}")
    except Exception as e:
        print(f"Error: {e}")

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
