import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

# ✅ Discord Webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ ログイン情報（仮予約時に使用）
LOGIN_EMAIL = "tasuku765@gmail.com"
LOGIN_PASSWORD = "syk3bzdsg"

# ✅ 検出対象の部屋名（正式名称）
target_keywords = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム パーシャルビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァグランドビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ハーバービュー",
]

# ✅ 部屋一覧URL（PC版）
BASE_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# ✅ 通知処理
def notify_discord(message):
    data = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"通知失敗: {e}")

# ✅ 待合室自動突破
def wait_for_waiting_room(driver):
    while "アクセスが集中しています" in driver.page_source:
        print("待合室に滞在中...リロードで待機")
        time.sleep(10)
        driver.refresh()
    print("待合室を突破しました")

# ✅ 仮予約（クレカ手前まで）
def login_and_reserve(driver):
    try:
        print("ログイン処理開始")
        driver.get("https://reserve.tokyodisneyresort.jp/login/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "loginId")))
        driver.find_element(By.ID, "loginId").send_keys(LOGIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LOGIN_PASSWORD)
        driver.find_element(By.CLASS_NAME, "btnLogin").click()

        wait_for_waiting_room(driver)

        driver.get(BASE_URL)
        time.sleep(3)
        try:
            adult_select = Select(driver.find_element(By.NAME, "adultNum"))
            adult_select.select_by_value("2")
        except:
            print("人数選択失敗")

        try:
            driver.find_element(By.CLASS_NAME, "btnNext").click()
            print("仮予約ページへ遷移成功")
            notify_discord("仮予約ページに進みました（クレカ入力前）")
        except:
            print("仮予約ページ遷移失敗")

    except Exception as e:
        print(f"ログインまたは仮予約エラー: {e}")

# ✅ 空室チェック（カレンダービュー）
def check_rooms(driver):
    driver.get(BASE_URL)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "roomList")))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rooms = soup.find_all("div", class_="roomList")

    for room in rooms:
        room_name_elem = room.find("span", class_="roomName")
        status_marks = room.find_all("span", class_="statusMark")

        if not room_name_elem or not status_marks:
            continue

        room_name = room_name_elem.get_text(strip=True)
        status_texts = [s.get_text(strip=True) for s in status_marks]

        for keyword in target_keywords:
            if keyword in room_name:
                for day_offset, status in enumerate(status_texts):
                    if status in ["○", "1", "2", "3"]:
                        stay_date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")

                        msg = (
                            f"日付: {stay_date}\n"
                            f"部屋: {room_name}\n"
                            f"状態: {status}\n"
                            f"検知時刻: {timestamp}\n"
                            f"https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"
                        )
                        print(msg)
                        notify_discord(msg)
                        login_and_reserve(driver)
                        return  # 1件見つけたら終了

# ✅ メイン処理ループ
def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    while True:
        print(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] 空室チェック中…")
        try:
            check_rooms(driver)
        except Exception as e:
            print(f"エラー発生: {e}")
        time.sleep(120)

if __name__ == "__main__":
    main()

