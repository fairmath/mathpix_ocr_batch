import base64
import json
import logging
import os
from glob import iglob
from pathlib import Path

import requests
from app import app
from PIL import Image as Pil_image
from simple_settings import settings

from .models import Image

images_topic = app.topic("images", value_type=Image)
logger = logging.getLogger(__name__)


@app.agent(images_topic)
async def image_converter(events):
    search_pattern = settings.SEARCH_PATTERN
    tif_path = os.path.dirname(os.path.dirname(search_pattern))
    async for event in events.filter(lambda e: not e.png):
        logger.info("Converting %s to png", event)
        Path(f"{settings.PNG_PATH}/{event.folder:03d}").mkdir(parents=True, exist_ok=True)
        outfile = await get_filename(event)
        if not os.path.isfile(outfile):
            im = Pil_image.open(f"{tif_path}/{event.folder:03d}/{event.file:08d}.TIF")
            im.save(outfile)
        event.png = True
        yield event


async def get_filename(img, extension="png"):
    if extension == "png":
        path = settings.PNG_PATH
    else:
        path = settings.JSON_PATH
    return f"{path}/{img.folder:03d}/{img.file:08d}.{extension}"


def convert_image(file_path):
    image_uri = "data:image/png;base64," + base64.b64encode(open(file_path, "rb").read()).decode()
    r = requests.post(
        "https://api.mathpix.com/v3/text",
        data=json.dumps(
            {
                "src": image_uri,
                "formats": ["text", "data", "html"],
                "data_options": {"include_asciimath": True, "include_latex": True},
                "include_line_data": True,
                "include_detected_alphabets": True,
            }
        ),
        headers={
            "app_id": settings.MATHPIX_APP_ID,
            "app_key": settings.MATHPIX_APP_KEY,
            "Content-type": "application/json",
        },
    )
    return json.loads(r.text)


@app.agent(images_topic)
async def image_extractor(events):
    async for event in events.filter(lambda e: e.png and not e.json):
        logger.info("Converting %s to json", event)
        png_filename = await get_filename(event)
        if os.path.isfile(png_filename):
            Path(f"{settings.JSON_PATH}/{event.folder:03d}").mkdir(parents=True, exist_ok=True)
            outfile = await get_filename(event, "json")
            if not os.path.isfile(outfile):
                res = convert_image(png_filename)
                with open(outfile, "w") as file_out:
                    json.dump(res, file_out, indent=4, sort_keys=True, ensure_ascii=False)
        event.json = True
        yield event


@app.task
async def scan_files():
    search_pattern = settings.SEARCH_PATTERN
    logger.info(f"Indexing {search_pattern}")
    for found in iglob(search_pattern, recursive=True):
        base = os.path.basename(found)
        file_number = int(os.path.splitext(base)[0])
        dirname = os.path.dirname(found)
        folder_number = int(os.path.basename(dirname))
        image = Image(file=file_number, folder=folder_number, png=False, json=False)
        await images_topic.send(value=image)
