"""Constants for the Brightwheel integration.

Modified 2026 by sNNNeaker: email/2FA login, new entities.
"""

from datetime import timedelta

DOMAIN = "brightwheel"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_CODE = "code"
CONF_TOKEN = "token"
CONF_COOKIE = "cookie"
CONF_CSRF = "csrf"
CONF_GUARDIAN_ID = "guardian_id"

SCAN_INTERVAL = timedelta(minutes=5)
HISTORY_DAYS = 14
MAX_TODAY_ACTIVITIES = 30
