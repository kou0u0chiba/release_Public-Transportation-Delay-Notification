import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import logging
import pytz # タイムゾーンを設定するためにpytzを使用

# ログの設定
logging.basicConfig(level=logging.INFO)

# Gmail認証情報を環境変数から取得
GMAIL_USER = os.environ.get('GMAIL_USER')  # 遅延情報の送付元のメールアドレス
GMAIL_PASS = os.environ.get('GMAIL_PASS')  # 上記メールアドレスのアプリケーション固有のパスワード

# 送信先メールアドレスを環境変数から取得
TO_EMAIL = os.environ.get('TO_EMAIL')

# 環境変数が設定されているか確認
if not GMAIL_USER or not GMAIL_PASS or not TO_EMAIL:
    raise ValueError("環境変数 GMAIL_USER, GMAIL_PASS, TO_EMAIL のいずれかが設定されていません")

# メールのタイトルと本文テンプレート
EMAIL_SUBJECT = '*** 運行情報'
EMAIL_BODY = (
    '現在、***に遅延が発生しています。<br>'
    '<a href="https://***">***のホームページ</a>'
    'をご確認ください。'
)

# 遅延情報を取得したい路線の会社のホームページ
URL = 'https://***'

# 遅延の確認
def check_delay():
    try:
        response = requests.get(URL)  # HTTP GETリクエストを送信
        response.raise_for_status()  # HTTPエラーがある場合に例外を発生させる
        soup = BeautifulSoup(response.text, 'html.parser')  # HTMLをパースする
        status_element = soup.find('a', class_='status_link')  # 運行状況を表示しているhtml要素クラス名を探す、任意の要素クラスを指定してください

        # 運行情報の判定
        if status_element:
            status_text = status_element.text
            if '遅延' in status_text or '遅れ' in status_text:
                return True
    except requests.RequestException as e:
        # HTTPエラーやネットワークエラーが発生した場合の処理
        logging.error(f"Error checking delay: {e}")
    return False

# 送信メールの設定
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))  # メール本文をHTML形式で設定

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, TO_EMAIL, text)
        server.quit()
        logging.info("Email sent successfully") # メールが正常に送信されたログ
        return True
    except smtplib.SMTPException as e:
        logging.error(f"Error sending email: {e}") # エラーメッセージのログ
        return False

# メール送信、ホームページのチェック頻度
def main(request=None): # 引数を必要に応じて対応
# JSTタイムゾーンを設定
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    logging.info(f"Current time in JST: {now.strftime('%Y-%m-%d %H:%M:%S')}") # 実行時間のログ
    
    # 月曜から金曜、7:00-22:05の間に以下の処理を行います
    if 0 <= now.weekday() <= 4 and (7 <= now.hour < 22 or (now.hour == 22 and now.minute <= 5)):
        if check_delay():
            logging.info("Delay detected, sending email.") # 遅延を確認し、メールを送信したログ
            email_sent = send_email(EMAIL_SUBJECT, EMAIL_BODY) # 遅延している場合にメールを送信

            # 送信に失敗した場合、ログに記録
            if not email_sent:
                logging.error("Email sending failed, will retry in the next scheduled execution.")
        else:
           logging.info("No delay detected, no email sent.") # 遅延していない場合のログ
    else:
        logging.info("Outside of checking hours.") # 遅延確認時間外の場合のログ

    logging.info("Checked delay status.") # 遅延確認が終了した事を意味するログ
    return 'Checked delay status.'
