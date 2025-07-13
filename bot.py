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

# ディズニーアカウント情報
EMAIL = "tasuku765@gmail.com"
PASSWORD = "syk3bzdsg"

# Discord通知先Webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# チェック対象ページ
LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# 対象部屋とhotelRoomCdの辞書（画像に基づく最新版）
target_rooms = {
    "テラスグランドハーバービュー": "HODHMTGD0004N",
    "テラスハーバービュー": "HODHMTKD0004N",
    "テラスピアッツァビュー": "HODHMTOD0004N",
    "テラスベネツィア": "HODHMTVD0005N",
    "バルコニーハーバービュー": "HODHMBKT0004N",
    "バルコニーハーバー4名": "HODHMBKQ0004N",
    "バルコニーピアッツァビュー": "HODHMBOQ0004N",
    "ハーバールームハーバービュー": "HODHMHKQ0005N",
    "ハーバールームピアッツァ": "HODHMHOW0005N",
    "スーペリアルームハーバービュー": "HODHMIKT0006N",
    "スーペリアルームハーバー4名": "HODHMIKQ0006N",
    "ポルト・パラディーゾ・サイド スーペリアルームハーバービュー": "HODHMKTT0005N",
    "ポルト・パラディーゾ・サイド スーペリアルームハーバービュー4名": "HODHMKQT0005N"
}

# 通知関数
def notify_discord(date, room_name, status):
    use_date = datetime.strptime(date, "%Y/%m/%d").strftime("%Y-%m-%d")
    hotel_room_cd = target_rooms.get(room_name)
    if not hotel_room_cd:
        return
    reserve_link = (
        f"https://reserve.tokyodisneyresort.jp/sp/hotel/list/?"
        f"showWay=&roomsNum=1&adultNum=2&childNum=0&stayingDays=1"
        f"&useDate={use_date}&searchHotelCD=DHM&hotelRoomCd={hotel_room_cd}&displayType=calendar"
    )
    message = (
        f"【ミラコスタ空室検知】\n"
        f"部屋：{room_name}\n"
        f"日付：{date}\n"
        f"空室状況：{status}\n"
        f"[\u25B6 予約ページを開く]({reserve_link})"
    )
    requests.post(WEBHOOK_URL, json={"content": message})

# 仮予約処理（任意）
def go_to_reservation(driver, reserve_link):
    try:
        driver.get("https://reserve.tokyodisneyresort.jp/login/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "form_login_id")))

        driver.find_element(By.ID, "form_login_id").send_keys(EMAIL)
        driver.find_element(By.ID, "form_login_pass").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginSubmit").click()
        time.sleep(5)

        try:
            agree_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnAgree"))
            )
            agree_button.click()
        except:
            pass

        driver.get(reserve_link)
        time.sleep(3)

        try:
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnNext"))
            )
            next_btn.click()
            time.sleep(2)
        except:
            print("次へボタンなし")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "adultNum")))
        driver.find_element(By.ID, "adultNum").send_keys("2")
        driver.find_element(By.CLASS_NAME, "btnNext").click()
        time.sleep(5)

        print("[OK] 仮予約画面に到達しました")

    except Exception as e:
        print(f"[ERROR] 仮予約処理エラー: {e}")

# 空室チェック
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

        if room_name not in target_rooms:
            continue

        calendar = room.find("div", class_="statusMarkArea")
        if not calendar:
            continue

        marks = calendar.find_all("span", class_="statusMark")
        dates = calendar.find_all("span", class_="date")

        for i, mark in enumerate(marks):
            status = mark.get_text(strip=True)
            if status in ["○", "1", "2", "3"] or status.startswith("\u00a5"):
                try:
                    date_text = dates[i].get_text(strip=True)
                    notify_discord(date_text, room_name, status)
                except IndexError:
                    continue

    driver.quit()

# メインループ
while True:
    try:
        check_rooms()
    except Exception as e:
        print(f"[ERROR] メインループ: {e}")
    time.sleep(120)
