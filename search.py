import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
import os
import asyncio
from aiohttp import web

# Variabile de mediu
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
PORT = int(os.getenv("PORT", 10000))  # Render setează $PORT automat

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True  # necesar pentru a citi comenzile

bot = commands.Bot(command_prefix="!", intents=intents)

FILE_NAME = "stilimobil_urls.txt"

def scrape_stilimobil():
    """Returnează linkurile noi de pe stilimobil.ro"""
    announcement_urls = set()
    page = 1

    while True:
        url = f"https://www.stilimobil.ro/apartamente-de-vanzare/iasi/?page={page}&&rooms=2&price_max=100000&floor_min=1&floor_max=3"
        print(f"🔎 Procesez pagina {page} -> {url}")

        response = requests.get(url, allow_redirects=True)
        if response.status_code != 200:
            print("❌ Eroare la accesarea paginii.")
            break

        if response.url == "https://www.stilimobil.ro/apartamente-de-vanzare/iasi/":
            print("✅ Am ajuns la final (redirect detectat).")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)
        page_links = []

        for link in links:
            href = link["href"]
            if "/apartament-2-camere-de-vanzare" in href:
                if href.startswith("/"):
                    href = "https://www.stilimobil.ro" + href
                href = href.split('#')[0]
                href = href.split('?')[0]

                announcement_urls.add(href)
                page_links.append(href)

        if not page_links:
            print("✅ Niciun anunț pe această pagină, mă opresc.")
            break

        page += 1

    # Comparare cu fișierul anterior
    previous_urls = set()
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            for line in f:
                previous_urls.add(line.strip())

    new_urls = announcement_urls - previous_urls

    # Salvare URL-uri în fișier
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        for url in sorted(announcement_urls):
            f.write(url + "\n")

    return sorted(new_urls)  # întoarce doar anunțurile noi


@tasks.loop(hours=24)
async def daily_scrape():
    """Rulează o dată la 24h și trimite linkuri noi în canal."""
    new_links = scrape_stilimobil()

    if not new_links:
        print("ℹ️ Nu au apărut anunțuri noi.")
        return

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
    except discord.DiscordException as e:
        print(f"❌ Eroare la fetch_channel: {e}")
        return

    for link in new_links:
        await channel.send(link)
        print(f"✨ Trimis link: {link}")


@bot.command(name="imobiliare")
async def manual_scrape(ctx):
    """Rulează scraping-ul manual când tastezi !imobiliare"""
    await ctx.send("🔎 Caut anunțuri noi pe stilimobil.ro...")
    new_links = scrape_stilimobil()

    if not new_links:
        await ctx.send("ℹ️ Nu am găsit anunțuri noi.")
        return

    for link in new_links:
        await ctx.send(link)
        print(f"✨ Trimis link manual: {link}")


@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    daily_scrape.start()  # pornește task-ul zilnic


# -----------------------
# Web server dummy pentru Render
# -----------------------
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_webserver():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌍 Web server pornit pe port {PORT}")


# -----------------------
# Pornire bot + server
# -----------------------
if TOKEN:
    loop = asyncio.get_event_loop()
    loop.create_task(start_webserver())  # pornește webserverul
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN nu este setat în variabilele de mediu.")
