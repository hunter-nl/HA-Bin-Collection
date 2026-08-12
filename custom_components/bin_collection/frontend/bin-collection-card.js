class BinCollectionCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  static getStubConfig() {
    return {};
  }

  static getConfigElement() {
    return document.createElement("bin-collection-card-editor");
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 6;
  }

  _escape(value) {
    const element = document.createElement("span");
    element.textContent = value || "";
    return element.innerHTML;
  }

  _date(value) {
    return new Intl.DateTimeFormat(this._language(), {
      weekday: "short",
      day: "numeric",
      month: "short",
    }).format(new Date(`${value}T12:00:00`));
  }

  _relativeDate(value) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const pickup = new Date(`${value}T00:00:00`);
    const days = Math.round((pickup - today) / 86400000);
    return new Intl.RelativeTimeFormat(this._language(), { numeric: "auto" }).format(days, "day");
  }

  _language() {
    return this._hass.locale?.language || this._hass.language || "en";
  }

  _noticeText(value) {
    const documentFragment = new DOMParser().parseFromString(value || "", "text/html");
    documentFragment.querySelectorAll("br").forEach((element) => element.replaceWith("\n"));
    documentFragment.querySelectorAll("p, div, li").forEach((element) => element.append("\n"));
    return documentFragment.body.textContent.replace(/\n{3,}/g, "\n\n").trim();
  }

  _bindNoticeActions() {
    this.querySelectorAll("button[data-action='delete']").forEach((button) => {
      button.addEventListener("click", () => {
        this._hass.callService("bin_collection", "delete_notice", {
          entry_id: button.dataset.entryId,
          notice_id: button.dataset.noticeId,
        });
      });
    });
  }

  render() {
    if (!this._hass || !this.config) return;
    const state = this.config.entity
      ? this._hass.states[this.config.entity]
      : Object.values(this._hass.states).find((candidate) =>
        candidate.attributes.entry_id && Array.isArray(candidate.attributes.collections) && Array.isArray(candidate.attributes.notices),
      );
    if (!state) {
      const message = this.config.entity ? `Entity not found: ${this._escape(this.config.entity)}` : "No Bin Collection overview found";
      this.innerHTML = `<ha-card><div class="empty">${message}</div></ha-card>`;
      return;
    }
    const attrs = state.attributes;
    const collections = (attrs.collections || []).slice(0, this.config.max_collections || 5);
    const notices = [...(attrs.notices || [])].sort((left, right) =>
      (right.published || "").localeCompare(left.published || ""),
    );
    const labels = (this._language().startsWith("nl")
      ? { rest: "Restafval", paper: "Papier", gft: "GFT", pmd: "PMD" }
      : { rest: "Residual waste", paper: "Paper", gft: "Organic waste", pmd: "PMD" });
    const providers = { mijnafvalwijzer: "MijnAfvalwijzer", acv: "ACV" };
    const icons = {
      rest: "Kliko_rest_brand",
      paper: "Kliko_paper_brand",
      gft: "Kliko_gft_brand",
      pmd: "Kliko_pmd_brand",
    };
    const rows = collections.length
      ? collections.map((item) => `
          <div class="pickup ${this._escape(item.type)}">
            <img class="bin" src="/ha_bin_collection/${icons[item.type] || "None"}.png" alt="">
            <div class="pickup-copy"><div>${this._escape(labels[item.type] || item.source_type)}</div><small>${this._relativeDate(item.date)}</small></div>
            <time>${this._date(item.date)}</time>
          </div>`).join("")
      : '<div class="empty">No upcoming collections</div>';
    const messages = notices.length
      ? `<section class="notices"><h3>Provider messages</h3>${notices.map((notice) => `
          <article class="notice">
            <div class="notice-copy"><strong>${this._escape(this._noticeText(notice.title))}</strong><p>${this._escape(this._noticeText(notice.body))}</p></div>
            <div class="notice-actions">
              <button data-action="delete" data-entry-id="${this._escape(attrs.entry_id)}" data-notice-id="${this._escape(notice.notice_id)}" title="Delete message" aria-label="Delete message">×</button>
            </div>
          </article>`).join("")}</section>`
      : "";
    const provider = providers[attrs.provider] || "Bin Collection";
    this.innerHTML = `<ha-card>
      <style>
        :host{display:block}.header{padding:18px 20px 10px;font-size:28px;line-height:1.2}.header small{display:block;margin-top:4px;font-size:13px;font-weight:400;color:var(--secondary-text-color)}.pickups{padding:0 12px 10px}.pickup{display:flex;gap:14px;align-items:center;padding:10px 8px;border-radius:8px}.pickup:hover{background:var(--secondary-background-color)}.bin{width:48px;height:48px;object-fit:contain}.pickup-copy{flex:1;font-size:19px}.pickup-copy small{display:block;margin-top:3px;color:var(--primary-color);font-size:15px}.pickup time{white-space:nowrap;font-size:16px}.notices{border-top:1px solid var(--divider-color);padding:12px 16px 16px}.notices h3{margin:0 0 8px;font-size:17px}.notice{display:flex;gap:10px;margin-top:8px;padding:10px 0}.notice + .notice{border-top:1px solid var(--divider-color)}.notice-copy{flex:1}.notice p{margin:4px 0 0;white-space:pre-wrap;color:var(--secondary-text-color)}.notice-actions{display:flex;gap:4px;align-items:flex-start}.notice-actions button{border:0;border-radius:50%;width:32px;height:32px;background:transparent;color:var(--primary-text-color);font-size:20px;cursor:pointer}.notice-actions button:hover{background:var(--secondary-background-color)}.empty{padding:18px;color:var(--secondary-text-color)}
      </style>
      <div class="header">Next collection dates<small>${this._escape(provider)}</small></div>
      <div class="pickups">${rows}</div>${messages}
    </ha-card>`;
    this._bindNoticeActions();
  }
}

