import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# チェック対象URL
LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# 対象部屋とhotelRoomCdの辞書
target_rooms = {
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー": "HODHMTGD0004N",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー": "HODHMTKD0004N",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー": "HODHMBKT0004N",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー": "HODHMBOQ0004N",
}

# Discord通知
def notify_discord(date, room_name, status):
    use_date = datetime.strptime(date, "%Y/%m/%d").strftime("%Y%m%d")
    hotel_room_cd = target_rooms.get(room_name)
    if not hotel_room_cd:
        return

    reserve_link = (
        f"https://reserve.tokyodisneyresort.jp/hotel/list/?"
        f"showWay=&roomsNum=1&adultNum=2&childNum=0&stayingDays=1"
        f"&useDate={use_date}&searchHotelCD=DHM&hotelRoomCd={hotel_room_cd}"
        f"&displayType=data-hotel&reservationStatus=1"
    )

    message = (
        f"【ミラコスタ空室検知】\n\n"
        f"Date: {date}\n"
        f"Room: {room_name}\n"
        f"Status: {status}\n\n"
        f"👉 {reserve_link}"
    )

    requests.post(WEBHOOK_URL, json={"content": message})
    print(f"[NOTIFY] {datetime.now()} | {room_name} {date} Status: {status}")

# 空室チェック
def check_rooms():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
    options.binary_location = '/usr/bin/chromium'  # ★ VPS専用追加

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    while True:
        driver.get(LIST_URL)
        time.sleep(5)

        if "ただいまサイトが混雑しております" in driver.page_source:
            print(f"[WAIT ROOM] {datetime.now()} | Waiting 10 sec...")
            time.sleep(10)
            continue
        else:
            break

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

                    # 日付フィルタ
                    target_date = datetime.strptime(date_text, "%Y/%m/%d")
                    today = datetime.today()
                    four_months_later = today + timedelta(days=120)
                    if not (today < target_date <= four_months_later):
                        continue

                    notify_discord(date_text, room_name, status)

                except IndexError:
                    continue

    driver.quit()

# メインループ
while True:
    try:
        print(f"[CHECK] {datetime.now()} | Start checking rooms...")
        check_rooms()
    except Exception as e:
        print(f"[ERROR] {datetime.now()} | Main loop error: {e}")
    time.sleep(120)

