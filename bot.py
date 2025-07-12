import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Discord Webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1390577349489328179/t_7-as4-tdDVt0QddU7g9qVDeZEHY1eWzOcicIX4zWJD0MRtFOIoBL2czjxJFEO_X_Gg"

# ✅ ログイン情報
LOGIN_EMAIL = "tasuku765@gmail.com"
LOGIN_PASSWORD = "syk3bzdsg"

# ✅ 対象部屋名
target_keywords = [
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバービュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド テラスルーム ハーバーグランドビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ピアッツァビュー",
    "スペチアーレ・ルーム＆スイート ポルト・パラディーゾ・サイド バルコニールーム ハーバービュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム パーシャルビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ピアッツァグランドビュー",
    "ポルト・パラディーゾ・サイド スーペリアルーム ハーバービュー"
]

LIST_URL = "https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"


def notify_discord(message):
    data = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"通知失敗: {e}")


def login(driver):
    driver.get("https://reserve.tokyodisneyresort.jp/login/")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "loginId")))
    driver.find_element(By.ID, "loginId").send_keys(LOGIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LOGIN_PASSWORD)
    driver.find_element(By.CLASS_NAME, "btnLogin").click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "headerLogo")))


def check_calendar_and_reserve(driver):
    driver.get(LIST_URL)
    time.sleep(3)
    room_links = driver.find_elements(By.XPATH, "//div[contains(@class, 'roomList')]/div[@class='roomInfo']/div[@class='roomName']/a")

    for link in room_links:
        room_name = link.text.strip()
        if any(keyword in room_name for keyword in target_keywords):
            print(f"対象の部屋発見: {room_name}")
            try:
                link.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "statusMark")))
                soup = BeautifulSoup(driver.page_source, "html.parser")
                status_marks = soup.find_all("span", class_="statusMark")
                for day_offset, status in enumerate(status_marks):
                    status_text = status.get_text(strip=True)
                    if status_text in ["○", "1", "2", "3"]:
                        stay_date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                        msg = (
                            f"日付: {stay_date}\n"
                            f"部屋: {room_name}\n"
                            f"状態: {status_text}\n"
                            f"確認時刻: {datetime.now().strftime('%Y/%m/%d %H:%M')}\n"
                            f"https://reserve.tokyodisneyresort.jp/sp/hotel/list/?searchHotelCD=DHM&displayType=hotel-search"
                        )
                        notify_discord(msg)

                        # ✅ 詳細ページ → 同意チェック → 次へ
                        agree = driver.find_element(By.ID, "agreeCheck")
                        agree.click()
                        driver.find_element(By.XPATH, "//a[contains(@class, 'next')]" ).click()
                        print("仮予約画面へ遷移成功")
                        return

                driver.back()
                time.sleep(2)
            except Exception as e:
                print(f"詳細ページ遷移失敗: {e}")


def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    login(driver)

    while True:
        try:
            check_calendar_and_reserve(driver)
        except Exception as e:
            print(f"エラー: {e}")
        time.sleep(120)


if __name__ == "__main__":
    main()

