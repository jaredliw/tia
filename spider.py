"""
[Resources] Download thumbnails from Google Drive
"""

import logging
import shutil
from io import BytesIO
from os import environ, makedirs
from pathlib import Path

import fitz
import requests
import yaml
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

flag = environ.get('IS_RUNNING_ON_CLOUD', 'false')
logger.info(f'Environment variable "IS_RUNNING_ON_CLOUD" is set to "{flag}"')
IS_RUNNING_ON_CLOUD = flag.lower() == 'true'
API_KEY = 'AIzaSyBTNnSWLmF5RnuROzZ53J4PXduhVkaJeHk'
API_URL = 'https://www.googleapis.com/drive/v3/files/'
BASE_FOLDER_PATH = Path(__file__).parent.resolve()
DATA_FOLDER_PATH = BASE_FOLDER_PATH / 'data'
STATIC_FOLDER_PATH = BASE_FOLDER_PATH / 'static' / 'resources'
METADATA_PARAMS = {
    'fields': 'id,name,hasThumbnail,thumbnailLink',
    'key': API_KEY
}
FILE_DOWNLOAD_PARAMS = {
    'alt': 'media',
    'key': API_KEY
}
id_name_mapping = {}

logger.info('Started')
makedirs(STATIC_FOLDER_PATH, exist_ok=True)
with open(DATA_FOLDER_PATH / 'resources.yml', 'r', encoding='utf-8') as f:
    logger.info('Loading yaml file')
    raw = yaml.load(f, Loader=yaml.SafeLoader)

for section in raw:
    for group in section['groups']:
        if 'has_subsection' in group and group['has_subsection'] == True:
            for subsection in group['subsection']:
                for file_id in subsection['file_ids']:
                    logger.info(f'Requesting metadata for file with id "{file_id}"')
                    req = requests.get(API_URL + file_id, params=METADATA_PARAMS)
                    req.raise_for_status()

                    ret_json = req.json()
                    id_name_mapping[ret_json['id']] = ret_json['name']
                    save_img_path = STATIC_FOLDER_PATH / (file_id + '.png')
                    if ret_json['hasThumbnail']:
                        logger.info('The file has a thumbnail, requesting')
                        thumbnail_req = requests.get(ret_json['thumbnailLink'], stream=True)
                        thumbnail_req.raise_for_status()

                        with open(save_img_path, 'wb') as f:
                            logger.info(f'Saving thumbnail to "{save_img_path}"')
                            thumbnail_req.raw.decode_content = True  # See: https://stackoverflow.com/a/13137873
                            shutil.copyfileobj(thumbnail_req.raw, f)
                    else:
                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # This code segment downloads the whole pdf file from the drive, with a high chance of being blocked by
                        # Google if it is running unsupervised on GitHub.
                        # When running on a local machine, one should adjust the code accordingly to generate thumbnails for
                        # large files while maintaining an adequate request rate.
                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        logger.info('The file does not have a thumbnail')
                        if IS_RUNNING_ON_CLOUD:
                            logger.info('Script is not running locally, skip this file id')
                            continue
                        
                        logger.info('Downloading the file')
                        file_req = requests.get(API_URL + file_id, params=FILE_DOWNLOAD_PARAMS)
                        file_req.raise_for_status()
                        if file_req.headers.get('Content-Type', '').lower() != 'application/pdf':
                            logger.info('Not a pdf file, skip this file id')
                            continue
                        
                        pdf_reader = fitz.open(stream=file_req.content, filetype="pdf")
                        cover_pixmap = pdf_reader.load_page(0).get_pixmap()
                        cover_img = Image.open(BytesIO(cover_pixmap.tobytes()))
                        cover_img.thumbnail((250, 250))
                        logger.info(f'Saving thumbnail to "{save_img_path}"')
                        cover_img.save(save_img_path)
                
        else:
            for file_id in group['file_ids']:
                logger.info(f'Requesting metadata for file with id "{file_id}"')
                req = requests.get(API_URL + file_id, params=METADATA_PARAMS)
                req.raise_for_status()

                ret_json = req.json()
                id_name_mapping[ret_json['id']] = ret_json['name']
                save_img_path = STATIC_FOLDER_PATH / (file_id + '.png')
                if ret_json['hasThumbnail']:
                    logger.info('The file has a thumbnail, requesting')
                    thumbnail_req = requests.get(ret_json['thumbnailLink'], stream=True)
                    thumbnail_req.raise_for_status()

                    with open(save_img_path, 'wb') as f:
                        logger.info(f'Saving thumbnail to "{save_img_path}"')
                        thumbnail_req.raw.decode_content = True  # See: https://stackoverflow.com/a/13137873
                        shutil.copyfileobj(thumbnail_req.raw, f)
                else:
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # This code segment downloads the whole pdf file from the drive, with a high chance of being blocked by
                    # Google if it is running unsupervised on GitHub.
                    # When running on a local machine, one should adjust the code accordingly to generate thumbnails for
                    # large files while maintaining an adequate request rate.
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    logger.info('The file does not have a thumbnail')
                    if IS_RUNNING_ON_CLOUD:
                        logger.info('Script is not running locally, skip this file id')
                        continue

                    logger.info('Downloading the file')
                    file_req = requests.get(API_URL + file_id, params=FILE_DOWNLOAD_PARAMS)
                    file_req.raise_for_status()
                    if file_req.headers.get('Content-Type', '').lower() != 'application/pdf':
                        logger.info('Not a pdf file, skip this file id')
                        continue

                    pdf_reader = fitz.open(stream=file_req.content, filetype="pdf")
                    cover_pixmap = pdf_reader.load_page(0).get_pixmap()
                    cover_img = Image.open(BytesIO(cover_pixmap.tobytes()))
                    cover_img.thumbnail((250, 250))
                    logger.info(f'Saving thumbnail to "{save_img_path}"')
                    cover_img.save(save_img_path)

logger.info('Writing mapping yaml file')
with open(DATA_FOLDER_PATH / '_resources_mapping.yml', 'w', encoding='utf-8') as f:
    for key, val in id_name_mapping.items():
        f.write(f'{key}: {val}\n')
logger.info('Finished')
