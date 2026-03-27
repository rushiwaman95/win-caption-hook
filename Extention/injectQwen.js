console.log("Content script (injectQwen.js) initialized in Qwen iframe.");

// Listen for messages from the parent sidepanel.js script
window.addEventListener("message", async (event) => {
    // Important: Validate the origin for security!
    if (event.origin !== "chrome-extension://" + chrome.runtime.id) {
        console.log("Message origin mismatch, ignoring:", event.origin);
        return;
    }

    console.log("Received message in iframe:", event.data);

    if (event.data.type === "ASK_QWEN_WITH_PROMPT") {
        const promptText = event.data.text;
        console.log("Received ASK_QWEN_WITH_PROMPT command with text:", promptText.substring(0, 50) + "...");

        // Function to wait for the input area to be available
        const waitForInput = (timeout = 15000) => {
            return new Promise((resolve, reject) => {
                const startTime = Date.now();
                const check = () => {
                    // Try common selectors for Qwen's input area
                    const inputSelector = 'textarea[placeholder*="message" i], textarea[placeholder*="Message" i], [contenteditable="true"].text-input, textarea';
                    const inputArea = document.querySelector(inputSelector);
                    
                    if (inputArea) {
                        resolve(inputArea);
                    } else if (Date.now() - startTime >= timeout) {
                        reject(new Error(`Input area not found within ${timeout}ms`));
                    } else {
                        setTimeout(check, 500);
                    }
                };
                check();
            });
        };

        try {
            const inputArea = await waitForInput();
            console.log("Found input area:", inputArea);

            // Clear the input area (optional, might help start a new conversation segment)
            // Note: Clearing might be tricky depending on how Qwen handles its input
            // A safer approach is often just appending/prepending, but for a new query, clearing is ideal if possible.
            // Let's try focusing and replacing value first.
            inputArea.focus();
            if (inputArea.tagName === 'TEXTAREA' || inputArea.tagName === 'INPUT') {
                 // Method 1: Set value and dispatch input
                 inputArea.value = promptText;
                 inputArea.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
                 // Optional: Dispatch change event too
                 inputArea.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
                 
            } else if (inputArea.isContentEditable) {
                 // Method 2: For contenteditable divs
                 inputArea.textContent = promptText; // Or innerHTML if needed, be careful with XSS
                 // Dispatch input event for contenteditable
                 inputArea.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: promptText }));
            } else {
                 // Fallback: try setting innerText
                 inputArea.innerText = promptText;
                 inputArea.dispatchEvent(new InputEvent('input', { bubbles: true }));
            }

            console.log("Prompt inserted into input area.");

            // Find and click the send button
            const sendButtonSelector = 'button[aria-label*="send" i], button[aria-label*="Send" i], button[type="submit"], .send-button, [data-testid*="send"]';
            const sendButton = document.querySelector(sendButtonSelector);

            if (sendButton) {
                console.log("Found send button, attempting to click.");
                // Simulate a click on the send button
                sendButton.click();
            } else {
                console.warn("Send button not found using common selectors. Trying Enter key in input.");
                // Fallback: Simulate pressing Enter in the input area
                inputArea.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
            }

        } catch (error) {
            console.error("Error filling input or sending:", error);
            // Potentially notify the sidepanel.js script about the failure
             chrome.runtime.sendMessage({
                type: "SIDEPANEL_INJECT_ERROR",
                error: error.message
            }).catch(e => console.error("Could not send error back to side panel:", e));
        }
    }
});