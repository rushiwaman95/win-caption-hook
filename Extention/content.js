(function () {
  var CUSTOM_PROMPT =
    "DEVOPS EXPERT MODE — ACTIVATED\n" +
    "Answer as a senior DevOps engineer with 10+ years experience.\n" +
    "Keep 2-3 short bullet points only.\n\n";

  var isChatGPT = location.hostname === "chatgpt.com";

  if (isChatGPT) {
    setupChatGPTInjector();
  } else {
    setupFloatingButton();
  }

  // ════════════════════════════════════════
  // A. CHATGPT INJECTOR (runs inside iframe)
  // ════════════════════════════════════════
  function setupChatGPTInjector() {
    var injecting = false;

    // CHANNEL 1: chrome.storage (primary — most reliable)
    chrome.storage.local.get(["pendingPrompt", "promptTime"], function (data) {
      if (data.pendingPrompt && Date.now() - data.promptTime < 60000) {
        chrome.storage.local.remove(["pendingPrompt", "promptTime"]);
        waitThenInject(data.pendingPrompt);
      }
    });

    chrome.storage.onChanged.addListener(function (changes) {
      if (changes.pendingPrompt && changes.pendingPrompt.newValue) {
        chrome.storage.local.remove(["pendingPrompt", "promptTime"]);
        waitThenInject(changes.pendingPrompt.newValue);
      }
    });

    // CHANNEL 2: chrome.runtime.onMessage (backup)
    chrome.runtime.onMessage.addListener(function (msg) {
      if (msg.action === "injectPrompt") waitThenInject(msg.prompt);
    });

    // CHANNEL 3: postMessage from sidepanel.js (backup)
    window.addEventListener("message", function (e) {
      if (e.data && e.data.type === "DEVOPS_INJECT") waitThenInject(e.data.prompt);
    });

    function waitThenInject(prompt) {
      if (injecting) return;
      injecting = true;
      setTimeout(function () {
        doInject(prompt).then(function () { injecting = false; });
      }, 300);
    }

    async function doInject(prompt) {
      var editor = await waitForEditor();
      if (!editor) return;
      await delay(100);

      editor.focus();

      if (editor.tagName === "TEXTAREA") {
        // React textarea — use native setter
        var setter = Object.getOwnPropertyDescriptor(
          window.HTMLTextAreaElement.prototype, "value"
        ).set;
        setter.call(editor, prompt);
        editor.dispatchEvent(new Event("input", { bubbles: true }));
      } else {
        // ProseMirror / contenteditable
        // Select all existing text, then replace via execCommand
        var sel = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(editor);
        sel.removeAllRanges();
        sel.addRange(range);
        document.execCommand("insertText", false, prompt);
      }

      await delay(200);
      clickSend();
    }

    function waitForEditor() {
      return new Promise(function (resolve) {
        var tries = 0;
        var iv = setInterval(function () {
          var el =
            document.querySelector("#prompt-textarea") ||
            document.querySelector("textarea") ||
            document.querySelector('[contenteditable="true"]');
          if (el || ++tries > 30) {
            clearInterval(iv);
            resolve(el || null);
          }
        }, 500);
      });
    }

    function clickSend() {
      var btn =
        document.querySelector('button[data-testid="send-button"]') ||
        document.querySelector('button[type="submit"]') ||
        document.querySelector('button[aria-label*="send" i]');
      if (btn && !btn.disabled) {
        btn.click();
      } else {
        // Retry — button may be enabling
        setTimeout(function () {
          var b = document.querySelector('button[data-testid="send-button"]') ||
                  document.querySelector('button[type="submit"]');
          if (b) b.click();
        }, 300);
      }
    }

    // Copy enhancement for code blocks
    document.addEventListener("click", function (e) {
      var button = e.target.closest("button");
      if (!button) return;
      var label = (button.getAttribute("aria-label") || "").toLowerCase();
      if (!label.includes("copy") || label === "copied") return;
      var code =
        button.closest("div") && button.closest("div").querySelector("code");
      if (code) copyText(code.textContent);
    }, true);
  }

  // ════════════════════════════════════
  // B. FLOATING BUTTON (all other pages)
  // ════════════════════════════════════
  function setupFloatingButton() {
    var btn = null;
    var lastCardClick = 0;

    // Inject floating button styles
    var style = document.createElement("style");
    style.textContent =
      "#gemin-ask-btn{position:absolute;z-index:2147483647;" +
      "background:linear-gradient(135deg,#4285f4,#886aea);" +
      "color:#fff;border:none;border-radius:20px;padding:6px 14px;" +
      "font-size:13px;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,0.25);" +
      "font-family:sans-serif;animation:gfade .15s ease}" +
      "#gemin-ask-btn:hover{transform:scale(1.05)}" +
      "@keyframes gfade{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}";
    document.head.appendChild(style);

    // Text selection → floating button
    document.addEventListener("mouseup", function (e) {
      setTimeout(function () {
        var text = window.getSelection().toString().trim();
        removeBtn();
        if (text.length < 2) return;

        btn = document.createElement("button");
        btn.id = "gemin-ask-btn";
        btn.textContent = "✨ Ask ChatGPT";
        btn.onclick = function (ev) {
          ev.stopPropagation();
          chrome.runtime.sendMessage({
            action: "askChatGPT",
            prompt: CUSTOM_PROMPT + '"' + text + '"'
          });
          removeBtn();
        };
        document.body.appendChild(btn);
        btn.style.left = e.pageX + 10 + "px";
        btn.style.top = e.pageY + 10 + "px";
      }, 100);
    });

    // Card click
    document.addEventListener("click", function (e) {
      if (btn && !btn.contains(e.target)) removeBtn();

      var card = e.target.closest(".card");
      if (!card || e.target.closest(".cp")) return;

      var now = Date.now();
      if (now - lastCardClick < 2000) return;
      lastCardClick = now;

      var textEl = card.querySelector(".t");
      var text = textEl
        ? textEl.textContent.trim()
        : card.textContent.replace("copy", "").trim();
      if (text.length < 3) return;

      // Visual feedback
      card.style.borderLeft = "3px solid #886aea";
      card.style.opacity = "0.7";
      setTimeout(function () {
        card.style.borderLeft = "";
        card.style.opacity = "1";
      }, 2000);

      chrome.runtime.sendMessage({
        action: "askChatGPT",
        prompt: CUSTOM_PROMPT + '"' + text + '"'
      });
    });

    function removeBtn() {
      if (btn) { btn.remove(); btn = null; }
    }
  }

  // ════════════════════
  // SHARED UTILITIES
  // ════════════════════
  function copyText(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0;left:-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }

  function delay(ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
  }
})();