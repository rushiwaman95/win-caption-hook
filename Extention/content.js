let btn = null;

const CUSTOM_PROMPT = `DEVOPS INTERVIEW CHEAT SHEET MODE — ACTIVATED

[PASTE YOUR QUESTION/DUMP BELOW]
→ I reply in STRICT format:

• Topic: [1-line ID]
• [keyword] — [3-5 word context]
• [command/tool] — [what it fixes]
• [metric/scale] — [target value]
• [prod-impact] — [outcome/result]
• [zero-downtime tactic] — [how applied]
• [senior shortcut] — [why it works]

RULES I FOLLOW:
- 5-7 bullets MAX
- Keyword + micro-phrase ONLY (3-5 words)
- NO long sentences, NO paragraphs, NO intros
- Tools/commands/metrics first, context second
- Senior context: scale, SLA, automation, drift, rollback

EXAMPLE INPUT:
"how do you handle k8s hpa not scaling during spike?"

EXAMPLE OUTPUT:
• Topic: K8s HPA Tuning
• metrics-server — enables auto-scaling
• hpa minReplicas 3 — avoids cold-start
• cpu threshold 70% — headroom for spikes
• custom metrics API — app-level triggers
• cluster-autoscaler fallback — node provisioning
• cooldown 30s — prevents thrashing
• prod: 99.95% SLA — zero downtime maintained

\n\n`;

// Ensure DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSelectionHandler);
} else {
  initSelectionHandler();
}

function initSelectionHandler() {
  // Try multiple event types for better coverage
  document.addEventListener("mouseup", handleMouseUp);
  document.addEventListener("selectionchange", handleSelectionChange); // fallback
}

function handleMouseUp(e) {
  setTimeout(() => {
    const text = window.getSelection().toString().trim();
    removeBtn();
    if (text.length < 2) return;

    // Create button safely
    btn = document.createElement("button");
    btn.id = "gemin-ask-btn"; // match CSS selector
    btn.textContent = "✨ Ask Qwen";
    btn.style.cssText = `
      position: absolute;
      z-index: 2147483647;
      background: linear-gradient(135deg, #4285f4, #886aea);
      color: white;
      border: none;
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 13px;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0,0,0,0.25);
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: sans-serif;
      animation: gemini-fade 0.15s ease;
    `;
    
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const fullPrompt = CUSTOM_PROMPT + `"${text}"`;
      chrome.runtime.sendMessage({ action: "askQwen", prompt: fullPrompt });
      removeBtn();
    });

    document.body.appendChild(btn);
    btn.style.left = `${e.pageX + 10}px`;
    btn.style.top = `${e.pageY + 10}px`;
  }, 100);
}

function handleSelectionChange() {
  // Optional: trigger on selection change (e.g., keyboard selection)
  const text = window.getSelection().toString().trim();
  if (text.length >= 2 && !btn) {
    handleMouseUp({ pageX: 100, pageY: 100 }); // fake coords — button will be repositioned on next mouseup
  }
}

function removeBtn() {
  if (btn) {
    btn.remove();
    btn = null;
  }
}

// Auto-trigger on caption card click (if present)
document.addEventListener("click", (e) => {
  const card = e.target.closest(".card");
  if (card && !e.target.closest(".cp")) {
    const textSpan = card.querySelector(".t");
    let text = textSpan ? textSpan.textContent.trim() : card.textContent.replace("copy", "").trim();
    if (text.length > 2) {
      const fullPrompt = CUSTOM_PROMPT + `"${text}"`;
      chrome.runtime.sendMessage({ action: "askQwen", prompt: fullPrompt });
    }
  }
});