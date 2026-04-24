import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def load_json(path, default, logger):
    if Path(path).exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_stats_day_key(stats_tz: str):
    try:
        return datetime.now(ZoneInfo(stats_tz)).date().isoformat()
    except Exception:
        return datetime.utcnow().date().isoformat()


def increment_metrics(target: dict, metrics: dict):
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            target[key] = target.get(key, 0) + value


def load_stats(stats_file: str, logger, extra_defaults: dict | None = None):
    data = load_json(stats_file, {}, logger)
    if not isinstance(data, dict):
        data = {}
    data.setdefault("schema_version", 2)
    data.setdefault("daily", {})
    data.setdefault("lifetime", {})
    if extra_defaults:
        for key, value in extra_defaults.items():
            data.setdefault(key, value)
    return data


def record_run_stats(
    *,
    stats_file: str,
    stats_tz: str,
    metrics: dict,
    logger,
    keep_days: int = 45,
    extra_defaults: dict | None = None,
):
    stats = load_stats(stats_file, logger, extra_defaults=extra_defaults)
    day_key = get_stats_day_key(stats_tz)
    daily = stats["daily"].setdefault(day_key, {})
    lifetime = stats["lifetime"]

    increment_metrics(daily, metrics)
    increment_metrics(lifetime, metrics)

    if metrics.get("posted", 0) > 0:
        stats["total_posts"] = stats.get("total_posts", 0) + int(metrics["posted"])

    try:
        keys_sorted = sorted(stats["daily"].keys())
        while len(keys_sorted) > keep_days:
            oldest = keys_sorted.pop(0)
            stats["daily"].pop(oldest, None)
    except Exception:
        pass

    save_json(stats_file, stats)
