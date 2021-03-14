import logging
import os
from glob import iglob

from app import app
from simple_settings import settings

from .models import Image, PageView

page_view_topic = app.topic("page_views", value_type=PageView)
hello_world_topic = app.topic("hello_world")
images_topic = app.topic("images", value_type=Image)

page_views = app.Table("page_views", default=int)

logger = logging.getLogger(__name__)


@app.agent(page_view_topic)
async def count_page_views(views):
    async for view in views.group_by(PageView.id):
        page_views[view.id] += 1
        logger.info(f"Event received. Page view Id {view.id}")

        yield view


@app.agent(images_topic)
async def consume_image(events):
    async for event in events:
        logger.info(event)

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
        image = Image(file=file_number, folder=folder_number, png=False, json=False, log="")
        await images_topic.send(value=image)
