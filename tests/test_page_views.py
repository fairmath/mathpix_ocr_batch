import os

import pytest

from page_views.agents import get_filename, image_converter
from page_views.models import Image


def get_test_image():
    return Image(file=210, folder=1, png=False, json=False)


@pytest.mark.asyncio()
async def test_png_path(test_app):
    filename = await get_filename(get_test_image())
    assert filename.index("png") > 0


@pytest.mark.asyncio()
async def test_json_path(test_app):
    filename = await get_filename(get_test_image(), "json")
    assert filename.index("json") > 0


@pytest.mark.asyncio()
async def test_get_filename(test_app):
    async with image_converter.test_context() as agent:
        await agent.put(get_test_image())
        filename = await get_filename(get_test_image())
        assert os.path.isfile(filename)
