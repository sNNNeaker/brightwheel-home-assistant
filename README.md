<p align="center">
  <!-- Plain <img> with an absolute URL: the HACS/Marketplace README renderer
       doesn't support <picture>/<source>, and relative paths only resolve on
       GitHub. -->
  <img alt="Brightwheel" src="https://raw.githubusercontent.com/sNNNeaker/brightwheel-home-assistant/master/custom_components/brightwheel/brand/logo%402x.png" width="420">
</p>

# Brightwheel for Home Assistant

A Home Assistant custom integration for [Brightwheel](https://mybrightwheel.com/), the daycare app that shares check-ins, photos and notes with parents.

> Unofficial. Not affiliated with or endorsed by Brightwheel. It uses the same web API as the Brightwheel website, which is undocumented and may change or break at any time.

## Entities (per child)

| Entity | Description |
|--------|-------------|
| `binary_sensor` Checked in | On if the newest check-in/out event today is a check-in; attributes `school`, `school_id`, `enrollment_status` |
| `sensor` Last check-in / Last check-out | Timestamp, attribute `by` |
| `sensor` Latest activity | Type of the newest activity; attributes `time`, `note`, `by`, `today` (today's activities) |
| `image` Latest photo | Newest photo from the last 14 days |
| `event` Activity | Fires for each new activity: `check_in`, `check_out`, `photo`, `video`, `note`, `other` (attributes `time`, `note`, `by`; the photo itself is only available through the Latest photo image entity) |

Each child is a device; its model shows the school (name from the guardian's school invites if Brightwheel returns it, else the school id) and the enrollment status when it is not "Active". A child enrolled at two schools appears twice; disable the device you don't need.

All children of the account are added, one device each. Data is polled every 5 minutes.

## Installation

Submitted to the HACS community catalog; until it is listed, add it as a **custom repository**. Once listed, search for **Brightwheel** instead and skip the custom repository step.

### Via the Marketplace (Home Assistant 2026.11 and newer)

From 2026.11 HACS is built into Home Assistant as the **Marketplace** (Settings → Marketplace).

1. Add `https://github.com/sNNNeaker/brightwheel-home-assistant` as a custom repository of type **Integration**. Custom repositories are fetched through the GitHub API, so the Marketplace asks you to connect a GitHub account the first time (catalog entries don't need one).
2. Download **Brightwheel**. No restart is needed on first install.
3. Settings → Devices & services → Add integration → **Brightwheel** (see Setup), or use
   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=brightwheel)

Updates show up under Settings → Updates; installing an update needs a restart, which the Marketplace offers via a repair.

### Via HACS (Home Assistant 2026.10 and older)

1. HACS, ⋮ menu, **Custom repositories**; add `https://github.com/sNNNeaker/brightwheel-home-assistant`, category **Integration**
2. Install **Brightwheel** and restart Home Assistant

### Manual

Copy `custom_components/brightwheel/` to `config/custom_components/brightwheel/` and restart Home Assistant.

## Setup

1. **Settings, Devices & services, Add integration, Brightwheel**
2. Enter your Brightwheel email and password
3. Brightwheel emails you a code; enter it

Your password is not stored, only the session credentials returned by Brightwheel.

## Re-authentication

When the session expires, Home Assistant asks you to sign in again. Enter your password and the newly emailed code; a new code is needed for each login.

## Credits and license

Based on [pmartindev/brightwheel-home-assistant](https://github.com/pmartindev/brightwheel-home-assistant). Licensed under Apache-2.0, see [LICENSE](LICENSE).
