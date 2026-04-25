import discord
from discord.ext import commands, tasks
import feedparser
import os
import asyncio
import threading
import http.server
import socketserver

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

# --- 2. 機器人基礎設定 ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- 3. 監控清單 (請確保 ID 正確且後面有逗號) ---
ACCOUNTS = {
    "Apex 官方推特": {
        "url": "https://rsshub.app/twitter/user/PlayApex",
        "channel": 1488022987046392021,
    }
}


# 紀錄最後發布的連結
last_posts = {name: None for name in ACCOUNTS}

# --- 4. 定時檢查任務 (每 10 分鐘) ---
@tasks.loop(minutes=10)
async def check_updates():
    for name, info in ACCOUNTS.items():
        channel = bot.get_channel(info["channel"])
        if not channel:
            continue
        try:
            feed = feedparser.parse(info["url"])
            if feed.entries:
                latest_link = feed.entries[0].link
                if latest_link != last_posts[name]:
                    await channel.send(f"📢 **{name}** 有新動態！\n{latest_link}")
                    last_posts[name] = latest_link
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Loop 檢查錯誤: {name}, {e}")

# --- 5. 核心：啟動立刻發送一次 ---
@bot.event
async def on_ready():
    print(f'✅ 機器人 {bot.user} 已上線！')
    
    for name, info in ACCOUNTS.items():
                try:
            # 改成 fetch_channel 加上 await，這會強制去 Discord 伺服器抓取頻道
            channel = await bot.fetch_channel(info["channel"])
            
            feed = feedparser.parse(info["url"])
            if feed.entries:
                latest_link = feed.entries[0].link
                last_posts[name] = latest_link
                
                await channel.send(f"🚀 **{name}** 自動監控已啟動！\n目前最新內容：\n{latest_link}")
                print(f"成功發送 {name} 的初始訊息")
        except Exception as e:
            # 如果還是失敗，Logs 會印出到底是「找不到頻道」還是「權限被擋住」
            print(f"啟動時出錯 ({name}): {e}")


    if not check_updates.is_running():
        check_updates.start()

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 延遲：{round(bot.latency * 1000)}ms')

token = os.getenv('DISCORD_TOKEN')
bot.run(token)
