import pytest

from src.ml.ml_service import MLService


@pytest.fixture
def svc():
    s = MLService.__new__(MLService)  # skip loading model files; test the fallback logic directly
    return s


@pytest.mark.parametrize(
    "features,expected",
    [
        ({}, "low"),
        ({"late_night": 3, "duration_minutes": 200, "avg_load": 0.9, "load_variance": 0.2}, "high"),
        ({"late_night": 3, "duration_minutes": 200}, "medium"),
        ({"late_night": 2, "duration_minutes": 180, "avg_load": 0.7}, "low"),  # thresholds are strict ">"
    ],
)
def test_heuristic_burnout(svc, features, expected):
    assert svc._heuristic_burnout(features) == expected


@pytest.mark.parametrize(
    "features,expected",
    [
        ({"load_variance": 0.5}, "C"),
        ({"load_variance": 0.01}, "B"),
        ({"load_variance": 0.01, "has_quiz": 1, "quiz_score": 100}, "A"),
        ({"load_variance": 0.5, "has_quiz": 1, "quiz_score": 0}, "C"),
    ],
)
def test_heuristic_performance(svc, features, expected):
    assert svc._heuristic_performance(features) == expected


def test_predict_falls_back_to_heuristic_when_no_model(svc):
    svc.models_loaded = False
    svc.burnout_model = None
    svc.performance_model = None
    level, conf, source = svc.predict_burnout({"late_night": 3, "duration_minutes": 200, "avg_load": 0.9, "load_variance": 0.2})
    assert (level, conf, source) == ("high", 0.5, "heuristic")
    grade, conf, source = svc.predict_performance({"load_variance": 0.01})
    assert (grade, conf, source) == ("B", 0.5, "heuristic")


def test_real_service_always_returns_a_valid_prediction():
    """With the pinned libs the committed models load; otherwise it must degrade to the heuristic."""
    s = MLService()
    sample = {"start_hour": 14, "duration_minutes": 90, "late_night": 0, "avg_load": 0.5, "max_load": 0.7,
              "load_variance": 0.02, "has_quiz": 1, "message_count": 5, "whiteboard_actions": 3, "quiz_score": 60}
    level, conf, source = s.predict_burnout(sample)
    assert level in {"low", "medium", "high"}
    assert 0 <= conf <= 1
    assert source in {"ml_model", "heuristic"}
    grade, conf, source = s.predict_performance(sample)
    assert grade in {"A", "B", "C", "D"}
    assert source in {"ml_model", "heuristic"}
