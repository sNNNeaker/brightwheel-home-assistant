# Brightwheel for Home Assistant

A Home Assistant custom integration for [Brightwheel](https://mybrightwheel.com/), the daycare app that shares check-ins, photos and notes with parents.

> Unofficial. Not affiliated with or endorsed by Brightwheel. It uses the same web API as the Brightwheel website, which is undocumented and may change or break at any time.

## Entities (per child)

| Entity | Description |
|--------|-------------|
| `binary_sensor` Checked in | On if the newest check-in/out event today is a check-in |
| `sensor` Last check-in / Last check-out | Timestamp, attribute `by` |
| `sensor` Latest activity | Type of the newest activity; attributes `time`, `note`, `by`, `today` (today's activities) |
| `image` Latest photo | Newest photo from the last 14 days |
| `event` Activity | Fires for each new activity: `check_in`, `check_out`, `photo`, `video`, `note`, `other` (attributes `time`, `note`, `by`, `image_url`) |

All children of the account are added, one device each. Data is polled every 5 minutes.

## Installation

1. HACS, three dots, **Custom repositories**
2. Add `https://github.com/sNNNeaker/brightwheel-home-assistant`, category **Integration**
3. Install **Brightwheel** and restart Home Assistant

## Setup

1. **Settings, Devices & services, Add integration, Brightwheel**
2. Enter your Brightwheel email and password
3. Brightwheel emails you a code; enter it

Your password is not stored, only the session credentials returned by Brightwheel.

## Re-authentication

When the session expires, Home Assistant asks you to sign in again. Enter your password and the newly emailed code; a new code is needed for each login.

## Credits and license

Based on [pmartindev/brightwheel-home-assistant](https://github.com/pmartindev/brightwheel-home-assistant). Licensed under Apache-2.0, see [LICENSE](LICENSE).
