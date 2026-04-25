import discord
from discord.ext import commands, tasks
import feedparser
import os
import asyncio
import threading
import http.server
import socketserver

# --- 1. 防休眠設定 (Render 24小時在線專用) ---
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

# --- 3. 【全能監控分流清單】 ---
# 請在此修改網址與對應的頻道 ID
# 提示：ID 請長按 Discord 頻道名稱後點選「複製頻道 ID」
ACCOUNTS = {
    "APEX 官方推特": {
        "url": "https://x.com/playapex?s=21&t=-czGc9vt-apy4yCbiz_O6Q",
        "channel": 1488022987046392021  # <--- 修改為頻道 A 的 ID
    },
    "ACAね 個人推特": {
        "url": "https://rsshub.app/twitter/user/ACAne_04",
        "channel":   # <--- 修改為頻道 B 的 ID
    },
    "ZUTOMAYO YT頻道": {
        "url": "https://rsshub.app/youtube/channel/UCvSVRNqBWQDnl3_L66L9_FA",
        "channel":   # <--- 修改為頻道 C 的 ID
    },
    "絕區零 B站動態": {
        "url": "https://rsshub.app/bilibili/user/dynamic/1636034895",
        "channel":   # <--- 修改為頻道 D 的 ID
    }
}

# 紀錄最後發布的連結，防止重複
last_posts = {name: None for name in ACCOUNTS}

@tasks.loop(minutes=10)
async def check_updates():
    for name, info in ACCOUNTS.items():
        channel = bot.get_channel(info["channel"])
        if not channel:
            continue

        try:
            feed = feedparser.parse(info["url"])
            if feed.entries:
                # 取得最新的一則內容
                latest_link = feed.entries[0].link
                
                # 如果與上次紀錄不同，就發送新訊息
                if latest_link != last_posts[name]:
                    if last_posts[name] is not None:
                        await channel.send(f"📢 **{name}** 更新囉！\n{latest_link}")
                    last_posts[name] = latest_link
            
            await asyncio.sleep(3) # 避免請求過快
        except Exception as e:
            print(f"❌ 檢查 {name} 時出錯: {e}")

@bot.event
async def on_ready():
    print(f'✅ 機器人 {bot.user} 已啟動，開始分流監控！')
    
    # 【啟動測試】一上線立刻在各頻道報到，確認 ID 是否填寫正確
    for name, info in ACCOUNTS.items():
        channel = bot.get_channel(info["channel"])
        if channel:
            try:
                feed = feedparser.parse(info["url"])
                if feed.entries:
                    last_posts[name] = feed.entries[0].link
                    await channel.send(f"✅ **{name}** 監控系統已就緒！\n目前最新內容：{last_posts[name]}")
            except Exception as e:
                print(f"啟動測試失敗: {name}, {e}")

    if not check_updates.is_running():
        check_updates.start()

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 延遲：{round(bot.latency * 1000)}ms')

# 讀取 Token
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
