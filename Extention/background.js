const CUSTOM_PROMPT = `DEVOPS EXPERT MODE — ACTIVATED
Answer as a senior DevOps engineer with 10+ years experience.
Keep 2-3 short bullet points only.\n\n`;

chrome.runtime.onInstalled.addListener(() => {
  chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: [1],
    addRules: [{
      id: 1,
      priority: 1,
      action: {
        type: "modifyHeaders",
        responseHeaders: [
          { header: "content-security-policy", operation: "remove" },
          { header: "x-frame-options", operation: "remove" }
        ]
      },
      condition: {
        urlFilter: "https://chatgpt.com/*",
        resourceTypes: ["main_frame", "sub_frame"]
      }
    }]
  });

  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

  chrome.contextMenus.create({
    id: "askChatGPT",
    title: "Ask ChatGPT",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "askChatGPT" && info.selectionText) {
    handlePrompt(CUSTOM_PROMPT + '"' + info.selectionText + '"', tab);
  }
});

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.action === "askChatGPT") {
    handlePrompt(msg.prompt, sender.tab);
  }
});

async function handlePrompt(prompt, senderTab) {
  // Store prompt
  chrome.storage.local.set({
    pendingPrompt: prompt,
    promptTime: Date.now()
  });

  // Broadcast to sidepanel
  chrome.runtime.sendMessage({ action: "injectPrompt", prompt }).catch(() => {});

  // Send to ChatGPT tabs
  try {
    const tabs = await chrome.tabs.query({ url: "https://chatgpt.com/*" });
    for (const tab of tabs) {
      chrome.tabs.sendMessage(tab.id, { action: "injectPrompt", prompt }).catch(() => {});
    }
  } catch (e) {}

  // ═══ AUTO-OPEN SIDE PANEL ═══
  try {
    let windowId;

    if (senderTab && senderTab.windowId) {
      windowId = senderTab.windowId;
    } else {
      // Fallback: get current active window
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (activeTab) windowId = activeTab.windowId;
    }

    if (windowId) {
      await chrome.sidePanel.open({ windowId: windowId });
    }
  } catch (e) {
    console.log("sidePanel.open failed:", e);
  }
}