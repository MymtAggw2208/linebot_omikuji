import os
import base64, hashlib, hmac
import logging
import random

from flask import abort, jsonify

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, PostbackEvent, TextMessage, TextSendMessage, 
    StickerMessage, StickerSendMessage,
    TemplateSendMessage,ButtonsTemplate,PostbackAction
)

omikuji = {'0':[6325,10979924,'大吉！良いことたくさんありますように'],
            '1':[11537,52002754,'中吉。いつも通りがいちばん'],
            '2':[11537,52002765,'凶…。平穏な日でありますように']}


def main(request):
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
    channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    line_bot_api = LineBotApi(channel_access_token)
    parser = WebhookParser(channel_secret)

    body = request.get_data(as_text=True)
    hash = hmac.new(channel_secret.encode('utf-8'),
        body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode()

    if signature != request.headers['X_LINE_SIGNATURE']:
        return abort(405)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return abort(405)

    for event in events:
        if isinstance(event, MessageEvent):
            if isinstance(event.message, TextMessage):
                line_bot_api.reply_message(
                    event.reply_token,
                    make_button_template()
                )
            else:
                continue
        if isinstance(event, PostbackEvent):
            line_bot_api.reply_message(
                event.reply_token,
                get_omikuji(event.postback.data)
            )
        else:
            continue

    return jsonify({ 'message': 'ok'})


def make_button_template():
    omikuji_key = ['0','1','2']
    message_template = TemplateSendMessage(
        alt_text='おみくじ',
        template=ButtonsTemplate(
            text='どれにする？',
            title='おみくじ',
            actions=[
                PostbackAction(
                    data=omikuji_key.pop(random.randint(0,2)),
                    label='これ'
                ),
                PostbackAction(
                    data=omikuji_key.pop(random.randint(0,1)),
                    label='それ'
                ),
                PostbackAction(
                    data=omikuji_key.pop(0),
                    label='あれ'
                )
            ]
        )
    )
    return message_template

def get_omikuji(key):
    result = omikuji[key]
    sticker_message = StickerSendMessage(
        package_id=result[0], sticker_id=result[1]
    )
    text_message = TextSendMessage(text=result[2])
    return [sticker_message, text_message]