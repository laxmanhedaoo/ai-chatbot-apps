"""Utility helpers for loading configuration from env vars or Upstash."""
import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from utils.config_utils.env_loader import get_env_var

try:
    from upstash_redis import Redis
except ModuleNotFoundError:
    Redis = None

logger = logging.getLogger("config-loader")

redis = None
if Redis is not None:
    config_url = get_env_var("UPSTASH_CONFIG_REDIS_URL", required=False)
    config_token = get_env_var("UPSTASH_CONFIG_REDIS_TOKEN", required=False)
    if config_url and config_token:
        redis = Redis(url=config_url, token=config_token)

# -------------------------------Load environment variables profile from .env file-------------------------------
load_dotenv()

# -------------------------------Get Env value for the profile -------------------------------
def get_profile_name() -> str:
    profile_name = get_env_var("PROFILE")
    if not profile_name:
        raise ValueError("Missing PROFILE value in .env")
    return profile_name

# -------------------------------Select the Upstash key for the profile -------------------------------
def select_upstash_key(env_name: str) -> str:
    return f"config:env:{env_name}"

# -------------------------------Fetch the correct profile from Upstash-------------------------------
def fetch_config_from_redis(redis_key: str) -> str:
    if redis is None:
        raise ValueError("Upstash config store is unavailable")

    response = redis.get(redis_key)
    if not response:
        raise ValueError(f"No config found in Redis for key: '{redis_key}'")
    return response

# -------------------------------Parse the JSON received from Upstash-------------------------------
def parse_config_json(response: str, redis_key: str) -> Dict[str, Any]:
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in Redis for key '{redis_key}': {e}")

# -------------------------------Flatten the response JSON from Upstash-------------------------------
def flatten_config_section(items: Any) -> Dict[str, Any]:
    flat_config: Dict[str, Any] = {}

    if isinstance(items, dict):
        for key, value in items.items():
            if value is not None:
                flat_config[key] = json.dumps(value) if isinstance(value, (dict, list)) else value
        return flat_config

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            key = item.get("key")
            value = item.get("value")
            if key is not None and value is not None:
                flat_config[key] = json.dumps(value) if isinstance(value, (dict, list)) else value

    return flat_config


def flatten_config(config_json: Dict[str, Any]) -> Dict[str, Any]:
    flat_config = {}

    if not isinstance(config_json, dict):
        return flat_config

    config_section = config_json.get("config")
    if isinstance(config_section, (dict, list)):
        flat_config.update(flatten_config_section(config_section))
        return flat_config

    for items in config_json.values():
        flat_config.update(flatten_config_section(items))

    return flat_config

# -------------------------------Use the profile and load env variable from Upstash-------------------------------
@lru_cache(maxsize=1)
def load_config_from_env() -> Dict[str, Any]:
    profile_name = get_profile_name()
    redis_key = select_upstash_key(profile_name)
    raw_config = fetch_config_from_redis(redis_key)
    config_json = parse_config_json(raw_config, redis_key)
    flat_config = flatten_config(config_json)
    flat_config["PROFILE"] = profile_name
    return flat_config

# -------------------------------Get env variable value from Upstash config-------------------------------
def get_config(key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value

    if redis is None:
        value = default
    else:
        try:
            config = load_config_from_env()
            value = config.get(key, default)
        except Exception as exc:
            logger.debug("Falling back to default for %s because remote config is unavailable: %s", key, exc)
            value = default

    if required and value is None:
        raise ValueError(f"Missing required config key: {key}")

    return value
