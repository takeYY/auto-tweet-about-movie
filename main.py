import os

import tweepy
from dotenv import load_dotenv
from flask import abort
from requests_oauthlib import OAuth1Session

load_dotenv()

REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]


def upload_media(media_path: str):
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    try:
        with open(media_path, "rb") as f:
            files = {"media": f}
            res = twitter.post("https://upload.twitter.com/1.1/media/upload.json", files=files)
            res.raise_for_status()

            res_json = res.json()
    except Exception as e:
        print(e)
        raise Exception(e)

    return str(res_json.get("media_id"))


def tweet(request):
    if not request.method == "POST":
        return abort(405)

    if not request.args and request.args.get("refresh_token"):
        return abort(400)

    if request.args.get("refresh_token") != REFRESH_TOKEN:
        return abort(401)

    client = tweepy.Client(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
    )

    message = "this is the test."
    media_id = upload_media("./docker_on_the_cat.jpeg")

    client.create_tweet(text=message, media_ids=[media_id])
    return message
