(async () => {
  const data = await chrome.storage.local.get("geminiPrompt");
  const prompt = data.geminiPrompt;
  if (!prompt) return;

  chrome.storage.local.remove("geminiPrompt");

  // Wait for Gemini's input field
  const waitForEditor = () => new Promise((resolve) => {
    const interval = setInterval(() => {
      const el =
        document.querySelector(".ql-editor p") ||
        document.querySelector("[contenteditable='true']") ||
        document.querySelector("textarea");
      if (el) { clearInterval(interval); resolve(el); }
    }, 500);
    setTimeout(() => clearInterval(interval), 15000);
  });

  const editor = await waitForEditor();
  if (!editor) return;

  await new Promise(r => setTimeout(r, 1000));

  if (editor.tagName === "TEXTAREA") {
    editor.value = prompt;
    editor.dispatchEvent(new Event("input", { bubbles: true }));
  } else {
    editor.focus();
    editor.innerText = prompt;
    editor.dispatchEvent(new InputEvent("input", { bubbles: true }));
  }

  // Auto-click send
  await new Promise(r => setTimeout(r, 600));
  const sendBtn =
    document.querySelector("[aria-label='Send message']") ||
    document.querySelector("button.send-button") ||
    document.querySelector("[data-mat-icon-name='send']") ||
    [...document.querySelectorAll("button")].find(b =>
      b.querySelector("mat-icon, .material-symbols-outlined")?.textContent?.includes("send")
    );

  if (sendBtn) sendBtn.click();
})();