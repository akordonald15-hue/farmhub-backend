import logging
from datetime import datetime, timezone


def get_client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_event(logger_name, request, action, result, user=None, extra=None, level="info"):
    logger = logging.getLogger(logger_name)
    user_id = getattr(user, "id", None)
    if user_id is None and request is not None:
        user_id = getattr(getattr(request, "user", None), "id", None)

    payload = {
        "action": action,
        "result": result,
        "user_id": user_id,
        "ip": get_client_ip(request),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)

    log_method = getattr(logger, level, logger.info)
    log_method("event", extra=payload)
