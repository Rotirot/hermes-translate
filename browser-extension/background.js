const SERVER = "http://127.0.0.1:7473";

// Default language pair stored in extension settings
let fromCode = "en";
let toCode   = "fr";

// Load saved pair on startup
chrome.storage.local.get(["fromCode","toCode"], (res) => {
  if (res.fromCode) fromCode = res.fromCode;
  if (res.toCode)   toCode   = res.toCode;
});

// Create context menu item
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "hermes-translate",
    title: "Translate with Hermes",
    contexts: ["selection"]
  });
});

// Handle right-click translate
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "hermes-translate") return;
  const text = info.selectionText?.trim();
  if (!text) return;

  try {
    const res = await fetch(`${SERVER}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, from: fromCode, to: toCode })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    // Inject a floating result panel into the page
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: showTranslation,
      args: [text, data.translation, fromCode, toCode]
    });
  } catch (err) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: showError,
      args: [err.message]
    });
  }
});

// Listen for pair changes from popup
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "SET_PAIR") {
    fromCode = msg.from;
    toCode   = msg.to;
    chrome.storage.local.set({ fromCode, toCode });
  }
});

// ── injected functions (run in page context) ──

function showTranslation(original, translation, from, to) {
  document.getElementById("hermes-overlay")?.remove();

  const overlay = document.createElement("div");
  overlay.id = "hermes-overlay";
  overlay.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:2147483647;
    background:#1e1e30; color:#e2e2f0; font-family:Segoe UI,sans-serif;
    font-size:14px; border-radius:10px; box-shadow:0 8px 32px rgba(0,0,0,.6);
    max-width:380px; min-width:240px; padding:0; overflow:hidden;
    border:1px solid #2e2e50;
  `;

  overlay.innerHTML = `
    <div style="background:#252538;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
      <span style="color:#a78bfa;font-weight:600;font-size:13px;">⬡ Hermes · ${from} → ${to}</span>
      <button id="hermes-close" style="background:none;border:none;color:#7070a0;cursor:pointer;font-size:16px;line-height:1;">✕</button>
    </div>
    <div style="padding:12px 14px 4px;">
      <div style="color:#7070a0;font-size:11px;margin-bottom:4px;">Original</div>
      <div style="color:#a0a0c0;font-size:13px;margin-bottom:10px;max-height:80px;overflow-y:auto;">${original}</div>
      <div style="color:#7070a0;font-size:11px;margin-bottom:4px;">Translation</div>
      <div style="color:#e2e2f0;font-size:14px;line-height:1.5;max-height:120px;overflow-y:auto;">${translation}</div>
    </div>
    <div style="padding:8px 14px 12px;text-align:right;">
      <button id="hermes-copy" style="background:#7c6af7;color:#fff;border:none;border-radius:6px;padding:5px 14px;cursor:pointer;font-size:12px;">Copy</button>
    </div>
  `;

  document.body.appendChild(overlay);
  document.getElementById("hermes-close").onclick = () => overlay.remove();
  document.getElementById("hermes-copy").onclick = () => {
    navigator.clipboard.writeText(translation);
    document.getElementById("hermes-copy").textContent = "Copied!";
  };

  // Auto-dismiss after 30 seconds
  setTimeout(() => overlay?.remove(), 30000);
}

function showError(msg) {
  document.getElementById("hermes-overlay")?.remove();
  const overlay = document.createElement("div");
  overlay.id = "hermes-overlay";
  overlay.style.cssText = `
    position:fixed;bottom:24px;right:24px;z-index:2147483647;
    background:#1e1e30;color:#f87171;font-family:Segoe UI,sans-serif;
    font-size:13px;border-radius:10px;padding:14px 18px;
    box-shadow:0 8px 32px rgba(0,0,0,.6);border:1px solid #2e2e50;
    max-width:360px;
  `;
  overlay.innerHTML = `<b>⬡ Hermes error</b><br><br>${msg}<br><br>
    <span style="color:#7070a0;font-size:12px;">Is <code>hermes_server.py</code> running?</span>
    <button onclick="this.parentElement.remove()" style="float:right;background:none;border:none;color:#7070a0;cursor:pointer;font-size:15px;">✕</button>`;
  document.body.appendChild(overlay);
  setTimeout(() => overlay?.remove(), 15000);
}
