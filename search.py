import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Nume fișier pentru a salva link-urile
file_name = "stilimobil_urls.txt"

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
if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            previous_urls.add(line.strip())

new_urls = announcement_urls - previous_urls

# Salvare URL-uri în fișier
with open(file_name, "w", encoding="utf-8") as f:
    for url in sorted(announcement_urls):
        f.write(url + "\n")

# Afișare raport
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\n📅 Data și ora rulării: {now}")
print(f"🏠 Număr total de apartamente găsite: {len(announcement_urls)}")
if new_urls:
    print(f"✨ Au apărut {len(new_urls)} anunțuri noi:")
    for url in sorted(new_urls):
        print(url)
else:
    print("ℹ️ Nu au apărut anunțuri noi față de ultima rulare.")
