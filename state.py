_seen_ids: set[str] = set()


def init_seen(entries: list[dict]):
    """Silently mark all current entries as seen on startup — no notifications sent."""
    for entry in entries:
        pre_user_id = str(entry.get("Pre User ID", ""))
        if pre_user_id:
            _seen_ids.add(pre_user_id)


def is_seen(pre_user_id: str) -> bool:
    return pre_user_id in _seen_ids


def mark_seen(pre_user_id: str):
    _seen_ids.add(pre_user_id)
