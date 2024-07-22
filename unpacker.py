import json


class Unpacker:

    def __init__(self, layout: str):
        self.layout_dict = json.loads(layout)

    def to_json(self) -> str:
        pass

    def __getitem__(self, item):
        pass
