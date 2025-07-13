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

# ✅ あなたのディズニーアカウント
EMAIL = "tasuku765@gmail.com"
PASSWORD = "syk3bzdsg"

# ✅ Discord通知用Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ チェック対象URL（ホテルから探す）
LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# ✅ 対象部屋の正式名称リスト
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

# ✅ 通知履歴（重複防止）
notified_set = set()

# ✅ Discord通知関数（リンク付き）
def notify_discord(date, room_name, status, reserve_link):
    message = (
        f"【ミラコスタ空室検知】\n"
        f"日付：{date}\n"
        f"部屋タイプ：{room_name}\n"
        f"空室状態：{status}\n"
        f"[予約ページを開く]({reserve_link})"
    )
    requests.post(WEBHOOK_URL, json={"content": message})

# ✅ 仮予約ページへ自動遷移
def go_to_reservation(driver, reserve_link):
    try:
        driver.get("https://reserve.tokyodisneyresort.jp/login/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "form_login_id")))
        driver.find_element(By.ID, "form_login_id").send_keys(EMAIL)
        driver.find_element(By.ID, "form_login_pass").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginSubmit").click()
        time.sleep(5)

        # 同意ボタン
        try:
            agree_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnAgree"))
            )
            agree_button.click()
        except:
            pass

        # 対象の部屋リンクへ
        driver.get(reserve_link)
        time.sleep(3)

        # 「次へ」があれば押す
        try:
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnNext"))
            )
            next_btn.click()
            time.sleep(2)
        except:
            print("次へボタンなし")

        # 人数選択（大人2人）
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "adultNum")))
        driver.find_element(By.ID, "adultNum").send_keys("2")
        driver.find_element(By.CLASS_NAME, "btnNext").click()
        time.sleep(5)

        print("[OK] 仮予約画面に到達しました")
    except Exception as e:
        print(f"[ERROR] 仮予約処理エラー: {e}")

# ✅ 空室チェック関数
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
        name_tag = room.find("div", class_="roomType")
        if not name_tag:
            continue
        room_name = name_tag.get_text(strip=True)

        if not any(name in room_name for name in target_rooms):
            continue

        calendar = room.find("div", class_="statusMarkArea")
        if not calendar:
            continue

        marks = calendar.find_all("span", class_="statusMark")
        dates = calendar.find_all("span", class_="date")
        link_tag = room.find("a", class_="planDetailBtn")
        if not link_tag:
            continue
        reserve_link = "https://reserve.tokyodisneyresort.jp" + link_tag["href"]

        for i, mark in enumerate(marks):
            status = mark.get_text(strip=True)
            if status in ["○", "1", "2", "3"] or status.startswith("¥"):
                try:
                    date_text = dates[i].get_text(strip=True)
                    key = f"{date_text}_{room_name}_{status}"
                    if key not in notified_set:
                        notify_discord(date_text, room_name, status, reserve_link)
                        go_to_reservation(driver, reserve_link)
                        notified_set.add(key)
                except IndexError:
                    continue

    driver.quit()

# ✅ メインループ（2分おき）
while True:
    try:
        check_rooms()
    except Exception as e:
        print(f"[ERROR] メインループ: {e}")
    time.sleep(120)
