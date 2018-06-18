import random
import requests
import configparser
import os
import urllib.request
import sys
from urllib.parse import quote
from bs4 import BeautifulSoup
from imgurpython import ImgurClient
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

# keyword
Animal = ["corgi", "柯基", "狗狗", "狗", "dog", "dogs"]
Movie = ["movie", "movies", "電影"]
News = ["news", "新聞"]


# Extra funciton
def is_chinese(uchar):
    if u'\u4e00' <= uchar <= u'\u9fa5':
        return True
    else:
        return False


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


def corgi():
    client = ImgurClient(client_id, client_secret)
    album = client.get_account_albums(album_id)
    images = client.get_album_images(album[0].id)
    index = random.randint(0, len(images) - 1)
    url = images[index].link
    return url


def youtube(target):
    target_url = 'https://www.youtube.com/results?search_query=' + target
    rs = requests.session()
    res = rs.get(target_url, verify=True)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    seqs = ['https://www.youtube.com{}'.format(data.find('a')['href']) for data in soup.select('.yt-lockup-title')]
    content = '{}\n{}\n{}'.format(seqs[0], seqs[1], seqs[2])
    return content


def translate(query, to_l="zh-TW", from_l="en"):
    typ = sys.getfilesystemencoding()
    C_agent = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36"}
    flag = 'class="t0">'
    target_url = "http://translate.google.com/m?hl=%s&sl=%s&q=%s" % (to_l, from_l, query.replace(" ", "+"))
    request = urllib.request.Request(target_url, headers=C_agent)
    page = str(urllib.request.urlopen(request).read().decode(typ))
    content = page[page.find(flag) + len(flag):]
    content = content.split("<")[0]
    return content


def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing technews ...')
    rs = requests.session()
    res = rs.get(target_url, verify=True)
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


def movie():
    target_url = 'https://movies.yahoo.com.tw/'
    print('Start parsing movies ...')
    rs = requests.session()
    res = rs.get(target_url, verify=True)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'lxml')
    content = ""

    for index, data in enumerate(soup.select('div.tab-content ul.ranking_list_r a')):
        if index == 10:
            return content
        title = data.find('span').text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = ""
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)

    if event.message.text.lower() in Animal:
        url = corgi()
        message = ImageSendMessage(original_content_url=url, preview_image_url=url)
    elif event.message.text == "HELP" or event.message.text == "help":
        buttons_template = TemplateSendMessage(
            alt_text='help',
            template=ButtonsTemplate(
                title='help',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='新聞',
                        text='news'
                    ),
                    MessageTemplateAction(
                        label='電影',
                        text='movies'
                    ),
                    MessageTemplateAction(
                        label='動物',
                        text='corgi'
                    ),
                    MessageTemplateAction(
                        label='more',
                        text='more'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif event.message.text == "More" or event.message.text == "more":
        buttons_template = TemplateSendMessage(
            alt_text='help2',
            template=ButtonsTemplate(
                title='help2',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='YouTube查詢',
                        text='youtube'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif tubesearch == True:
        tubesearch = False
        target = event.message.text
        content = youtube(target)
        message = TextSendMessage(text=content)
    elif event.message.text == "youtube" and tubesearch == False:
        tubesearch = True
        message = TextSendMessage(text="請輸入查詢內容")
    elif str(event.message.text)[0:2] == "翻譯":
        if event.message.text[3:]:
            target = event.message.text[3:]
            if is_chinese(target[0]):
                content = translate(quote(target), "en", "zh-TW")
            else:
                content = translate(target)
            message = TextSendMessage(text=content)
        else:
            message = TextSendMessage(text="請輸入要翻譯的字")
    elif event.message.text.lower() in News:
        content = technews()
        message = TextSendMessage(text=content)
    elif event.message.text.lower() in Movie:
        content = movie()
        message = TextSendMessage(text=content)
    elif event.message.text == "開始玩":
        buttons_template = TemplateSendMessage(
            alt_text='開始玩 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='新聞',
                        text='news'
                    ),
                    MessageTemplateAction(
                        label='電影',
                        text='movies'
                    ),
                    MessageTemplateAction(
                        label='動物',
                        text='corgi'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0
    else:
        message = TextSendMessage(text="人家看不懂耶~")

    line_bot_api.reply_message(event.reply_token, message)


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    print("package_id:", event.message.package_id)
    print("sticker_id:", event.message.sticker_id)
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,
                   107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
                   126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])
    sticker_message = StickerSendMessage(package_id='1', sticker_id=sticker_id)
    line_bot_api.reply_message(event.reply_token, sticker_message)


if __name__ == "__main__":
    tubesearch = False
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
