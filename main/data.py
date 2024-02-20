import datetime

from main.models import APOD


class APODData:

    @staticmethod
    def from_dict(date_str, title, explanation, url, media_type, service_version, twitter_media_id=None, twitter_post_id=None):
        return APOD(
            date=datetime.date.fromisoformat(date_str),
            title=title,
            explanation=explanation,
            url=url,
            media_type=media_type,
            service_version=service_version,
            twitter_media_id=str(twitter_media_id),
            twitter_post_id=str(twitter_post_id)
        )
