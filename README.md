# Pentair Water Softener - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant integration for Pentair water softeners that use the Erie Connect cloud platform.

> **Note:** This integration was originally developed for Erie IQSoft devices but works with any water softener using the Erie Connect platform, including Pentair devices.

## Features

- 📊 Total water consumption monitoring
- 🔄 Regeneration tracking (last regeneration, total count)
- 🛠️ Maintenance date tracking
- 💧 Water flow sensor
- ⚠️ Warning notifications
- 🧂 Low salt level detection

## Requirements

- Home Assistant 2024.1.0 or newer
- An Erie Connect compatible water softener (Pentair, Erie IQSoft, etc.)
- Erie Connect account credentials

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on **Integrations**
3. Click the three dots menu (⋮) in the top right corner
4. Select **Custom repositories**
5. In the "Repository" field, enter:
   ```
   https://github.com/renson-thijs-dhaenens/pentair-homeassistant
   ```
6. In the "Category" dropdown, select **Integration**
7. Click **Add**
8. Close the custom repositories dialog
9. Click **+ Explore & Download Repositories**
10. Search for "Pentair Water Softener"
11. Click on it and then click **Download**
12. Restart Home Assistant

### Manual Installation

1. Copy the `pentair_water` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Pentair Water Softener"
4. Enter your Erie Connect email and password
5. The integration will automatically discover your water softener

## Entities

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<device>_total_volume` | Total water consumption (liters) |
| `sensor.<device>_last_regeneration` | Last regeneration timestamp |
| `sensor.<device>_nr_regenerations` | Total regeneration count |
| `sensor.<device>_last_maintenance` | Last maintenance timestamp |
| `sensor.<device>_flow` | Water flow per polling period (liters) |
| `sensor.<device>_warnings` | Active warnings |
| `sensor.<device>_status` | Current device status (e.g., "In Service") |
| `sensor.<device>_capacity_remaining` | Remaining capacity until regeneration (liters) |
| `sensor.<device>_days_remaining` | Estimated days until next regeneration |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.<device>_low_salt` | Low salt level indicator |

> **Note:** `<device>` will be replaced with your device name (e.g., `pentair_water_softener`).

## Example Configurations

### Formatted Date Template Sensors

```yaml
template:
  - sensor:
      - name: "Water Softener Last Maintenance"
        state: >
          {{ as_timestamp(states('sensor.pentair_water_last_maintenance')) | timestamp_custom("%d/%m/%Y @ %H:%M", True) }}

      - name: "Water Softener Last Regeneration"
        state: >
          {{ as_timestamp(states('sensor.pentair_water_last_regeneration')) | timestamp_custom("%d/%m/%Y @ %H:%M", True) }}

      - name: "Time Until Maintenance"
        state: >
          {%- set days = (( as_timestamp(states('sensor.pentair_water_last_maintenance')) + 3600 * 24 * 365 - as_timestamp(now()) )/ (3600*24)) | round(0, "ceil") -%}
          {% if days > 30 %}
          {{ (days / 30) | round(0, "ceil") }} months
          {% elif days > 14 %}
          {{ days }} days
          {% else %}
          {{ days }} days ❗
          {% endif %}
```

### Lovelace Entity Card

```yaml
type: entities
title: Water Softener
entities:
  - entity: sensor.pentair_water_warnings
    name: Warnings
  - entity: sensor.pentair_water_total_volume
    name: Total Water Consumption
    icon: mdi:water
  - entity: sensor.pentair_water_last_regeneration
    name: Last Regeneration
    icon: mdi:calendar-clock
  - entity: sensor.pentair_water_nr_regenerations
    name: Regeneration Count
    icon: mdi:recycle
  - entity: sensor.pentair_water_last_maintenance
    name: Last Service
    icon: mdi:calendar-clock
  - entity: binary_sensor.pentair_water_low_salt
    name: Low Salt
    icon: mdi:shaker-outline
```

### Mini Graph Card - Weekly Water Consumption

Requires [mini-graph-card](https://github.com/kalkih/mini-graph-card) from HACS.

```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.pentair_water_flow
    icon: mdi:water
    aggregate_func: sum
    name: "Water consumption"
name: Daily water consumption (last 7 days)
hours_to_show: 168
group_by: date
show:
  graph: bar
  labels: true
color_thresholds:
  - value: 0
    color: "#f5fdff"
  - value: 1
    color: "#3295a8"
```

### Mini Graph Card - 24 Hour Water Consumption

```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.pentair_water_flow
    aggregate_func: sum
    name: "Water consumption"
name: Last 24 hours water consumption
hours_to_show: 24
group_by: hour
hour24: true
show:
  graph: bar
  labels: true
color_thresholds:
  - value: 0
    color: "#f5fdff"
  - value: 1
    color: "#3295a8"
```

## Automations

### Low Salt Notification

```yaml
automation:
  - alias: "Water Softener - Low Salt Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.pentair_water_low_salt
        to: "on"
    action:
      - service: notify.notify
        data:
          title: "🧂 Water Softener Alert"
          message: "Low salt level detected in your water softener"
```

### Daily Status Notification

```yaml
automation:
  - alias: "Water Softener - Daily Status"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.pentair_water_low_salt
        state: "on"
    action:
      - service: notify.notify
        data:
          title: "🧂 Water Softener Reminder"
          message: "Remember to refill salt in your water softener"
```

## Troubleshooting

### Common Issues

1. **Authentication fails**: Verify your Erie Connect credentials work in the mobile app
2. **No device found**: Ensure your water softener is connected to the Erie Connect cloud
3. **Entities unavailable**: Check if the Erie Connect API is accessible

### Debug Logging

Add this to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  default: info
  logs:
    custom_components.pentair_water: debug
    erie_connect: debug
```

## Credits

- Based on the original Erie Water Treatment integration by [Tomasz Gebarowski](https://github.com/tgebarowski)
- Uses the [erie-connect](https://github.com/tgebarowski/erie-connect) Python library

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
