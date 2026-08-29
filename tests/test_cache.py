
import time

from app.cache import TTLCache


def test_cache_set_and_get():
    cache = TTLCache(ttl=10)

    cache.set("key", "value")

    assert cache.get("key") == "value"


def test_cache_misses_for_unknown_key():
    cache = TTLCache(ttl=10)

    assert cache.get("missing") is None


def test_cache_expires_value():
    cache = TTLCache(ttl=0.05)

    cache.set("key", "value")

    assert cache.get("key") == "value"

    time.sleep(0.1)

    assert cache.get("key") is None


def test_cache_delete():
    cache = TTLCache(ttl=10)

    cache.set("key", "value")
    cache.delete("key")

    assert cache.get("key") is None


def test_cache_clear():
    cache = TTLCache(ttl=10)

    cache.set("key-1", "value-1")
    cache.set("key-2", "value-2")

    cache.clear()

    assert cache.size() == 0
