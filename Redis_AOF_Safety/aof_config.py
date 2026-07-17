"""
Redis AOF and crash safety configurations.
This module enforces server-side settings on the Redis instance to prevent data loss.
"""

import logging
from redis import Redis

logger = logging.getLogger(__name__)

def configure_redis_mitigations(redis_client: Redis):
    """
    Enforces Redis server-side configurations for crash safety:
    1. appendonly = yes (Enable AOF logging)
    2. appendfsync = everysec (Write to disk every second)
    3. auto-aof-rewrite-percentage = 100
    4. auto-aof-rewrite-min-size = 64mb (Configure rewriting log bounds)
    5. maxmemory-policy = noeviction (Prevent key evictions when memory is full)
    """
    try:
        # 1. Enable AOF
        redis_client.config_set("appendonly", "yes")
        # 2. Enforce fsync every second
        redis_client.config_set("appendfsync", "everysec")
        # 3. Configure auto-rewrite percentage
        redis_client.config_set("auto-aof-rewrite-percentage", "100")
        # 4. Configure auto-rewrite min size
        redis_client.config_set("auto-aof-rewrite-min-size", "67108864")  # 64MB in bytes
        # 5. Set maxmemory-policy to noeviction
        redis_client.config_set("maxmemory-policy", "noeviction")
        print("[OK] Redis mitigation configurations applied successfully (AOF enabled, auto-rewrite set, noeviction set)")
    except Exception as e:
        logger.warning(f"Could not apply Redis server configurations: {e}. Ensure Redis has admin CONFIG permissions.")
