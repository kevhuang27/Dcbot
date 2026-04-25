import discord
from discord.ext import commands, tasks
import feedparser
import os
import asyncio
import threading
import http.server
import socketserver
import requests
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

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
    "Apex 最新消息": {
        # 直接抓新貼文，這是 Reddit 最穩定的路徑
        "url": "https://www.reddit.com/r/apexlegends/new/.rss",
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
            # 強制抓取頻道
            channel = await bot.fetch_channel(info["channel"])
            
            feed = feedparser.parse(info["url"])
            if feed.entries:
                latest_link = feed.entries[0].link
                last_posts[name] = latest_link
                
                # 發送初始訊息
                await channel.send(f"🚀 **{name}** 自動監控已啟動！\n目前最新內容：\n{latest_link}")
                print(f"成功發送 {name} 的初始訊息")
        except Exception as e:
            print(f"啟動時出錯 ({name}): {e}")

    # 啟動循環任務
    if not check_updates.is_running():
        check_updates.start()

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 延遲：{round(bot.latency * 1000)}ms')

token = os.getenv('DISCORD_TOKEN')
@bot.command()
async def check(ctx):
    await ctx.send("🔍 正在嘗試從來源抓取最新消息...")
    for name, info in ACCOUNTS.items():
        try:
            # 1. 強制轉換 ID 並抓取頻道
            target_id = int(info["channel"])
            channel = await bot.fetch_channel(target_id)
            
            # 2. 使用 requests 戴上「瀏覽器面具」去抓取內容
            response = requests.get(info["url"], headers=HEADERS, timeout=10)
            
            # 3. 解析抓下來的內容
            feed = feedparser.parse(response.content)
            
            if feed.entries:
                link = feed.entries[0].link
                title = feed.entries[0].title
                await channel.send(f"✅ 手動抓取成功！\n來源：{name}\n標題：{title}\n內容：{link}")
            else:
                # 如果抓不到，印出 HTTP 狀態碼幫助除錯
                await ctx.send(f"❌ {name} 回傳為空。狀態碼: {response.status_code}")
                
        except Exception as e:
            await ctx.send(f"❌ 抓取失敗，錯誤訊息：{e}")

# 這一行永遠要在最後面
bot.run(token)
