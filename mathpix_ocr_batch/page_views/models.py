import faust


class PageView(faust.Record):
    id: str
    user: str


class Image(faust.Record):
    def __abstract_init__(self) -> None:
        pass

    folder: int
    file: int
    png: bool
    json: bool
    log: str
