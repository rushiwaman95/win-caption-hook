chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action !== "askGemini") return;

  chrome.storage.local.set({ geminiPrompt: msg.prompt }, () => {
    chrome.storage.local.get("geminiWindowId", ({ geminiWindowId }) => {

      if (geminiWindowId) {
        // Check if window still exists
        chrome.windows.get(geminiWindowId, {}, (win) => {
          if (chrome.runtime.lastError || !win) {
            // Window was closed, create new one
            openSidebar();
          } else {
            // Window exists — reuse it, just reload Gemini
            chrome.tabs.query({ windowId: geminiWindowId }, (tabs) => {
              if (tabs && tabs[0]) {
                chrome.tabs.update(tabs[0].id, { url: "https://gemini.google.com/app" });
                chrome.windows.update(geminiWindowId, { focused: true });
              }
            });
          }
        });
      } else {
        openSidebar();
      }

    });
  });
});

function openSidebar() {
  chrome.windows.getCurrent((currentWin) => {
    const sidebarWidth = 420;

    // Shrink main window
    chrome.windows.update(currentWin.id, {
      width: currentWin.width - sidebarWidth
    });

    // Create sidebar popup
    chrome.windows.create({
      url: "https://gemini.google.com/app",
      type: "popup",
      width: sidebarWidth,
      height: currentWin.height,
      left: currentWin.left + currentWin.width - sidebarWidth,
      top: currentWin.top
    }, (win) => {
      chrome.storage.local.set({ geminiWindowId: win.id });
    });
  });
}

// Clear stored ID when sidebar is closed
chrome.windows.onRemoved.addListener((windowId) => {
  chrome.storage.local.get("geminiWindowId", ({ geminiWindowId }) => {
    if (windowId === geminiWindowId) {
      chrome.storage.local.remove("geminiWindowId");
    }
  });
});