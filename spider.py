"""
[Resources] Download thumbnails from Google Drive
"""

from os import environ, makedirs
from pathlib import Path
import requests, shutil, yaml

API_KEY = environ['GOOGLE_API_KEY']
API_URL = 'https://www.googleapis.com/drive/v3/files/'
BASE_FOLDER_PATH = Path(__file__).parent.resolve()
DATA_FOLDER_PATH = BASE_FOLDER_PATH / 'data'
STATIC_FOLDER_PATH = BASE_FOLDER_PATH / 'static' / 'resources'
params = {
    'fields': 'id,name,hasThumbnail,thumbnailLink',
    'key': API_KEY
}
id_name_mapping = {}

makedirs(STATIC_FOLDER_PATH, exist_ok=True)
with open(DATA_FOLDER_PATH / 'resources.yml', 'r', encoding='utf-8') as f:
    raw = yaml.load(f, Loader=yaml.SafeLoader)

for section in raw:
    for group in section['groups']:
        for file_id in group['file_ids']:
            req = requests.get(API_URL + file_id, params=params)
            req.raise_for_status()

            ret_json = req.json()
            id_name_mapping[ret_json['id']] = ret_json['name']
            if not ret_json['hasThumbnail']:
                continue

            req2 = requests.get(ret_json['thumbnailLink'], stream=True)
            req2.raise_for_status()

            with open(STATIC_FOLDER_PATH / (file_id + '.png'), 'wb') as f:
                req2.raw.decode_content = True  # See: https://stackoverflow.com/a/13137873
                shutil.copyfileobj(req2.raw, f)

with open(DATA_FOLDER_PATH / '_resources_mapping.yml', 'w', encoding='utf-8') as f:
    for key, val in id_name_mapping.items():
        f.write(f'{key}: {val}\n')
