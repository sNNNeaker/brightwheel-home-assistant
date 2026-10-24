"""Data model and pure helpers for Brightwheel activities.

Added 2026 by sNNNeaker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from .const import MAX_TODAY_ACTIVITIES

CHECKIN = "ac_checkin"

EVENT_TYPES = ["check_in", "check_out", "photo", "video", "note", "other"]


@dataclass
class StudentData:
    """Activities of one student."""

    student_id: str
    name: str
    activities: list[dict[str, Any]] = field(default_factory=list)
    school_id: str | None = None
    school_name: str | None = None
    enrollment_status: str | None = None


def activity_time(activity: dict[str, Any]) -> datetime | None:
    """Return the local event time of an activity."""
    for key in ("event_date", "created_at"):
        value = activity.get(key)
        if isinstance(value, str) and (parsed := dt_util.parse_datetime(value)):
            return dt_util.as_local(parsed)
    return None


def sort_activities(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return activities newest first."""
    floor = dt_util.utc_from_timestamp(0)
    return sorted(
        activities,
        key=lambda a: activity_time(a) or floor,
        reverse=True,
    )


def actor_name(activity: dict[str, Any]) -> str | None:
    """Return the full name of the activity's actor."""
    actor = activity.get("actor")
    if not isinstance(actor, dict):
        return None
    name = f"{actor.get('first_name') or ''} {actor.get('last_name') or ''}".strip()
    return name or None


def checkin_state(activity: dict[str, Any]) -> bool | None:
    """Return True if checked in, False if checked out, None if unknown."""
    state = activity.get("state")
    if state is not None and str(state) in ("1", "2"):
        return str(state) == "1"
    if isinstance(activity.get("checked_in"), bool):
        return activity["checked_in"]
    blob = activity.get("details_blob")
    if isinstance(blob, dict):
        if isinstance(blob.get("checked_in"), bool):
            return blob["checked_in"]
        if blob.get("state") is not None and str(blob["state"]) in ("1", "2"):
            return str(blob["state"]) == "1"
    return None


def checkin_events(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return check-in/out activities, order preserved."""
    return [a for a in activities if a.get("action_type") == CHECKIN]


def last_check(
    activities: list[dict[str, Any]], state: bool
) -> tuple[datetime | None, str | None]:
    """Return (time, actor) of the newest check-in (True) or check-out (False)."""
    for activity in checkin_events(activities):
        if checkin_state(activity) is state:
            return activity_time(activity), actor_name(activity)
    return None, None


def is_checked_in_today(activities: list[dict[str, Any]], now: datetime) -> bool | None:
    """Return True if the newest check event of today is a check-in."""
    today = dt_util.as_local(now).date()
    for activity in checkin_events(activities):
        when = activity_time(activity)
        if when is not None and when.date() == today:
            return checkin_state(activity)
    return False


def friendly_type(activity: dict[str, Any]) -> str:
    """Return a readable activity type."""
    action = str(activity.get("action_type") or "")
    if action == CHECKIN:
        return "Check-out" if checkin_state(activity) is False else "Check-in"
    names = {
        "ac_photo": "Photo",
        "ac_video": "Video",
        "ac_note": "Note",
        "ac_kudo": "Kudos",
    }
    if action in names:
        return names[action]
    cleaned = action.removeprefix("ac_").replace("_", " ").strip()
    return cleaned.title() if cleaned else "Activity"


def event_type(activity: dict[str, Any]) -> str:
    """Return the event entity type of an activity."""
    action = activity.get("action_type")
    if action == CHECKIN:
        state = checkin_state(activity)
        if state is None:
            return "other"
        return "check_in" if state else "check_out"
    return {"ac_photo": "photo", "ac_video": "video", "ac_note": "note"}.get(
        str(action), "other"
    )


def image_url(activity: dict[str, Any]) -> str | None:
    """Return the full-size image url of an activity, if any."""
    media = activity.get("media")
    if isinstance(media, dict):
        return media.get("image_url") or None
    return None


def today_activities(
    activities: list[dict[str, Any]], now: datetime
) -> list[dict[str, Any]]:
    """Return today's activities (max 30), newest first."""
    today = dt_util.as_local(now).date()
    result: list[dict[str, Any]] = []
    for activity in activities:
        when = activity_time(activity)
        if when is None or when.date() != today:
            continue
        result.append(
            {
                "time": when.isoformat(),
                "type": friendly_type(activity),
                "note": activity.get("note"),
                "by": actor_name(activity),
            }
        )
        if len(result) >= MAX_TODAY_ACTIVITIES:
            break
    return result


def latest_photo(
    activities: list[dict[str, Any]],
) -> tuple[str | None, datetime | None]:
    """Return (url, time) of the newest photo."""
    for activity in activities:
        if activity.get("action_type") == "ac_photo" and (url := image_url(activity)):
            return url, activity_time(activity)
    return None, None
