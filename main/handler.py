import abc
import datetime
import enum
import os
import pathlib
import time

import requests
from django.db import IntegrityError

from pytube import YouTube

from main.clients import NasaClient, TwitterClient
from main.data import APODData
from main.models import APOD


NASA_CLIENT = NasaClient(os.environ.get('NASA_KEY'))
TWITTER_CLIENT = TwitterClient(
    os.environ.get("TWITTER_CONSUMER_KEY"), os.environ.get("TWITTER_CONSUMER_SECRET"),
    os.environ.get("TWITTER_ACCESS_TOKEN"), os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
)


class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class BaseUploader:
    def __init__(self, file_url):
        self.file_url = file_url

    @abc.abstractmethod
    def create_file_from_url(self):
        raise NotImplemented()

    @abc.abstractmethod
    def upload(self):
        raise NotImplemented()

    def clean_up(self, upload_file_name):
        pathlib.Path(upload_file_name).unlink()


class ImageUploader(BaseUploader):

    def create_file_from_url(self):
        img_file_name = self.file_url.split('/')[-1]
        img_data = requests.get(self.file_url).content
        with open(img_file_name, 'wb') as img_file:
            img_file.write(img_data)
        return img_file_name

    def upload(self):
        upload_file_name = self.create_file_from_url()
        media_id = TWITTER_CLIENT.upload_image(upload_file_name)
        self.clean_up(upload_file_name)
        return media_id


class VideoUploader(BaseUploader):

    def create_file_from_url(self):
        yt = YouTube(self.file_url)
        file_path_str = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
        return file_path_str

    def upload(self):
        upload_file_name = self.create_file_from_url()
        media_id = TWITTER_CLIENT.upload_video_init(upload_file_name)
        TWITTER_CLIENT.upload_video_append(upload_file_name, media_id)
        TWITTER_CLIENT.upload_video_finalize(media_id)
        self.clean_up(upload_file_name)
        return media_id


class TwitterMediaFactory:
    @classmethod
    def from_media_type(cls, media_type):
        return {
            MediaType.IMAGE.value: ImageUploader,
            MediaType.VIDEO.value: VideoUploader
        }.get(media_type)


class MediaUpload:

    def __init__(self,file_url, media_type):
        self.file_url = file_url
        self.media_type = media_type

    def get_media_uploader(self):
        return TwitterMediaFactory.from_media_type(self.media_type)(self.file_url)


class ManageTweet:

    def __init__(self,title, media_id=None):
        self.title = title
        self.media_id = media_id

    def post(self):
        tweet_id = TWITTER_CLIENT.create_tweet(self.title, self.media_id)
        return tweet_id

    def delete(self, tweet_id):
        TWITTER_CLIENT.delete_tweet(tweet_id)


class UploadNASADataToTwitter:

    @classmethod
    def upload_nasa_data_to_twitter(cls, extra_params=None, sleep=10):
        if extra_params is None:
            extra_params = {}
        nasa_data = NASA_CLIENT.fetch_apod_data(extra_params)
        nasa_data = [nasa_data] if isinstance(nasa_data, dict) else nasa_data
        for data in nasa_data:
            nasa_media_url = data.get('url')
            nasa_media_title = data.get('title')
            date = data.get('date')
            if not APOD.objects.filter(date=datetime.datetime.fromisoformat(date), title=nasa_media_title).exists():
                nasa_media_type = data.get('media_type')
                twitter_media_upload = MediaUpload(nasa_media_url, nasa_media_type)
                media_uploader_class = twitter_media_upload.get_media_uploader()
                media_id = media_uploader_class.upload()
                time.sleep(sleep)  # allow some time for twitter to finalize big media uploads
                manage_tweet = ManageTweet(nasa_media_title, media_id)
                tweet_id = manage_tweet.post()
                cls.create_entry_in_db(data, media_id, tweet_id, manage_tweet)

    @classmethod
    def create_entry_in_db(cls, data, media_id, tweet_id, manage_tweet):
        apod = APODData.from_dict(
            date_str=data.get('date'),
            title=data.get('title'),
            explanation=data.get('explanation'),
            url=data.get('url'),
            media_type=data.get('media_type'),
            service_version=data.get('service_version'),
            twitter_media_id=str(media_id),
            twitter_post_id=str(tweet_id)
        )
        try:
            apod.save()
        except IntegrityError as e:
            print(e)
            manage_tweet.delete(tweet_id)
            print(f"{tweet_id} deleted")
