import datetime
import math
import os
import urllib.request

import requests
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

TMDB_API_KEY = os.environ["TMDB_API_KEY"]


def get_datetime_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))


def is_time2tweet(target_number: float):
    now = get_datetime_now()

    minute = now.minute
    time2tweet = int(target_number % 60)

    return minute == time2tweet


def get_current_movie_rank() -> int:
    date: datetime = get_datetime_now()
    hour: int = date.hour
    sequential_order: int = (hour // 3) - 4

    ranking: int = 3 * date.weekday() + sequential_order
    return ranking


def get_trend_movies(page: int = 1):
    trend_movie_endpoint = "https://api.themoviedb.org/3/trending/movie/week"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "ja-JP",
        "region": "JP",
        "page": page,
    }
    res = requests.get(url=trend_movie_endpoint, params=params)
    res.raise_for_status()

    return res.json()


def get_current_trend_movie(ranking: int, page: int):
    trend_movies_json: dict[str, str] = get_trend_movies(page=page)
    trend_movie_result = trend_movies_json.get("results")[ranking]
    trend_movie = {
        "title": trend_movie_result.get("title"),
        "popularity": trend_movie_result.get("popularity"),
        "poster_path": trend_movie_result.get("poster_path"),
        "vote_average": trend_movie_result.get("vote_average"),
        "vote_count": trend_movie_result.get("vote_count"),
    }

    return trend_movie


def get_movie_media_url(poster_path: str):
    return f"https://image.tmdb.org/t/p/w500{poster_path}"


def create_average_rating_moon_icon(
    vote_average: float,
    max_moon: int = 5,
    q25: float = 0.25,
    q75: float = 0.75,
):
    vote_float, vote_int = math.modf(vote_average)
    vote_int = int(vote_int)

    full_moon = "🌕" * vote_int
    if vote_float < q25:
        moon = "🌘"
    elif vote_float < q75:
        moon = "🌗"
    else:
        moon = "🌖"
    new_moon = "🌑" * (max_moon - len(full_moon) - len(moon))

    return full_moon + moon + new_moon


def create_tweet_message(trend_movie: dict, ranking: int):
    now = get_datetime_now()

    today = now.strftime("%y.%m.%d")
    rank = ranking + 1
    title = trend_movie["title"]
    popularity = trend_movie["popularity"]
    vote_average = trend_movie["vote_average"]
    average_rating_icon = create_average_rating_moon_icon(vote_average / 2)
    vote_count = trend_movie["vote_count"]
    return "\n".join(
        [
            f"人気映画ランキング ({today})",
            "",
            f"{rank}位 {popularity:,} point",
            f"『{title}』",
            f"{average_rating_icon} ({vote_count:,})",
        ]
    )


def upload_media(media_url: str):
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    try:
        with urllib.request.urlopen(media_url) as web_file:
            media_data = web_file.read()
            files = {"media": media_data}
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

    ranking: int = get_current_movie_rank()
    page: int = 1 if ranking < 20 else 2
    trend_movie = get_current_trend_movie(ranking=ranking, page=page)
    if not is_time2tweet(target_number=trend_movie["popularity"]):
        return "ツイートする時間ではありません。"

    message = create_tweet_message(trend_movie, ranking)
    media_url = get_movie_media_url(trend_movie["poster_path"])
    media_id = upload_media(media_url=media_url)

    client.create_tweet(text=message, media_ids=[media_id])
    return message
