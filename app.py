import random
import requests
import re
import configparser
from bs4 import BeautifulSoup
from imgurpython import ImgurClient
import urllib

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

# config
line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
client_id = config['imgur_api']['Client_id']
client_secret = config['imgur_api']['Client_Secret']
album_id = config['imgur_api']['Album_id']


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 當看到"news"時會去開起technews網站內容
def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing technews ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""

    for index, data in enumerate(soup.select('article div h1.entry-title a')):
        if index == 12:
            return content
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content
# 當是"最新電影"的時候會去查詢電影
def movie():
	target_url = 'https://movies.yahoo.com.tw/'
	rs = requests.session()
	res = rs.get(target_url, verify=True)
	res.encoding = 'utf-8'
	soup = BeautifulSoup(res.text, 'lxml')   
	content = ""
	for index , data in enumerate(soup.select('html body div#maincontainer main div.maincontent.ga_index div#container div#content_r div.r_box div.r_box_inner div.ranking_inner_r div.tab-content div#list1 ul.ranking_list_r a')):
		if index == 20:
			return content 
		title = data.text
		link =  data['href']
		content += '{}\n{}\n'.format(title, link)
	return content

# 當看到"corgi"或"柯基"的訊息時會去相簿隨機po出一張圖片 當是"youtube"的時候會將後面的字做搜尋並列出查詢結果的一項
# 為根據特別訊息做出反應的code
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = ""
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)

    if event.message.text == "corgi" or event.message.text == "柯基":
        client = ImgurClient(client_id, client_secret)
        album = client.get_account_albums(album_id)
        images = client.get_album_images(album[0].id)
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        message = ImageSendMessage(original_content_url=url, preview_image_url=url)

    elif "youtube" in event.message.text:
        target = event.message.text[8:len(event.message.text)]
        target_url = 'https://www.youtube.com/results?search_query=' + target
        rs = requests.session()
        res = rs.get(target_url, verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        seqs = ['https://www.youtube.com{}'.format(data.find('a')['href']) for data in soup.select('.yt-lockup-title')]
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text=seqs[0]),
                TextSendMessage(text=seqs[1]),
                TextSendMessage(text=seqs[2])
            ])

    elif event.message.text == "news":
        content = technews()
        message = TextSendMessage(text=content)
		
    elif event.message.text == "最新電影":
        a=movie()
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=a))
		
    else:
        message = TextSendMessage(text=event.message.text)

    line_bot_api.reply_message(event.reply_token, message)


import os

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
