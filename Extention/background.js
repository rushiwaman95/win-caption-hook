function initContextMenus() {
  // Always try to create context menu — safe to call repeatedly
  chrome.contextMenus.remove("askQwenContext", () => {
    chrome.contextMenus.create({
      id: "askQwenContext",
      title: "Ask Qwen about this",
      contexts: ["selection"]
    });
  });
}

function initiate() {
  // Set side panel behavior
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(e => console.warn(e));

  // Add declarative net request rule (for iframe embedding)
  chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: [1],
    addRules: [{
      id: 1,
      priority: 1,
      action: {
        type: "modifyHeaders",
        responseHeaders: [
          { header: "content-security-policy", operation: "remove" },
          { header: "x-frame-options", operation: "remove" },
          { header: "frame-options", operation: "remove" },
          { header: "frame-ancestors", operation: "remove" },
          { header: "X-Content-Type-Options", operation: "remove" },
          { header: "access-control-allow-origin", operation: "set", value: "*" }
        ]
      },
      condition: {
        urlFilter: "||chat.qwen.ai/",
        resourceTypes: ["main_frame", "sub_frame"]
      }
    }]
  }).catch(e => console.error("DNR rule error:", e));

  // Register context menu on every startup (critical!)
  initContextMenus();

  // Listen for messages from content script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "askQwen") {
      chrome.sidePanel.open({ windowId: sender.tab.windowId }).catch(() => {});
      setTimeout(() => {
        chrome.runtime.sendMessage({
          type: "SIDEPANEL_ASK_QWEN",
          text: request.prompt
        }).catch(() => {});
      }, 800);
    }
    return true; // async response
  });

  // Handle context menu click
  chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "askQwenContext" && info.selectionText) {
      const CUSTOM_PROMPT = `Answer like an experienced AWS DevOps engineer in a real interview.
Keep answers in point to point no big sentence. just keep 2 to 3 short bullet points.
\n\n`;
      const fullPrompt = CUSTOM_PROMPT + `"${info.selectionText.trim()}"`;

      chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
      setTimeout(() => {
        chrome.runtime.sendMessage({
          type: "SIDEPANEL_ASK_QWEN",
          text: fullPrompt
        }).catch(() => {});
      }, 800);
    }
  });
}

initiate();