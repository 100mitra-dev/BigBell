from datetime import datetime, date


def today_str() -> str:
    return date.today().isoformat()


def days_until(target_date: str) -> int:
    if not target_date:
        return 0
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    delta = target - date.today()
    return delta.days
