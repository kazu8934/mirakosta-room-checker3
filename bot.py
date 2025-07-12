import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Discord通知用Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ チェック対象の部屋名（正式名称で部分一致OK）
TARGET_ROOMS = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム パーシャルビュー"
]

# ✅ 対象URL（ホテルから探す）
LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"

# ✅ ログイン情報
EMAIL = "tasuku765@gmail.com"
PASSWORD = "syk3bzdsg"

# ✅ Chrome起動設定（ConoHa / Render対応）
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_page_load_timeout(90)

# ✅ Discord通知関数（整形版）
def notify_discord(date, room_name, status, link):
    message = (
        f"【ミラコスタ空室検知】\n"
        f"📅 日付：{date}\n"
        f"🏨 部屋タイプ：\n{room_name}\n"
        f"🛏 空室数：{status}\n"
        f"👉 [予約ページはこちら]({link})"
    )
    requests.post(WEBHOOK_URL, json={"content": message})

# ✅ 空室チェック関数
def check_rooms():
    driver.get(LIST_URL)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    room_blocks = soup.find_all("div", class_="roomList")

    for room_block in room_blocks:
        room_name = room_block.find("p", class_="roomName").text.strip()

        # 対象の部屋名かチェック
        if any(target in room_name for target in TARGET_ROOMS):
            spans = room_block.find_all("span", class_="statusMark")
            days = room_block.find_all("span", class_="dayNum")

            for span, day in zip(spans, days):
                status = span.text.strip()
                date_text = day.text.strip()

                if status in ["○", "1", "2", "3"] and date_text.isdigit():
                    # 日付取得＆リンク作成
                    today = datetime.today()
                    target_day = int(date_text)
                    target_date = today.replace(day=1) + timedelta(days=(target_day - 1))
                    formatted_date = target_date.strftime("%Y-%m-%d")

                    link = "https://reserve.tokyodisneyresort.jp" + room_block.find("a")["href"]

                    # 仮予約ページへ遷移し確認
                    try:
                        driver.get(link)
                        time.sleep(2)

                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "form__agree")))
                        driver.find_element(By.ID, "form__agree").click()
                        driver.find_element(By.CLASS_NAME, "btnSubmit").click()
                        time.sleep(2)

                        driver.find_element(By.ID, "form__login_id").send_keys(EMAIL)
                        driver.find_element(By.ID, "form__password").send_keys(PASSWORD)
                        driver.find_element(By.ID, "loginSubmit").click()
                        time.sleep(5)

                        if "purchase/entry/new" in driver.current_url:
                            notify_discord(formatted_date, room_name, status, driver.current_url)

                    except Exception as e:
                        print(f"[ERROR] 仮予約遷移失敗: {e}")

##################
### 🔁 メインループ ###
##################
while True:
    try:
        check_rooms()
    except Exception as e:
        print(f"[ERROR] メインループ: {e}")
    time.sleep(120)  # ← 2分おきにチェック
