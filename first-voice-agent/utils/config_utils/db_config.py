"""Utilty to connect to databases(Upstash) from where our agents fetch interview session data,coding-questions,company-prompts and so on"""
from utils.config_utils.config_loader import get_config
from utils.monitoring_utils.logging import get_logger

try:
    from upstash_redis import Redis
except ModuleNotFoundError:
    Redis = None

logger = get_logger("db-config")

redis = None
if Redis is not None:
    redis_url = get_config("UPSTASH_REDIS_URL", required=False)
    redis_token = get_config("UPSTASH_REDIS_TOKEN", required=False)
    if redis_url and redis_token:
        redis = Redis(url=redis_url, token=redis_token)
