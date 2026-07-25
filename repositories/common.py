import json


def decode_payload(row):
    return json.loads(row["payload_json"])
