import pytest
from lib import get_merged_video_filename, remove_brackets


def test_get_merged_video_filename():
    assert get_merged_video_filename("hello world") == "hello_world"
    assert get_merged_video_filename("this is a test") == "this_is_a_test"
    assert get_merged_video_filename("single") == "single"
    assert get_merged_video_filename("") == ""
    assert get_merged_video_filename("hello   world") == "hello___world"
    assert get_merged_video_filename("  leading and trailing  ") == "__leading_and_trailing__"
    assert get_merged_video_filename("special_chars! @# $%^") == "special_chars!_@#_$%^"


def test_remove_brackets():
    assert remove_brackets("Hello World (2024)") == "Hello World"
    assert remove_brackets("Hello World") == "Hello World"
    assert remove_brackets("Test (2024) (extra)") == "Test"
    assert remove_brackets("(2024) Hello World") == ""
    assert remove_brackets("Hello (2024) World") == "Hello"
    assert remove_brackets("(2024)") == ""
    assert remove_brackets("") == ""
    assert remove_brackets("   ") == ""
    assert remove_brackets("Nested (inside (another))") == "Nested"
    assert remove_brackets("Special!@# (remove me)") == "Special!@#"
