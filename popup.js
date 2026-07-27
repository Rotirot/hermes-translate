const SERVER = "http://127.0.0.1:7473";

async function init() {
  const select = document.getElementById("pair");
  const status = document.getElementById("status");
  const dot    = document.getElementById("dot");
  const srvTxt = document.getElementById("server-status");

  // Load available pairs from server
  try {
    const res  = await fetch(`${SERVER}/pairs`);
    const data = await res.json();
    dot.className = "dot online";
    srvTxt.textContent = "Server online";

    data.pairs.forEach(p => {
      const opt = document.createElement("option");
      opt.value = `${p.from}|${p.to}`;
      opt.textContent = p.label;
      select.appendChild(opt);
    });

    // Restore saved pair
    chrome.storage.local.get(["fromCode","toCode"], (saved) => {
      if (saved.fromCode && saved.toCode) {
        select.value = `${saved.fromCode}|${saved.toCode}`;
      }
    });
  } catch {
    dot.className = "dot offline";
    srvTxt.textContent = "Server offline — run hermes_server.py";
    select.innerHTML = '<option value="">Server not running</option>';
  }

  // Save on change
  select.addEventListener("change", () => {
    const [from, to] = select.value.split("|");
    chrome.runtime.sendMessage({ type: "SET_PAIR", from, to });
    status.textContent = "Saved!";
    setTimeout(() => status.textContent = "", 1500);
  });
}

init();
