# Bin Collection Card

Bin Collection automatically registers this card as a JavaScript module for
Home Assistant storage-mode dashboards. No manual Dashboard Resources entry is
needed.

For Lovelace `resource_mode: yaml`, add the module resource to the YAML
configuration because Home Assistant keeps YAML-managed resources immutable:

```yaml
resources:
  - url: /ha_bin_collection/bin-collection-card.js?v=1.0.0
    type: module
```

The card uses the paired `Kliko_*_brand.png` assets: the bin icon and the
matching waste-stream symbol are presented side by side.
