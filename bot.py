import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Discord通知用Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ チェック対象の正式部屋名称（完全一致）
target_rooms = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム パーシャルビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ハーバービュー"
]

# ✅ Discord通知関数
def notify_discord(date_str, room_name, status):
    message = (
        f"【ミラコスタ空室検知】\n"
        f"日付：{date_str}\n"
        f"部屋タイプ：{room_name}\n"
        f"空室状態：{status}\n"
        f"[👉 予約ページはこちら](https://reserve.tokyodisneyresort.jp/sp/hotel/list/)"
    )
    try:
        requests.post(WEBHOOK_URL, json={"content": message})
        print(f"✅ 通知済：{room_name} {date_str} {status}")
    except Exception as e:
        print(f"❌ 通知失敗: {e}")

# ✅ 空室チェック本体
def check_calendar_status():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?showWay=&roomsNum=&adultNum=2&childNum=&stayingDays=1&useDate=&cpListStr=&childAgeBedInform=&searchHotelCD=DHM&hotelSearchDetail=true&detailOpenFlg=0&displayType=hotel-search&reservationStatus=1"
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "roomList")))

    rooms = driver.find_elements(By.CLASS_NAME, "roomList")
    today = datetime.now()

    for room in rooms:
        try:
            room_name = room.find_element(By.CLASS_NAME, "roomName").text.strip()
            if any(room_name == target for target in target_rooms):
                status_elems = room.find_elements(By.CLASS_NAME, "statusMark")
                for offset, elem in enumerate(status_elems):
                    status = elem.text.strip()
                    if status in ["○", "1", "2", "3"]:
                        date_str = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
                        notify_discord(date_str, room_name, status)
        except Exception as e:
            print(f"⚠️ 部屋情報の取得失敗: {e}")

    driver.quit()

# ✅ 実行
if __name__ == "__main__":
    while True:
        print("▶ ミラコスタ空室チェック開始")
        try:
            check_calendar_status()
        except Exception as e:
            print(f"❌ 実行時エラー: {e}")
        time.sleep(120)

