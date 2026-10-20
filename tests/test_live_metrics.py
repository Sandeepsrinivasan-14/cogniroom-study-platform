from datetime import datetime

from src import live_metrics


class FakeService:
    def __init__(self, data):
        self.data = data

    def get_live_metrics(self, room_id):
        return self.data


def test_empty_room(monkeypatch):
    monkeypatch.setattr(live_metrics, "redis_service", FakeService({}))
    out = live_metrics.get_room_live_metrics(5)
    assert out == {"room_id": 5, "users": [], "group_avg_load": None, "total_users": 0, "last_updated": None}


def test_group_average_and_latest_timestamp(monkeypatch):
    data = {1: {"load_score": 0.2, "ts": 1_700_000_000.0}, 2: {"load_score": 0.6, "ts": 1_700_000_100.0}}
    monkeypatch.setattr(live_metrics, "redis_service", FakeService(data))
    out = live_metrics.get_room_live_metrics(9)
    assert out["total_users"] == 2
    assert out["group_avg_load"] == 0.4
    assert out["last_updated"] == datetime.fromtimestamp(1_700_000_100.0).isoformat()
    assert {u["user_id"] for u in out["users"]} == {1, 2}
