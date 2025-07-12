import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Discord Webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# チェック対象の正式名称の部屋タイプ（部分一致OK）
target_keywords = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァグランドビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム パーシャルビュー",
]

# URL（ホテル一覧）
TARGET_URL = "https://reserve.tokyodisneyresort.jp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# 通知関数
def notify_discord(message):
    data = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print("通知エラー:", e)

# 空室チェック処理
def check_rooms(driver):
    driver.get(TARGET_URL)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rooms = soup.find_all("div", class_="roomList")

    for room in rooms:
        name_elem = room.find("span", class_="roomName")
        status_elems = room.find_all("span", class_="statusMark")

        if not name_elem or not status_elems:
            continue

        room_name = name_elem.get_text(strip=True)
        status_list = [s.get_text(strip=True) for s in status_elems]

        for keyword in target_keywords:
            if keyword in room_name:
                for offset, status in enumerate(status_list):
                    if status in ["○", "1", "2", "3"]:
                        target_date = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
                        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

                        message = f"""【ミラコスタ空室検知】
日付：{target_date}
部屋タイプ：{room_name}
空室状態：{status}
検出時刻：{now}

スマホ：https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search
PC版：https://reserve.tokyodisneyresort.jp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search
"""
                        print(message)
                        notify_discord(message)
                        return  # 1件見つけたら終了

# メイン処理
def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    while True:
        print("巡回中:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            check_rooms(driver)
        except Exception as e:
            print("巡回エラー:", e)
        time.sleep(120)

if __name__ == "__main__":
    main()


