let qwenFrame = document.getElementById("qwen-frame");
let isFrameReady = false;
let pendingPrompt = null;

// Show loading indicator initially
document.getElementById("loading").style.display = "block";

function askQwenInFrame(promptText) {
    if (isFrameReady) {
        try {
            console.log("Sending prompt to Qwen iframe:", promptText.substring(0, 50) + "...");
            qwenFrame.contentWindow.postMessage({
                type: "ASK_QWEN_WITH_PROMPT",
                text: promptText
            }, "https://chat.qwen.ai");
        } catch (error) {
            console.error("Error sending message to Qwen iframe:", error);
        }
    } else {
        console.log("Frame not ready, buffering prompt...");
        pendingPrompt = promptText;
    }
}

qwenFrame.onload = () => {
    console.log("Qwen iframe loaded.");
    isFrameReady = true;
    document.getElementById("loading").style.display = "none"; // Hide loading indicator

    // If there was a prompt waiting, send it now
    if (pendingPrompt) {
        askQwenInFrame(pendingPrompt);
        pendingPrompt = null; // Clear buffer
    }
};

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "SIDEPANEL_ASK_QWEN") {
        console.log("Received prompt from background script in sidepanel.js:", request.text.substring(0, 50) + "...");
        askQwenInFrame(request.text);
    }
});