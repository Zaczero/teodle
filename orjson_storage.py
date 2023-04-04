import orjson
from tinydb.storages import JSONStorage


class ORJSONStorage(JSONStorage):
    def _serialize(self, obj) -> str:
        return orjson.dumps(obj).decode()  # option=orjson.OPT_INDENT_2

    def _deserialize(self, data):
        return orjson.loads(data)
