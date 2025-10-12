import pytest


def calculate_average(numbers):
    if not numbers:
        raise ValueError("empty sequence")
    total = 0
    count = 0
    for item in numbers:
        if not isinstance(item, (int, float)):
            raise TypeError("non-numeric value")
        total += item
        count += 1
    return total / count


def test_avg_basic():
    assert calculate_average([1, 2, 3]) == 2


def test_avg_float():
    assert calculate_average([1, 2]) == 1.5


def test_avg_empty_raises():
    with pytest.raises(ValueError):
        calculate_average([])


def test_avg_non_numeric_raises():
    with pytest.raises(TypeError):
        calculate_average([1, "x"])
