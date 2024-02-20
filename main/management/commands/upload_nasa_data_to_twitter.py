import datetime

from django.core.management import BaseCommand

from main.handler import UploadNASADataToTwitter
from main.models import APOD


class Command(BaseCommand):
    help = "Uploads NASA data to twitter"

    def handle(self, *args, **options):
        extra_apod_params = {}
        try:
            latest_apod_fetch = APOD.objects.latest('date')
            valid_next_day = latest_apod_fetch.date + datetime.timedelta(days=1)
            extra_apod_params.update({'start_date': str(valid_next_day)})
        except APOD.DoesNotExist:
            curr_date = datetime.datetime.now().date().isoformat()
            extra_apod_params = {'start_date': curr_date, 'end_date': curr_date}
        UploadNASADataToTwitter.upload_nasa_data_to_twitter(extra_params=extra_apod_params)