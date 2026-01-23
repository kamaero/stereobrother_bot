"""
Basic unit tests for StereoBrother Bot
"""

import pytest


def test_basic():
    """Basic test to ensure tests can run"""
    assert True


def test_math():
    """Simple math test"""
    assert 1 + 1 == 2


class TestBasicClass:
    """Test class example"""

    def test_class_method(self):
        """Test method in class"""
        assert "hello".upper() == "HELLO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
