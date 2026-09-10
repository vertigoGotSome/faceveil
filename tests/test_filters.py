import numpy as np
import pytest

from faceveil.filters import FilterMode, Settings, anonymize


@pytest.fixture
def frame():
    return np.random.default_rng(42).integers(0, 256, (100, 120, 3), dtype=np.uint8)


@pytest.mark.parametrize("mode", list(FilterMode))
def test_filters_change_only_face_region_without_mutating_input(frame, mode):
    original = frame.copy()
    result = anonymize(frame, [(30, 20, 40, 50)], Settings(mode=mode, cover_all=False, margin=0))
    assert np.array_equal(frame, original)
    assert np.array_equal(result[:20], frame[:20])
    assert np.array_equal(result[70:], frame[70:])
    assert np.array_equal(result[:, :30], frame[:, :30])
    assert np.array_equal(result[:, 70:], frame[:, 70:])
    assert not np.array_equal(result[20:70, 30:70], frame[20:70, 30:70])
    assert result.dtype == frame.dtype
    assert result.shape == frame.shape


def test_complete_cover_is_independent_of_detection(frame):
    assert not anonymize(frame, [], Settings()).any()
    assert not anonymize(frame, [(10, 10, 20, 20)], Settings()).any()


def test_margin_and_clipping(frame):
    settings = Settings(mode=FilterMode.SOLID, cover_all=False, margin=0.5)
    result = anonymize(frame, [(-5, -5, 20, 20)], settings)
    assert not result[:25, :25].any()
    assert np.array_equal(result[25:], frame[25:])


def test_missing_faces_leaves_frame_unchanged_in_experimental_mode(frame):
    result = anonymize(frame, [], Settings(cover_all=False))
    assert np.array_equal(result, frame)
    assert result is not frame


@pytest.mark.parametrize("box", [(200, 200, 10, 10), (0, 0, 0, 4), (-100, -100, 5, 5)])
def test_invalid_or_outside_boxes_are_ignored(frame, box):
    assert np.array_equal(anonymize(frame, [box], Settings(cover_all=False)), frame)


@pytest.mark.parametrize("kwargs", [{"strength": 0}, {"strength": 81}, {"margin": -1}])
def test_settings_reject_invalid_values(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


@pytest.mark.parametrize("mode", list(FilterMode))
def test_tiny_region(frame, mode):
    result = anonymize(frame, [(0, 0, 1, 1)], Settings(mode=mode, cover_all=False, margin=0))
    assert result.shape == frame.shape


def test_pixelation_produces_constant_blocks(frame):
    result = anonymize(
        frame,
        [(0, 0, 120, 100)],
        Settings(cover_all=False, margin=0, strength=20),
    )
    assert np.all(result[:20, :20] == result[0, 0])
