import boto3
import json
import re

from datetime import datetime, timedelta
from ftplib import FTP
from io import BytesIO
from os import environ


class GeshemUpdate():

    def __init__(self):
        self.ftp = None
        self.s3 = boto3.client('s3')
        self.BUCKET = 'imgs.geshem.space'
        self.IMG_PREFIX = 'imgs/'

    def __enter__(self):
        self.init_ftp()
        return self

    def __exit__(self, *args):
        if self.ftp:
            self.ftp.quit()

    def init_ftp(self):
        host = environ.get("FTP_HOST")
        username = environ.get("FTP_USERNAME")
        password = environ.get("FTP_PASSWORD")
        if all([host, username, password]):
            self.ftp = FTP(host)
            self.ftp.login(username, password)
            self.ftp.cwd("From_IMS")
            print("Logged in to FTP server...")

    def get_latest_ftp_images(self):
        return sorted(list(self.ftp.nlst()))[-10:]

    def get_latest_bucket_keys(self):
        latest_keys = []
        yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime('%Y%m%d')

        try:
            latest_imgs = self.s3.list_objects_v2(Bucket=self.BUCKET, Prefix=self.IMG_PREFIX, StartAfter=self.IMG_PREFIX + yesterday)['Contents']
            latest_keys = [i['Key'] for i in latest_imgs]
        except KeyError:
            pass

        return latest_keys

    def fetch_missing_images(self):
        ftp_imgs = self.get_latest_ftp_images()
        s3_imgs = self.get_latest_bucket_keys()
        updated = False

        for img in ftp_imgs:
            key = self.key_from_filename(img)
            if key not in s3_imgs:
                self.fetch_image(img, key)
                updated = True

        return updated

    def fetch_image(self, img_name, key):
        img = BytesIO()
        print(f"Downloading {img_name} from FTP")
        self.ftp.retrbinary(f"RETR {img_name}", img.write)
        img.seek(0)
        print(f"Uploading to {key}")
        self.s3.put_object(Bucket=self.BUCKET, Key=key, Body=img, ContentType='image/png', CacheControl='public, max-age=31536000')

    def key_from_filename(self, filename):
        _name, date = filename.split(".")[0].split("_")
        res = 280
        # date conversion isn't really needed but we do it anyway just to make sure
        dt = datetime.strptime(date, '%Y%m%d%H%M')
        d = dt.strftime('%Y%m%d')
        t = dt.strftime('%H%M')
        return f'{self.IMG_PREFIX}{d}/{t}/{res}.png'

    def generate_json(self):
        latest_keys = self.get_latest_bucket_keys()
        keys = sorted(list(filter(lambda k: k.endswith('280.png'), latest_keys)))[-10:]
        index = json.dumps({'280': keys})
        self.s3.put_object(Bucket=self.BUCKET, Key='imgs.json', Body=index, ContentType='application/json', CacheControl='public, max-age=60')

    def run(self):
        updated = self.fetch_missing_images()
        if updated:
            self.generate_json()
        return f"Updated: {updated}"


def update(event, context):
    with GeshemUpdate() as gu:
        res = gu.run()
    body = {
        "message": "SUCCESS: \n" + res,
        "input": event
    }
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    return response


if __name__ == "__main__":
    with GeshemUpdate() as gu:
        res = gu.run()
