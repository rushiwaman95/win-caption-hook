let btn = null;
let lastCardClickTime = 0;

const CUSTOM_PROMPT = `DEVOPS EXPERT MODE — ACTIVATED
Answer as a senior DevOps engineer with 10+ years of experience.
Keep answers in point to point no big sentence. just keep 2 to 3 short bullet points.

\n\n`;

// ─── BULLETPROOF EXTENSION CHECK ───
function getRuntime() {
    try {
        if (typeof chrome === "undefined") return null;
        if (typeof chrome.runtime === "undefined") return null;
        if (!chrome.runtime.id) return null;
        return chrome.runtime;
    } catch (e) {
        return null;
    }
}

function safeSendMessage(msg) {
    var rt = getRuntime();
    if (!rt) return false;
    try {
        rt.sendMessage(msg);
        return true;
    } catch (e) {
        return false;
    }
}

// ─── INIT ───
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}

function init() {
    document.addEventListener("mouseup", handleMouseUp);

    // ─── CARD CLICK → ASK QWEN ───
    document.addEventListener("click", function (e) {
        // Remove floating button if clicking elsewhere
        if (btn && !btn.contains(e.target)) {
            removeBtn();
        }

        var card = e.target.closest(".card");
        if (!card || e.target.closest(".cp")) return;

        // Debounce
        var now = Date.now();
        if (now - lastCardClickTime < 2000) return;
        lastCardClickTime = now;

        var textSpan = card.querySelector(".t");
        var text = textSpan
            ? textSpan.textContent.trim()
            : card.textContent.replace("copy", "").trim();
        if (text.length < 3) return;

        // Visual feedback
        card.style.borderLeft = "3px solid #886aea";
        card.style.opacity = "0.7";
        setTimeout(function () {
            card.style.borderLeft = "";
            card.style.opacity = "1";
        }, 2000);

        var sent = safeSendMessage({
            action: "askQwen",
            prompt: CUSTOM_PROMPT + '"' + text + '"'
        });

        if (!sent) {
            console.log("Qwen extension not available — reload extension & refresh page");
        }
    });

    // ─── LISTEN FOR MESSAGES FROM BACKGROUND ───
    var rt = getRuntime();
    if (rt) {
        try {
            rt.onMessage.addListener(function (msg) {
                if (msg.action === "resetAndAsk") {
                    injectPrompt(msg.prompt);
                }
            });
        } catch (e) {}
    }
}

// ─── TEXT SELECTION → FLOATING BUTTON ───
function handleMouseUp(e) {
    setTimeout(function () {
        if (!getRuntime()) return;

        var text = window.getSelection().toString().trim();
        removeBtn();
        if (text.length < 2) return;

        btn = document.createElement("button");
        btn.id = "gemin-ask-btn";
        btn.textContent = "✨ Ask Qwen";
        btn.style.cssText =
            "position:absolute;z-index:2147483647;" +
            "background:linear-gradient(135deg,#4285f4,#886aea);" +
            "color:white;border:none;border-radius:20px;" +
            "padding:6px 14px;font-size:13px;cursor:pointer;" +
            "box-shadow:0 2px 10px rgba(0,0,0,0.25);" +
            "display:flex;align-items:center;gap:6px;" +
            "font-family:sans-serif;";

        btn.addEventListener("click", function (ev) {
            ev.stopPropagation();
            safeSendMessage({
                action: "askQwen",
                prompt: CUSTOM_PROMPT + '"' + text + '"'
            });
            removeBtn();
        });

        document.body.appendChild(btn);
        btn.style.left = e.pageX + 10 + "px";
        btn.style.top = e.pageY + 10 + "px";
    }, 100);
}

function removeBtn() {
    if (btn) {
        btn.remove();
        btn = null;
    }
}

// ─── INJECT PROMPT (for Qwen page) ───
async function injectPrompt(prompt) {
    var newChatBtn =
        document.querySelector('button[aria-label*="new chat" i]') ||
        Array.from(document.querySelectorAll("button")).find(function (b) {
            return b.textContent.trim().toLowerCase().includes("new chat");
        });
    if (newChatBtn) {
        newChatBtn.click();
        await new Promise(function (r) { setTimeout(r, 800); });
    }

    var editor = await waitForEditor();
    if (!editor) return;
    await new Promise(function (r) { setTimeout(r, 600); });

    if (editor.tagName === "TEXTAREA") {
        editor.value = prompt;
        editor.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
        editor.focus();
        editor.innerText = prompt;
        editor.dispatchEvent(new InputEvent("input", { bubbles: true }));
    }

    await new Promise(function (r) { setTimeout(r, 600); });
    var sendBtn = findSendButton();
    if (sendBtn) sendBtn.click();
}

function waitForEditor() {
    return new Promise(function (resolve) {
        var interval = setInterval(function () {
            var el =
                document.querySelector('textarea[placeholder*="message" i]') ||
                document.querySelector(".ql-editor") ||
                document.querySelector('[contenteditable="true"]') ||
                document.querySelector("textarea");
            if (el) {
                clearInterval(interval);
                resolve(el);
            }
        }, 500);
        setTimeout(function () { clearInterval(interval); resolve(null); }, 15000);
    });
}

function findSendButton() {
    return (
        document.querySelector('button[type="submit"]') ||
        document.querySelector('button[aria-label*="send" i]') ||
        document.querySelector('[data-testid*="send"]') ||
        Array.from(document.querySelectorAll("button")).find(function (b) {
            return (
                b.textContent.toLowerCase().includes("send") ||
                (b.getAttribute("aria-label") || "").toLowerCase().includes("send")
            );
        })
    );
}