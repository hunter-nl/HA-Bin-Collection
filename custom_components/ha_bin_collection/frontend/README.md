# HA Bin Collection Card

HA Bin Collection automatically registers this card as a JavaScript module for
Home Assistant storage-mode dashboards. No manual Dashboard Resources entry is
needed.

For Lovelace `resource_mode: yaml`, add the module resource to the YAML
configuration because Home Assistant keeps YAML-managed resources immutable:

```yaml
resources:
  - url: /ha_bin_collection/ha-bin-collection-card.js?v=0.0.1-alpha
    type: module
```
