import redis
import requests

from flask import Flask, render_template
from os import environ
from pathlib import Path
from redis.exceptions import ConnectionError

MAPS_JSON = 'http://map.govmap.gov.il/rainradar/radar.json'
STATIC_DIR = Path(__file__).resolve().parents[0] / 'static'

app = Flask(__name__)
redis = redis.from_url(environ.get('REDIS_URL', 'redis://localhost'))

def fetch_latest_images():
    maps_json = requests.get(MAPS_JSON).json()
    for r in ['images140', 'images280']:
        imgs = sorted(maps_json[r].items(), key=lambda x: x[0], reverse=True)[:1]  # only take latest
        for _ts, url in imgs:
            image = requests.get('http://' + url)
            filename = r[-3:] + '.png'
            with open(str(STATIC_DIR / filename), 'wb+') as f:
                f.write(image.content)

@app.route('/')
def home():
    return render_template('index.html')

@app.after_request
def update_images(response):
    # poor man's background task
    try:
        if not redis.get('fresh'):
            redis.setex('fresh', 'yes', 60)
            fetch_latest_images()
    except ConnectionError as e:
        if app.debug:
            fetch_latest_images()
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)