BinCollectionCard.prototype.constructor = BinCollectionCard;
customElements.define("bin-collection-card", BinCollectionCard);

class BinCollectionCardEditor extends HTMLElement {
  setConfig(config) {
    this.config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._hass || !this.config) return;
    const entities = Object.entries(this._hass.states)
      .filter(([entityId, state]) =>
        state.attributes.entry_id
        && (Object.hasOwn(state.attributes, "collections") || entityId.endsWith("_overview")),
      );
    const selectedEntity = this.config.entity || entities[0]?.[0] || "";
    const options = entities
      .map(([entityId, state]) => `<option value="${entityId}" ${entityId === selectedEntity ? "selected" : ""}>${state.attributes.provider || "Bin Collection"} — ${entityId}</option>`)
      .join("");
    this.innerHTML = `<style>:host{display:block;padding:8px 0}.field{display:grid;gap:6px;margin:10px 0}select,input{font:inherit;padding:8px;border:1px solid var(--divider-color);border-radius:4px;background:var(--card-background-color);color:var(--primary-text-color)}</style>
      <label class="field">Provider<select id="entity"><option value="">Select a provider</option>${options}</select></label>
      <label class="field">Collections shown<input id="max" type="number" min="1" max="20" value="${this.config.max_collections || 5}"></label>`;
    const updateConfig = () => {
      const entity = this.querySelector("#entity").value;
      const maxCollections = Number(this.querySelector("#max").value) || 5;
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: { ...this.config, entity, max_collections: maxCollections } }, bubbles: true, composed: true }));
    };
    this.querySelectorAll("select,input").forEach((element) => {
      element.addEventListener("change", updateConfig);
      element.addEventListener("input", updateConfig);
    });
  }
}
customElements.define("bin-collection-card-editor", BinCollectionCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "bin-collection-card",
  name: "Bin Collection Card",
  description: "Upcoming waste collections and provider messages.",
});
