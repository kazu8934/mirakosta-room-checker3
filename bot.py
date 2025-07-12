import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Discord通知用Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ チェック対象のURL（ホテルから探すルート）
LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# ✅ 対象部屋（正式名称ベースでフィルタ）
target_rooms = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム パーシャルビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァグランドビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ハーバービュー",
]

# ✅ 通知送信関数
def notify_discord(date, room_name, status, link):
    message = (
        f"【ミラコスタ空室検知】\n"
        f"日付：{date}\n"
        f"部屋タイプ：\n{room_name}\n"
        f"空室数：{status}\n"
        f"[予約ページを開く]({link})"
    )
    requests.post(WEBHOOK_URL, json={"content": message})

# ✅ 空室チェック処理
def check_rooms():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(LIST_URL)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    rooms = soup.find_all("div", class_="planListItem")

    for room in rooms:
        room_name_tag = room.find("div", class_="roomType")
        if not room_name_tag:
            continue
        room_name = room_name_tag.get_text(strip=True)

        # ✅ 対象部屋かどうか
        if not any(target in room_name for target in target_rooms):
            continue

        # ✅ カレンダービューがあるか確認
        calendar = room.find("div", class_="statusMarkArea")
        if not calendar:
            continue

        status_marks = calendar.find_all("span", class_="statusMark")
        date_texts = calendar.find_all("span", class_="date")

        for i, status in enumerate(status_marks):
            mark = status.get_text(strip=True)

            # ✅ 通知対象（○・1〜3・または金額表示）
            if mark == "○" or mark in ["1", "2", "3"] or mark.startswith("¥"):
                try:
                    date_text = date_texts[i].get_text(strip=True)
                    notify_discord(date_text, room_name, mark, LIST_URL)
                except IndexError:
                    continue

    driver.quit()

# ✅ メインループ（2分おきに実行）
while True:
    try:
        check_rooms()
    except Exception as e:
        print(f"[ERROR] メインループ：{e}")
    time.sleep(120)  # 2分おき
