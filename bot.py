import discord
from discord.ext import commands, tasks
import feedparser
import os
import asyncio
import http.server
import socketserver
import threading

# --- 1. 防休眠設定 ---
def keep_alive():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")
    with socketserver.TCPServer(("", 10000), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# --- 2. 機器人設定 ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 這裡填入你想接收訊息的頻道 ID (在 Discord 頻道按右鍵點「複製頻道 ID」)
TARGET_CHANNEL_ID = 123456789012345678  # <--- 請換成你的頻道 ID

# 想追蹤的推特 RSS 連結 (這裡以 ZUTOMAYO 為例)
# 使用 RSSHub 的公共伺服器 (若失效可換其他的)
TWITTER_RSS_URL = "https://rsshub.app/twitter/user/zutomayo"

last_post_link = None  # 用來記錄最後一則發過的貼文，避免重複發送

@tasks.loop(minutes=10)
async def check_twitter():
    global last_post_link
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        return

    try:
        # 抓取 RSS 資料
        feed = feedparser.parse(TWITTER_RSS_URL)
        if feed.entries:
            latest_post = feed.entries[0]
            link = latest_post.link

            # 如果這則貼文還沒發過
            if link != last_post_link:
                last_post_link = link
                await channel.send(f"📢 **ZUTOMAYO 推特更新囉！**\n{link}")
                print(f"成功推送：{link}")
    except Exception as e:
        print(f"檢查推特時發生錯誤: {e}")

@bot.event
async def on_ready():
    print(f'✅ 機器人 {bot.user} 已上線，開始監控推特...')
    check_twitter.start() # 啟動循環任務

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 延遲：{round(bot.latency * 1000)}ms')

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
