import requests
import sqlite3
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load environment variables from .env file
load_dotenv()

# init
def check_version():
    required = [line.strip() for line in open('requirements.txt')]

    for package in required:
        package_name, package_version = package.split('==')
        name, version = pkg_resources.get_distribution(package_name).project_name, pkg_resources.get_distribution(package_name).version
        if package != f'{name}=={version}':
            raise ValueError(f'{name} version {version} is installed but does not match the requirements')


# Accessing variables
discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")

# Use these variables in your application
print("Bot Token:", discord_bot_token)

# 資料庫連接與建立
conn = sqlite3.connect("earthquakes.db")
c = conn.cursor()
c.execute(
    """
    CREATE TABLE IF NOT EXISTS sent_earthquakes (
        report_content TEXT PRIMARY KEY
    )
"""
)
conn.commit()

async def broadcast_message(bot, message):
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                await channel.send(message)
            except Exception as e:
                print(f"Failed to send message to {channel.name} in {guild.name}: {e}")

# 檢查並發送地震報告
async def check_and_send_earthquakes():
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization=你的授權碼"
    response = requests.get(url)
    data = response.json()

    earthquake = data["records"]["Earthquake"][0]
    report_content = earthquake["ReportContent"]
    c.execute(
        "SELECT * FROM sent_earthquakes WHERE report_content = ?",
        (report_content,),
    )
    if c.fetchone() is None:
        # 地震未被報告，發送到 Discord
        message = f"爾伯地震報告：{report_content}"
        await broadcast_message(bot, "您要發送的消息")
        # channel = bot.get_channel('yourChannel')
        await channel.send(message)
        # 將地震報告內容記錄到資料庫
        c.execute(
            "INSERT INTO sent_earthquakes (report_content) VALUES (?)",
            (report_content,),
        )
        conn.commit()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await broadcast_message(bot, f"online")
    check_earthquakes.start()

@tasks.loop(seconds=2)
async def check_earthquakes():
    await check_and_send_earthquakes()

bot.run(discord_bot_token)