import os

import requests
from requests_oauthlib import OAuth1


class NasaClient:
    APOD_URL = 'https://api.nasa.gov/planetary/apod'

    def __init__(self, nasa_key):
        self.nasa_key = nasa_key

    def fetch_apod_data(self, extra_params):
        api_param = {'api_key': self.nasa_key}
        params = {**extra_params, **api_param} if extra_params else api_param
        nasa_res = requests.get(self.APOD_URL, params=params)
        nasa_data = nasa_res.json()
        return nasa_data


class TwitterClient:
    POST_URL = "https://api.twitter.com/2/tweets"
    MEDIA_URL = "https://upload.twitter.com/1.1/media/upload.json"

    def get_delete_url(self, tweet_id):
        return f"{self.POST_URL}/{tweet_id}"

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    def get_auth(self):
        return OAuth1(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)

    def create_tweet(self, title, media_id=None):
        tweet_payload = {
            'text': title
        }
        if media_id:
            tweet_payload.update({"media": {"media_ids": ["{}".format(media_id)]}})
        response = requests.post(auth=self.get_auth(), url=self.POST_URL, json=tweet_payload, headers={"Content-Type": "application/json"})
        tweet_id = response.json().get("data", {}).get("id", None)
        assert tweet_id is not None
        return tweet_id

    def delete_tweet(self, tweet_id):
        response = requests.delete(auth=self.get_auth(), url=self.get_delete_url(tweet_id))
        assert response.json().get("data", {}).get("deleted", False) is True

    def upload_image(self, file_name):
        with open(file_name, 'rb') as f:
            files = {'media': f}
            response = requests.post(self.MEDIA_URL, auth=self.get_auth(), files=files).json()
        media_id = response.get('media_id')
        return media_id

    def upload_video_init(self, file_name):
        request_data = {
            'command': 'INIT',
            'media_type': 'video/mp4',
            'total_bytes': os.path.getsize(file_name),
            'media_category': 'tweet_video'
        }

        req = requests.post(url=self.MEDIA_URL, data=request_data, auth=self.get_auth())
        media_id = req.json()['media_id']
        return media_id

    def upload_video_append(self, file_name, media_id):
        segment_id = 0
        bytes_sent = 0
        file = open(file_name, 'rb')

        while bytes_sent < os.path.getsize(file_name):
            chunk = file.read(4 * 1024 * 1024)

            request_data = {
                'command': 'APPEND',
                'media_id': media_id,
                'segment_index': segment_id
            }

            files = {
                'media': chunk
            }

            res = requests.post(url=self.MEDIA_URL, data=request_data, files=files, auth=self.get_auth())
            assert res.status_code == 204

            segment_id = segment_id + 1
            bytes_sent = file.tell()

    def upload_video_finalize(self, media_id):
        request_data = {
            'command': 'FINALIZE',
            'media_id': media_id
        }

        res = requests.post(url=self.MEDIA_URL, data=request_data, auth=self.get_auth())
        assert res.status_code == 200
