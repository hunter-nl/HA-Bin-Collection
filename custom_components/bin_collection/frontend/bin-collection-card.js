class BinCollectionCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity)
      throw new Error("Specify a Bin Collection overview entity.");
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 4;
  }

  render() {
    if (!this._hass || !this.config) return;
    const state = this._hass.states[this.config.entity];
    if (!state) {
      this.innerHTML = `<ha-card><div class="empty">Entity not found: ${this.config.entity}</div></ha-card>`;
      return;
    }
    const collections = (state.attributes.collections || []).slice(0, 8);
    const notices = state.attributes.notices || [];
    const labels = { rest: "Rest", paper: "Papier", gft: "GFT", pmd: "PMD" };
    const icon = (type) =>
      `<img class="bin ${type}" src="/ha_bin_collection/${{ rest: "Kliko_rest", paper: "Kliko_paper", gft: "Kliko_gft", pmd: "Kliko_pmd" }[type] || "None"}.png" alt="">`;
    const rows = collections.length
      ? collections
          .map(
            (item) =>
              `<div class="pickup">${icon(item.type)}<span>${labels[item.type] || item.source_type}</span><time>${item.date}</time></div>`,
          )
          .join("")
      : `<div class="empty">No upcoming collections</div>`;
    const messages = notices
      .map(
        (notice) =>
          `<div class="notice"><b>${notice.title}</b><br>${notice.body}</div>`,
      )
      .join("");
    this.innerHTML = `<ha-card><style>:host{display:block}.header{display:flex;justify-content:space-between;align-items:baseline;padding:16px 16px 10px;font-size:20px;font-weight:600}.header small{font-size:12px;font-weight:400;color:var(--secondary-text-color)}.pickups{padding:0 12px 10px}.pickup{display:flex;gap:12px;align-items:center;padding:8px}.pickup time{margin-left:auto;color:var(--secondary-text-color)}.bin{width:42px;height:42px;object-fit:cover;border-radius:4px}.notice{margin:8px 16px 16px;padding:10px;border-left:4px solid var(--warning-color,#f6a700);background:var(--secondary-background-color);border-radius:4px}.empty{padding:18px;color:var(--secondary-text-color)}</style><div class="header"><span>Afval</span><small>${state.state === "none" ? "Geen komende inzameling" : `Volgende: ${state.state}`}</small></div><div class="pickups">${rows}</div>${messages}</ha-card>`;
  }
}
BinCollectionCard.prototype.constructor = BinCollectionCard;
customElements.define("bin-collection-card", BinCollectionCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "bin-collection-card",
  name: "Bin Collection Card",
  description: "Upcoming waste collections and collector notices.",
});
