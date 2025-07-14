import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller  # ✅ 自動インストール用

# ✅ 自動でChromeDriverインストール
chromedriver_autoinstaller.install()

# ✅ Discord通知用Webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ チェック対象URL
LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# ✅ 対象部屋
target_rooms = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー",
]

# ✅ Discord通知
def notify_discord(date, room_name, status):
    message = (
        f"【ミラコスタ空室検知】\n"
        f"日付：{date}\n"
        f"部屋タイプ：{room_name}\n"
        f"空室状態：{status}\n"
        f"👉 [予約ページ](https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search)"
    )
    requests.post(WEBHOOK_URL, json={"content": message})

# ✅ 空室チェック
def check_rooms():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
    options.binary_location = '/usr/bin/chromium-browser'

    driver = webdriver.Chrome(options=options)

    driver.get(LIST_URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rooms = soup.find_all("div", class_="planListItem")

    for room in rooms:
        name_tag = room.find("div", class_="roomType")
        if not name_tag:
            continue

        room_name = name_tag.get_text(strip=True)
        if room_name not in target_rooms:
            continue

        calendar = room.find("div", class_="statusMarkArea")
        if not calendar:
            continue

        marks = calendar.find_all("span", class_="statusMark")
        dates = calendar.find_all("span", class_="date")

        for i, mark in enumerate(marks):
            status = mark.get_text(strip=True)
            if status in ["○", "1", "2", "3"] or status.startswith("¥"):
                try:
                    date_text = dates[i].get_text(strip=True)
                    notify_discord(date_text, room_name, status)
                except IndexError:
                    continue

    driver.quit()

# ✅ メインループ
while True:
    try:
        print(f"[CHECK] {datetime.now()} | Start checking rooms...")
        check_rooms()
    except Exception as e:
        print(f"[ERROR] {datetime.now()} | Main loop error: {e}")

    time.sleep(120)
