const ADDRESS = "https://chatgpt.com";

async function fetchAuth() {
  try {
    const res = await fetch(ADDRESS + "/api/auth/session");
    if (res.status === 403)
      return { ok: false, msg: 'Pass Cloudflare at <a href="' + ADDRESS + '" target="_blank">chatgpt.com</a>' };
    const data = await res.json();
    if (!res.ok || !data.accessToken)
      return { ok: false, msg: 'Login at <a href="' + ADDRESS + '" target="_blank">chatgpt.com</a> first' };
    return { ok: true };
  } catch (e) {
    return { ok: false, msg: "Connection error" };
  }
}

async function init() {
  const container = document.getElementById("iframe");
  const auth = await fetchAuth();

  if (auth.ok) {
    const iframe = document.createElement("iframe");
    iframe.src = ADDRESS + "/chat";
    iframe.id = "chatgpt-frame";
    iframe.style.cssText = "width:100%;height:100vh;border:none;";
    container.appendChild(iframe);

    // Forward prompts to iframe via postMessage (backup channel)
    chrome.runtime.onMessage.addListener((msg) => {
      if (msg.action === "injectPrompt") {
        iframe.contentWindow.postMessage(
          { type: "DEVOPS_INJECT", prompt: msg.prompt },
          ADDRESS
        );
      }
    });
  } else {
    container.innerHTML =
      '<div class="extension-body"><div class="notice">' + auth.msg + '</div></div>';
  }
}

init();