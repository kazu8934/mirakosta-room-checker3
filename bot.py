import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ✅ Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ 対象部屋コード
TARGET_ROOM_CODES = [
    "HODHMTGD0004N", "HODHMTKD0004N", "HODHMBKT0004N"
]

# ✅ 通知関数
def notify_discord(room_name, status_text, detected_date):
    detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"🟢 **空室検知**\n"
        f"**部屋名:** {room_name}\n"
        f"**空室状況:** {status_text}\n"
        f"**空室日付:** {detected_date}\n"
        f"**検知日時:** {detection_time}\n"
        f"👉 [ここから予約](https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search)"
    )
    requests.post(WEBHOOK_URL, json={"content": message})

# ✅ Seleniumセットアップ
def create_driver():
    options = Options()
    options.binary_location = "/usr/bin/chromium"  # ✅ Chromium固定
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    return webdriver.Chrome(options=options)

# ✅ 待合室突破関数
def wait_in_queue(driver):
    while "reserve-q.tokyodisneyresort.jp" in driver.current_url:
        requests.post(WEBHOOK_URL, json={"content": "⏳ 待合室中…リロード待機中"})
        time.sleep(30)
        driver.refresh()

# ✅ ログイン処理
def login(driver):
    driver.get("https://reserve.tokyodisneyresort.jp/login/")
    wait_in_queue(driver)
    driver.find_element(By.ID, "loginId").send_keys("tasuku765@gmail.com")
    driver.find_element(By.ID, "loginPass").send_keys("syk3bzdsg")
    driver.find_element(By.ID, "loginSubmit").click()
    wait_in_queue(driver)

# ✅ 仮予約処理
def start_reservation(driver):
    login(driver)
    driver.get("https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search")
    wait_in_queue(driver)
    requests.post(WEBHOOK_URL, json={"content": "🚨 仮予約ページまで進みました（クレカ入力手前）"})

# ✅ メインループ
def main_loop():
    print("Bot起動中。巡回を開始します。")
    driver = create_driver()
    try:
        login(driver)
        while True:
            driver.get("https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search")
            wait_in_queue(driver)

            elements = driver.find_elements(By.CLASS_NAME, "roomName")
            statuses = driver.find_elements(By.CLASS_NAME, "statusMark")

            for room, status in zip(elements, statuses):
                room_name = room.text.strip()
                status_text = status.text.strip()
                room_code = room.get_attribute("data-roomcode")
                detected_date = datetime.now().strftime("%Y-%m-%d")

                if room_code in TARGET_ROOM_CODES and (status_text in ["○", "1", "2", "3"] or "¥" in status_text):
                    notify_discord(room_name, status_text, detected_date)
                    start_reservation(driver)

            time.sleep(120)

    finally:
        driver.quit()

if __name__ == "__main__":
    main_loop()