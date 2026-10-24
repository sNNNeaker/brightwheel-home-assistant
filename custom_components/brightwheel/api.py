"""Async API client for Brightwheel.

Modified 2026 by sNNNeaker: email/2FA login, new entities.
"""

from __future__ import annotations

import asyncio
from datetime import date
import json
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://schools.mybrightwheel.com/api/v1"
COOKIE_NAME = "_brightwheel_v2"
TIMEOUT = 15

_BASE_HEADERS = {
    "X-Client-Name": "web",
    "X-Client-Version": "225",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin": "https://schools.mybrightwheel.com",
    "Referer": "https://schools.mybrightwheel.com/",
}


class BrightwheelError(Exception):
    """Base error for Brightwheel."""


class BrightwheelAuthError(BrightwheelError):
    """Authentication failed or expired."""


class BrightwheelConnectionError(BrightwheelError):
    """Brightwheel could not be reached."""


class BrightwheelApi:
    """Client for the (unofficial) Brightwheel web API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str | None = None,
        cookie: str | None = None,
        csrf: str | None = None,
        guardian_id: str | None = None,
    ) -> None:
        """Initialize with the shared HA session and optional credentials."""
        self._session = session
        self._token = token
        self._cookie = cookie
        self._csrf = csrf
        self._guardian_id = guardian_id

    def _headers(self, authenticated: bool) -> dict[str, str]:
        headers = dict(_BASE_HEADERS)
        if authenticated:
            if self._token:
                headers["X-Parse-Session-Token"] = self._token
            if self._cookie:
                headers["Cookie"] = f"{COOKIE_NAME}={self._cookie}"
            if self._csrf:
                headers["X-CSRF-Token"] = self._csrf
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        authenticated: bool = True,
        login: bool = False,
    ) -> tuple[dict[str, Any], str | None]:
        """Send a request, return (json body, cookie value if set)."""
        try:
            async with asyncio.timeout(TIMEOUT):
                async with self._session.request(
                    method,
                    f"{BASE_URL}{path}",
                    json=payload,
                    params=params,
                    headers=self._headers(authenticated),
                ) as resp:
                    status = resp.status
                    text = await resp.text()
                    morsel = resp.cookies.get(COOKIE_NAME)
                    cookie = morsel.value if morsel else None
        except TimeoutError as err:
            raise BrightwheelConnectionError("Timeout talking to Brightwheel") from err
        except aiohttp.ClientError as err:
            raise BrightwheelConnectionError("Cannot reach Brightwheel") from err

        if status in (401, 403) or "E1200" in text:
            raise BrightwheelAuthError("Authentication rejected")
        if login and status in (400, 422):
            raise BrightwheelAuthError("Login rejected")
        if status == 429 or status >= 500:
            raise BrightwheelConnectionError(f"Brightwheel unavailable (HTTP {status})")
        if status >= 400:
            raise BrightwheelError(f"Unexpected HTTP status {status}")

        data: dict[str, Any] = {}
        if text:
            try:
                parsed = json.loads(text)
            except ValueError as err:
                raise BrightwheelError("Invalid JSON from Brightwheel") from err
            if isinstance(parsed, dict):
                data = parsed
        return data, cookie

    async def async_start_login(self, email: str, password: str) -> bool:
        """Start login; return True if a 2FA code was emailed."""
        data, _ = await self._request(
            "POST",
            "/sessions/start",
            payload={"user": {"email": email, "password": password}},
            authenticated=False,
            login=True,
        )
        return data.get("2fa_required") is True

    async def async_finish_login(
        self, email: str, password: str, code: str | None
    ) -> dict[str, str | None]:
        """Finish login and return token, cookie, csrf and guardian_id."""
        payload: dict[str, Any] = {"user": {"email": email, "password": password}}
        if code:
            payload["2fa_code"] = code
        data, cookie = await self._request(
            "POST", "/sessions", payload=payload, authenticated=False, login=True
        )
        user = data.get("user")
        guardian_id = user.get("object_id") if isinstance(user, dict) else None
        self._token = data.get("token") or None
        self._cookie = cookie
        self._csrf = data.get("csrf") or None
        if not (self._token or self._cookie):
            raise BrightwheelAuthError("Login returned no credentials")
        self._guardian_id = guardian_id
        return {
            "token": self._token,
            "cookie": self._cookie,
            "csrf": self._csrf,
            "guardian_id": guardian_id,
        }

    async def async_get_guardian_id(self) -> str:
        """Return the guardian id of the logged-in user."""
        guardian_id = None
        try:
            data, _ = await self._request("GET", "/users/me")
            guardian_id = data.get("object_id")
        except BrightwheelAuthError:
            raise
        except BrightwheelError:
            guardian_id = None
        guardian_id = guardian_id or self._guardian_id
        if not guardian_id:
            raise BrightwheelError("Guardian id unknown")
        self._guardian_id = guardian_id
        return guardian_id

    async def async_get_students(self) -> list[dict[str, Any]]:
        """Return the student dicts of this guardian."""
        guardian_id = await self.async_get_guardian_id()
        data, _ = await self._request("GET", f"/guardians/{guardian_id}/students")
        students: list[dict[str, Any]] = []
        for item in data.get("students") or []:
            if not isinstance(item, dict):
                continue
            student = item.get("student", item)
            if isinstance(student, dict) and student.get("object_id"):
                students.append(student)
        return students

    async def async_get_activities(
        self, student_id: str, start: date, end_exclusive: date
    ) -> list[dict[str, Any]]:
        """Return activities from start up to (excluding) end_exclusive."""
        data, _ = await self._request(
            "GET",
            f"/students/{student_id}/activities",
            params={
                "page": 0,
                "page_size": 100,
                "start_date": start.isoformat(),
                "end_date": end_exclusive.isoformat(),
            },
        )
        return [a for a in data.get("activities") or [] if isinstance(a, dict)]
