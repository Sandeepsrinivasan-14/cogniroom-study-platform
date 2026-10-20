"""Live metrics must round-trip through Redis as JSON (never pickle) and ignore bad payloads."""

import json
import pickle

from src.redis_service import RedisService


class FakeRedis:
    def __init__(self):
        self.hashes = {}

    def hset(self, key, field, value):
        self.hashes.setdefault(key, {})[field.encode()] = value

    def expire(self, key, seconds):
        pass

    def hgetall(self, key):
        return self.hashes.get(key, {})


def make_service():
    svc = RedisService.__new__(RedisService)  # skip connecting to a real Redis
    svc.client = FakeRedis()
    return svc


def test_metrics_round_trip():
    svc = make_service()
    svc.set_live_metrics(1, 7, 0.42, 1700000000.0)
    assert svc.get_live_metrics(1) == {7: {"load_score": 0.42, "ts": 1700000000.0}}


def test_stored_value_is_json_not_pickle():
    svc = make_service()
    svc.set_live_metrics(1, 7, 0.5, 1.0)
    raw = svc.client.hashes["room:1:metrics"][b"7"]
    assert json.loads(raw) == {"load_score": 0.5, "ts": 1.0}


def test_pickled_payload_is_ignored_not_executed():
    svc = make_service()

    class Boom:
        def __reduce__(self):
            return (exit, (1,))  # would terminate the process if ever unpickled

    svc.client.hashes["room:1:metrics"] = {b"9": pickle.dumps(Boom())}
    assert svc.get_live_metrics(1) == {}


def test_no_client_is_a_noop():
    svc = make_service()
    svc.client = None
    svc.set_live_metrics(1, 1, 0.1, 1.0)
    assert svc.get_live_metrics(1) == {}
