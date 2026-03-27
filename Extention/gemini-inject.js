// Listen for messages from background
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "resetAndAsk") {
    injectPrompt(msg.prompt);
  }
});

async function injectPrompt(prompt) {
  // Optional: try to clear chat (Qwen doesn't expose clear API, but we can simulate)
  // Try clicking "New Chat" if exists
  const newChatBtn = document.querySelector('button[aria-label*="new chat"]') ||
                     document.querySelector('button:contains("New Chat")') ||
                     [...document.querySelectorAll('button')].find(b => 
                       b.textContent.trim().toLowerCase().includes('new chat')
                     );
  if (newChatBtn) {
    newChatBtn.click();
    await new Promise(r => setTimeout(r, 800));
  }

  // Wait for editor
  const editor = await waitForEditor();
  if (!editor) return;

  await new Promise(r => setTimeout(r, 600));

  // Clear and fill
  if (editor.tagName === "TEXTAREA") {
    editor.value = prompt;
    editor.dispatchEvent(new Event("input", { bubbles: true }));
  } else {
    editor.focus();
    editor.innerText = prompt;
    editor.dispatchEvent(new InputEvent("input", { bubbles: true }));
  }

  // Auto-send
  await new Promise(r => setTimeout(r, 600));
  const sendBtn = findSendButton();
  if (sendBtn) sendBtn.click();
}

function waitForEditor() {
  return new Promise((resolve) => {
    const interval = setInterval(() => {
      const el =
        document.querySelector('textarea[placeholder*="message" i]') ||
        document.querySelector('.ql-editor') ||
        document.querySelector('[contenteditable="true"]') ||
        document.querySelector('textarea');
      if (el) {
        clearInterval(interval);
        resolve(el);
      }
    }, 500);
    setTimeout(() => clearInterval(interval), 15000);
  });
}

function findSendButton() {
  return document.querySelector('button[type="submit"]') ||
         document.querySelector('button[aria-label*="send" i]') ||
         [...document.querySelectorAll('button')].find(b =>
           b.textContent.toLowerCase().includes('send') ||
           b.getAttribute('aria-label')?.toLowerCase().includes('send')
         );
}