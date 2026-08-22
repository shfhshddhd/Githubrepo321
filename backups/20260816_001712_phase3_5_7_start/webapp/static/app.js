(() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  const notice = document.getElementById("notice");
  const retry = document.getElementById("retry");
  const refreshState = document.getElementById("refresh-state");
  let ticket = "";

  if (tg) {
    tg.ready();
    tg.expand();
    if (tg.colorScheme === "light") {
      document.documentElement.dataset.telegramTheme = "light";
    }
  }

  function setNotice(message, kind = "") {
    notice.textContent = message;
    notice.className = `notice ${kind}`.trim();
  }

  function setText(id, value) {
    document.getElementById(id).textContent = value;
  }

  function showError(message) {
    setNotice(message, "error");
    retry.hidden = false;
    refreshState.classList.add("paused");
  }

  async function authenticate() {
    retry.hidden = true;
    refreshState.classList.remove("paused");
    if (!tg || !tg.initData) {
      showError("Open this page from the Telegram bot to continue.");
      return;
    }

    setNotice("Authenticating with Telegram…");
    const response = await fetch("api/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initData: tg.initData }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      if (payload.code === "not_hosted") {
        showError("No active hosted account was found. Use /host in the control bot first.");
      } else {
        showError(payload.message || "Telegram authentication failed.");
      }
      return;
    }
    ticket = payload.ticket;
    setNotice("Securely connected.", "success");
    await refreshStatus();
  }

  async function refreshStatus() {
    const response = await fetch("api/status", {
      headers: { Authorization: `Bearer ${ticket}` },
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      if (payload.code === "not_hosted") {
        showError("Your hosted Telegram account is no longer active. Use /host in the control bot first.");
        return;
      }
      showError(payload.message || "The authorization expired. Try again.");
      return;
    }

    const account = payload.hosted && payload.session_active;
    const voice = payload.voice_chat;
    setText("account-status", account ? "Connected" : "Offline");
    setText("account-detail", account ? `Telegram ID ${payload.telegram_user_id}` : "Hosted session unavailable");
    setText("vc-status", voice.connected ? "Connected" : "Not connected");
    setText("vc-detail", voice.connected ? (voice.title || "Active Voice Chat") : "Use .vcjoin in the control bot");
    if (voice.connected) {
      setNotice("Voice Chat connected. Live audio is the next phase.", "success");
    }
  }

  retry.addEventListener("click", () => authenticate().catch(() => showError("Could not reach the Mini App server.")));
  authenticate().catch(() => showError("Could not reach the Mini App server."));
})();