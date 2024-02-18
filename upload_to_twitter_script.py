import os
import requests
from requests_oauthlib import OAuth1


NASA_KEY = os.environ.get('NASA_KEY')

APOD_URL = 'https://api.nasa.gov/planetary/apod'
params = {'api_key': NASA_KEY}
r = requests.get(APOD_URL, params=params)
nasa_data = r.json()
nasa_image_url = nasa_data.get('hdurl')
nasa_image_title = nasa_data.get('title')
nasa_img_file_name = nasa_image_url.split('/')[-1]
nasa_image_data = requests.get(nasa_image_url).content
with open(nasa_img_file_name, 'wb') as f:
    f.write(nasa_image_data)

consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")


def connect_to_oauth(consumer_key, consumer_secret, acccess_token, access_token_secret):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(consumer_key, consumer_secret, acccess_token, access_token_secret)
    return url, auth


url, auth = connect_to_oauth(
    consumer_key, consumer_secret, access_token, access_token_secret
)

tweet_payload = {'text': nasa_image_title}

img_upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
with open(nasa_img_file_name, 'rb') as f:
    files = {'media': f}
    media_response = requests.post(img_upload_url, auth=auth, files=files)

os.remove(nasa_img_file_name)
media_json = media_response.json()
media_id = media_json.get('media_id')
tweet_payload_with_media_ids = {**tweet_payload, "media": {"media_ids": ["{}".format(media_id)]}}

request = requests.post(auth=auth, url=url, json=tweet_payload_with_media_ids, headers={"Content-Type": "application/json"})
print(request.json())
