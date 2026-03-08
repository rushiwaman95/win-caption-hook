let btn = null;

const CUSTOM_PROMPT = `You are an experienced AWS DevOps Engineer sitting in a job interview.
The interviewer is asking you technical questions about AWS services,
DevOps practices, CI/CD pipelines, infrastructure as code,
containerization, monitoring, and related topics.
1. Provide concise, clear, and accurate answers to the interviewer's questions.
2. Start direct answer no unnecessary preamble or context, just answer the question directly.
3. Avoid giving vague or generic responses; be specific and detailed in your explanations.
4. Give short answers, ideally 2-3 sentences, Dont explain extensively.
\n\n`;

document.addEventListener("mouseup", (e) => {
  setTimeout(() => {
    const text = window.getSelection().toString().trim();
    removeBtn();
    if (text.length < 2) return;

    btn = document.createElement("button");
    btn.id = "gemini-ask-btn";
    btn.innerHTML = `✨ Ask Gemini`;
    btn.style.left = `${e.pageX + 10}px`;
    btn.style.top = `${e.pageY + 10}px`;

    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const fullPrompt = CUSTOM_PROMPT + `"${text}"`;
      chrome.runtime.sendMessage({ action: "askGemini", prompt: fullPrompt });
      removeBtn();
    });

    document.body.appendChild(btn);
  }, 100);
});

document.addEventListener("mousedown", (e) => {
  if (btn && !btn.contains(e.target)) removeBtn();
});

function removeBtn() {
  if (btn) { btn.remove(); btn = null; }
}

// Automatically trigger Gemini when a caption card is clicked (win-caption-hook interface)
document.addEventListener("click", (e) => {
  const card = e.target.closest(".card");
  // Only trigger if a card was clicked and it wasn't the copy button (which stops propagation anyway, but let's be safe)
  if (card && !e.target.closest(".cp")) {
    // Get text, ignoring the 'copy' button text
    const textSpan = card.querySelector(".t");
    let text = textSpan ? textSpan.textContent.trim() : card.textContent.replace("copy", "").trim();
    if (text.length > 2) {
      const fullPrompt = CUSTOM_PROMPT + `"${text}"`;
      chrome.runtime.sendMessage({ action: "askGemini", prompt: fullPrompt });
    }
  }
});