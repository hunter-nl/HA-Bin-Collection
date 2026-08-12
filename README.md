# HA Bin Collection

<img src="brand/logo.svg" alt="HA Bin Collection" style="max-width: 600px;">

[![Release][release-badge]][release-url]
[![Validate][validate-badge]][validate-url]
[![CI][ci-badge]][ci-url]
[![License][license-badge]][license-url]
[![Home-Assistant][ha-badge]][ha-url]
[![HACS Custom][hacs-badge]][hacs-url]

[release-badge]: https://img.shields.io/github/v/release/hunter-nl/HA-Bin-Collection?include_prereleases&sort=semver&display_name=release&label=Release
[release-url]: https://github.com/hunter-nl/HA-Bin-Collection/releases
[validate-badge]: https://img.shields.io/github/actions/workflow/status/hunter-nl/HA-Bin-Collection/validate.yaml?label=Validate
[validate-url]: https://github.com/hunter-nl/HA-Bin-Collection/actions/workflows/validate.yaml
[ci-badge]: https://img.shields.io/github/actions/workflow/status/hunter-nl/HA-Bin-Collection/ci.yaml?label=CI
[ci-url]: https://github.com/hunter-nl/HA-Bin-Collection/actions/workflows/ci.yaml
[license-badge]: https://img.shields.io/github/license/hunter-nl/HA-Bin-Collection?color=blue
[license-url]: https://github.com/hunter-nl/HA-Bin-Collection/blob/main/LICENSE
[ha-badge]: https://img.shields.io/badge/Home--Assistant-2026.7.0%2B-green?logo=homeassistant
[ha-url]: https://www.home-assistant.io
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5?logo=homeassistantcommunitystore&logoColor=white
[hacs-url]: https://www.hacs.xyz/docs/faq/custom_repositories/

HA Bin Collection is a Home Assistant custom integration for Dutch waste collection calendars. Version `0.0.1-alpha` supports **MijnAfvalwijzer** and **ACV** (Ximmio), with a provider design intended for further collectors.

It gives every configured address its own collection calendar, consistent Rest/Papier/GFT/PMD date sensors, provider notices, day-before reminders, and a compact Lovelace card.

## Requirements

- Home Assistant 2026.7.0 or newer.

## Install

### HACS (Recommended)

1. Open **HACS** → **⋮** → **Custom repositories**.
2. Add `hunter-nl/HA-Bin-Collection` as an **Integration** repository.
3. Find **HA Bin Collection**, download it, and restart Home Assistant.
4. Add **HA Bin Collection** in **Settings → Devices & services**.

### Manual

1. Copy `custom_components/ha_bin_collection` to `/config/custom_components/ha_bin_collection`.
2. Restart Home Assistant, then add **HA Bin Collection** in **Settings → Devices & services**. Each address is a separate integration entry.

The setup flow asks for provider, postcode, house number, and optional addition. Its options page controls the refresh period (six hours by default) and the day-before reminder (20:00 local time by default).

## Upgrade

### HACS

HACS checks [hunter-nl/HA-Bin-Collection](https://github.com/hunter-nl/HA-Bin-Collection) for published releases. Before upgrading, create a Home Assistant backup, read the release notes, download the release, and restart Home Assistant.

### Manual

1. Create a Home Assistant backup.
2. Replace `/config/custom_components/ha_bin_collection` with the `custom_components/ha_bin_collection` directory from the desired [GitHub release](https://github.com/hunter-nl/HA-Bin-Collection/releases).
3. Restart Home Assistant.

## Entities

For each address HA Bin Collection creates an all-collections calendar plus these stable sensors:

- Rest, Papier, GFT and PMD: the next pickup date for the category.
- Overview: the next pickup date and `collections`/`notices` attributes used by the card.
- Collector notices: the active notice count and full notice records.

Additional provider categories remain available in the Overview data instead of being silently discarded.

## Dashboard card

For Home Assistant's standard storage-mode dashboards, HA Bin Collection automatically adds its bundled card as a JavaScript module resource. Then use the overview entity created for the address:

```yaml
type: custom:ha-bin-collection-card
entity: sensor.ha_bin_collection_home_overview
```

The card shows the next pickups using Rest (grey), Papier (light blue), GFT (green), and PMD (orange), together with collector notices.

If you use Lovelace `resource_mode: yaml`, Home Assistant deliberately keeps resources in YAML. Add this resource to your Lovelace configuration instead:

```yaml
resources:
  - url: /ha_bin_collection/ha-bin-collection-card.js?v=0.0.1-alpha
    type: module
```

## Notifications and automations

New or changed collector notices and each scheduled reminder create a persistent Home Assistant notification. They also fire events, so users choose their own `notify` service rather than giving this integration device credentials:

- `ha_bin_collection.provider_notice`: `entry_id`, `title`, `body`
- `ha_bin_collection.collection_reminder`: `entry_id`, `date`, `waste_types`, `message`

Example mobile notification automation:

```yaml
alias: HA Bin Collection reminder to phone
triggers:
  - trigger: event
    event_type: ha_bin_collection.collection_reminder
actions:
  - action: notify.mobile_app_my_phone
    data:
      title: Bin Collection
      message: "{{ trigger.event.data.message }}"
```

## Troubleshooting

Enable `custom_components.ha_bin_collection: debug` in the logger configuration, refresh the integration entry, and include the provider and a redacted address when reporting an issue.

## Support

- [GitHub Issues](https://github.com/hunter-nl/HA-Bin-Collection/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>
