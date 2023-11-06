# 必要なライブラリのインポート
# -----------------------------------------------------

import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json



# 各処理の関数
# -----------------------------------------------------

# loggerを使用するための関数
def setup_logging():

    logger = logging.getLogger('LoggingTest')    # ログの出力名を設定
    logger.setLevel(logging.INFO)                # ログレベル:INFOを指定

    sh = logging.StreamHandler() # ログのコンソール出力の設定
    logger.addHandler(sh)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')  # ログの出力形式の設定
    sh.setFormatter(formatter)

    return logger

# webdriverを使用するための関数
def webdriver_setup():
    # User-Agent
    user_agent = "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

    # オプション設定
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 画面を非表示
    options.add_argument('--user-agent=' + user_agent) # ユーザーエージェントの変更
    options.add_argument("--disable-gpu")
    options.add_argument("--enable-application-cache")
    options.add_experimental_option('detach', True)  # 自動でwebdriverを終了しない

    # WebDriverの初期化
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)


    return driver

# Spreadsheetへ接続するための関数
def connect_spreadsheet(sheet_name):
    with open('config/spreadsheet.json', 'r') as f:
        data = json.load(f)

    # 認証情報を指定してクライアントを作成
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(data["json_file"], scope)
    client = gspread.authorize(credentials)

    if sheet_name == "keyword":
        spread_sheet_key = data["connect"]
    elif sheet_name == "data":
        spread_sheet_key = data["connect"]
    else:
        raise ValueError("Invalid sheet_name. Use 'import' or 'export'.")

    # シート名に基づいてワークシートを取得
    worksheet = client.open_by_key(spread_sheet_key).worksheet(sheet_name)

    return worksheet




# メイン処理の実行
# -----------------------------------------------------

# WebDriverの初期化
driver = webdriver_setup()

# ロギングのセットアップを行い、ロガーを取得する
logger = setup_logging()

keywords = []
filenames = []

logger.info('データの取得を開始します。')

start_row = 1  # 開始行
worksheet_import = connect_spreadsheet("keyword")  # "import"シートに接続

# スプレッドシートの関数に接続して各リストに代入する
keywords = worksheet_import.col_values(1)[start_row:]  # A列の値を取得（A2から最終行まで）
posts = worksheet_import.col_values(3)[start_row:]  # C列の値を取得（C2から最終行まで）

for keyword, post in zip(keywords, posts):
    logger.info('「%s」の取得を開始します。', keyword)

    url = f"https://www.google.com/search?q={keyword}"
    driver.get(url)

    # ページの最下部へスクロール
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    time.sleep(2)

    # try:
    #     # 「次へ」というテキストを持つリンクが表示されるまで最大10秒間待機
    #     next_link = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.LINK_TEXT, "次へ >")))
    #     next_link.click()  # リンクをクリック
    # except TimeoutException:
    #     print("次へ リンクが指定時間内に見つかりませんでした。")

    # BeautifulSoupを使用してHTMLをパース
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 特定の要素を選択
    elements = soup.select('#main > div')

    # すべてのアンカータグを見つけるための空のリストを作成
    anchor_tags = []

    # 各要素内のアンカータグを見つけてリストに追加
    for element in elements:
        anchor_tags.extend(element.find_all('a'))

    urls = [tag.get('href') for tag in anchor_tags if tag.get('href')]

    # 条件に基づいてURLをフィルタリングし、必要な変換を適用
    filtered_urls = []
    for url in urls:
        # '/search?q='で始まるURLを無視
        if not url.startswith('/search?q='):
            # '/url?esrc=s&q=&rct=j&sa=U&url='を削除
            if url.startswith('/url?esrc=s&q=&rct=j&sa=U&url='):
                url = url.replace('/url?esrc=s&q=&rct=j&sa=U&url=', '')
            filtered_urls.append(url)

    # 加工後のURLリストを表示
    print(filtered_urls)


driver.quit()

# if not failed_list:
#     logger.info('%s 件の処理が完了しました。', len(keywords))
# else:
#     success = len(keywords) - len(failed_list)
#     logger.info('%s 件の処理が完了しました。（成功：%s 件 / 失敗：%s 件）', len(keywords), success, len(failed_list))

#     # ファイルに箇条書きで出力する
#     with open('get_amazon_image/export/failed_list.txt', 'w') as file:
#         for jan in failed_list:
#             file.write(f'{jan}\n')