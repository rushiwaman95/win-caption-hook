console.log("injectQwen.js initialized");

window.addEventListener("message", async function (event) {
    try {
        if (event.origin !== "chrome-extension://" + chrome.runtime.id) return;
    } catch (e) {
        return;
    }

    if (event.data.type === "ASK_QWEN_WITH_PROMPT") {
        var promptText = event.data.text;
        console.log("Received prompt:", promptText.substring(0, 50) + "...");

        try {
            var inputArea = await waitForInput();
            console.log("Found input:", inputArea.tagName);

            inputArea.focus();
            await sleep(300);

            if (inputArea.tagName === "TEXTAREA" || inputArea.tagName === "INPUT") {
                // Clear first
                inputArea.value = "";
                inputArea.dispatchEvent(new Event("input", { bubbles: true }));
                await sleep(100);
                // Set value
                inputArea.value = promptText;
                inputArea.dispatchEvent(new Event("input", { bubbles: true }));
                inputArea.dispatchEvent(new Event("change", { bubbles: true }));
            } else if (inputArea.isContentEditable) {
                inputArea.textContent = "";
                await sleep(100);
                inputArea.textContent = promptText;
                inputArea.dispatchEvent(new InputEvent("input", {
                    bubbles: true,
                    inputType: "insertText",
                    data: promptText
                }));
            } else {
                inputArea.innerText = promptText;
                inputArea.dispatchEvent(new InputEvent("input", { bubbles: true }));
            }

            console.log("Prompt inserted");
            await sleep(800);

            // Try multiple ways to send
            var sent = false;

            // Method 1: Find send button by multiple selectors
            var sendBtn = findSendBtn();
            if (sendBtn) {
                console.log("Found send button, clicking");
                sendBtn.click();
                sent = true;
            }

            // Method 2: Enter key on textarea
            if (!sent) {
                console.log("Trying Enter key");
                inputArea.dispatchEvent(new KeyboardEvent("keydown", {
                    key: "Enter", code: "Enter", keyCode: 13,
                    which: 13, bubbles: true
                }));
                inputArea.dispatchEvent(new KeyboardEvent("keypress", {
                    key: "Enter", code: "Enter", keyCode: 13,
                    which: 13, bubbles: true
                }));
                inputArea.dispatchEvent(new KeyboardEvent("keyup", {
                    key: "Enter", code: "Enter", keyCode: 13,
                    which: 13, bubbles: true
                }));
            }

        } catch (error) {
            console.error("Error:", error);
            try {
                chrome.runtime.sendMessage({
                    type: "SIDEPANEL_INJECT_ERROR",
                    error: error.message
                });
            } catch (e) {}
        }
    }
});

function sleep(ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
}

function waitForInput(timeout) {
    timeout = timeout || 15000;
    return new Promise(function (resolve, reject) {
        var start = Date.now();
        var check = function () {
            var el =
                document.querySelector("textarea") ||
                document.querySelector('[contenteditable="true"]') ||
                document.querySelector('textarea[placeholder*="message" i]') ||
                document.querySelector(".ql-editor");
            if (el) {
                resolve(el);
            } else if (Date.now() - start >= timeout) {
                reject(new Error("Input not found"));
            } else {
                setTimeout(check, 500);
            }
        };
        check();
    });
}

function findSendBtn() {
    // Try many selectors — Qwen changes their UI frequently
    var selectors = [
        'button[type="submit"]',
        'button[aria-label*="send" i]',
        'button[aria-label*="Send"]',
        '[data-testid*="send"]',
        '.send-button',
        'button.chat-send',
        // SVG icon buttons (common in chat UIs)
        'button svg[viewBox] ~ span',
    ];

    for (var i = 0; i < selectors.length; i++) {
        var el = document.querySelector(selectors[i]);
        if (el) {
            // If we found an element inside button, get the button
            var btn = el.closest("button") || el;
            if (btn.tagName === "BUTTON") return btn;
        }
    }

    // Fallback: find button with send-like icon or text
    var buttons = document.querySelectorAll("button");
    for (var j = 0; j < buttons.length; j++) {
        var b = buttons[j];
        var label = (b.getAttribute("aria-label") || "") +
                    (b.textContent || "");
        if (label.toLowerCase().match(/send|submit|arrow/)) {
            return b;
        }
        // Check for SVG arrow icon (very common send button)
        if (b.querySelector("svg") && !b.textContent.trim()) {
            var rect = b.getBoundingClientRect();
            // Small button near bottom-right is likely send
            if (rect.width < 60 && rect.bottom > window.innerHeight - 100) {
                return b;
            }
        }
    }

    return null;
}