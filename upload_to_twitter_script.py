import abc
import datetime
import enum
import os
import pathlib
import time

import requests

from pytube import YouTube
from requests_oauthlib import OAuth1


class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class TwitterAuth:

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    def get_auth(self):
        return OAuth1(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)


class TwitterBaseUploader:
    def __init__(self, file_url, auth, upload_url):
        self.file_url = file_url
        self.auth = auth
        self.upload_url = upload_url

    @abc.abstractmethod
    def create_file_from_url(self):
        raise NotImplemented()

    @abc.abstractmethod
    def upload(self):
        raise NotImplemented()

    def clean_up(self, upload_file_name):
        pathlib.Path(upload_file_name).unlink()


class TwitterImageUploader(TwitterBaseUploader):

    def create_file_from_url(self):
        img_file_name = self.file_url.split('/')[-1]
        img_data = requests.get(self.file_url).content
        with open(img_file_name, 'wb') as img_file:
            img_file.write(img_data)
        return img_file_name

    def upload(self):
        upload_file_name = self.create_file_from_url()
        with open(upload_file_name, 'rb') as f:
            files = {'media': f}
            response = requests.post(self.upload_url, auth=self.auth, files=files).json()
        media_id = response.get('media_id')
        self.clean_up(upload_file_name)
        return media_id


class TwitterVideoUploader(TwitterBaseUploader):

    def create_file_from_url(self):
        yt = YouTube(self.file_url)
        file_path_str = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
        return file_path_str

    def upload_init(self, file_name):
        request_data = {
            'command': 'INIT',
            'media_type': 'video/mp4',
            'total_bytes': os.path.getsize(file_name),
            'media_category': 'tweet_video'
        }

        req = requests.post(url=self.upload_url, data=request_data, auth=self.auth)
        media_id = req.json()['media_id']
        return media_id

    def upload_append(self, file_name, media_id):
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

            res = requests.post(url=self.upload_url, data=request_data, files=files, auth=self.auth)

            segment_id = segment_id + 1
            bytes_sent = file.tell()

    def upload_finalize(self, media_id):
        request_data = {
            'command': 'FINALIZE',
            'media_id': media_id
        }

        res = requests.post(url=self.upload_url, data=request_data, auth=self.auth)

    def upload(self):
        upload_file_name = self.create_file_from_url()
        media_id = self.upload_init(upload_file_name)
        self.upload_append(upload_file_name, media_id)
        self.upload_finalize(media_id)
        self.clean_up(upload_file_name)
        return media_id


class TwitterMediaFactory:
    @classmethod
    def from_media_type(cls, media_type):
        return {
            MediaType.IMAGE.value: TwitterImageUploader,
            MediaType.VIDEO.value: TwitterVideoUploader
        }.get(media_type)


class NasaAPOD:
    APOD_URL = 'https://api.nasa.gov/planetary/apod'

    def __init__(self, nasa_key):
        self.nasa_key = nasa_key

    def fetch_data_from_nasa(self, start_date, end_date):
        params = {'api_key': self.nasa_key}
        today = datetime.datetime.now().date()
        if start_date is None and end_date is None:
            params.update({'start_date': today, 'end_date': today})
        elif start_date and end_date:
            params.update({'start_date': start_date, 'end_date': end_date})
        elif start_date:
            params.update({'start_date': start_date})
        nasa_res = requests.get(self.APOD_URL, params=params)
        nasa_data = nasa_res.json()
        return nasa_data


class TwitterMediaUpload:
    MEDIA_URL = "https://upload.twitter.com/1.1/media/upload.json"

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, file_url, media_type):
        self.file_url = file_url
        self.media_type = media_type
        self.auth = TwitterAuth(consumer_key, consumer_secret, access_token, access_token_secret)

    def get_media_uploader(self):
        return TwitterMediaFactory.from_media_type(self.media_type)(self.file_url, self.auth.get_auth(), self.MEDIA_URL)


class TwitterPost:
    POST_URL = "https://api.twitter.com/2/tweets"

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, title, media_id=None):
        self.title = title
        self.media_id = media_id
        self.auth = TwitterAuth(consumer_key, consumer_secret, access_token, access_token_secret)

    def post(self):
        tweet_payload = {
            'text': self.title
        }
        if self.media_id:
            tweet_payload.update({"media": {"media_ids": ["{}".format(self.media_id)]}})
        response = requests.post(auth=self.auth.get_auth(), url=self.POST_URL, json=tweet_payload, headers={"Content-Type": "application/json"})


class UploadNASADataToTwitter:

    @classmethod
    def get_nasa_key(cls):
        return os.environ.get('NASA_KEY')

    @classmethod
    def get_twitter_keys(cls):
        return os.environ.get("TWITTER_CONSUMER_KEY"), os.environ.get("TWITTER_CONSUMER_SECRET"), os.environ.get("TWITTER_ACCESS_TOKEN"), os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

    @classmethod
    def upload_nasa_data_to_twitter(cls, start_date_str=None, end_date_str=None):
        nasa_apod = NasaAPOD(cls.get_nasa_key())
        consumer_key, consumer_secret, access_token, access_token_secret = cls.get_twitter_keys()
        nasa_data = nasa_apod.fetch_data_from_nasa(start_date_str, end_date_str)
        for data in nasa_data:
            nasa_media_url = data.get('url')
            nasa_media_title = data.get('title')
            nasa_media_type = data.get('media_type')
            twitter_media_upload = TwitterMediaUpload(consumer_key, consumer_secret, access_token, access_token_secret, nasa_media_url, nasa_media_type)
            media_uploader_class = twitter_media_upload.get_media_uploader()
            media_id = media_uploader_class.upload()
            time.sleep(10)
            twitter_post = TwitterPost(consumer_key, consumer_secret, access_token, access_token_secret, nasa_media_title, media_id)
            twitter_post.post()


UploadNASADataToTwitter.upload_nasa_data_to_twitter('2024-02-14', '2024-02-15')
