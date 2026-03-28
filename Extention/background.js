function initContextMenus() {
    chrome.contextMenus.removeAll(function () {
        chrome.contextMenus.create({
            id: "askQwenContext",
            title: "Ask Qwen about this",
            contexts: ["selection"]
        });
    });
}

function initiate() {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(function () {});

    chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: [1],
        addRules: [{
            id: 1,
            priority: 1,
            action: {
                type: "modifyHeaders",
                responseHeaders: [
                    { header: "content-security-policy", operation: "remove" },
                    { header: "x-frame-options", operation: "remove" },
                    { header: "frame-options", operation: "remove" },
                    { header: "frame-ancestors", operation: "remove" },
                    { header: "X-Content-Type-Options", operation: "remove" },
                    { header: "access-control-allow-origin", operation: "set", value: "*" }
                ]
            },
            condition: {
                urlFilter: "||chat.qwen.ai/",
                resourceTypes: ["main_frame", "sub_frame"]
            }
        }]
    }).catch(function (e) { console.error("DNR rule error:", e); });

    initContextMenus();

    chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
        if (request.action === "askQwen") {
            chrome.sidePanel.open({ windowId: sender.tab.windowId }).catch(function () {});
            setTimeout(function () {
                chrome.runtime.sendMessage({
                    type: "SIDEPANEL_ASK_QWEN",
                    text: request.prompt
                }).catch(function () {});
            }, 1200);
        }
        return true;
    });

    chrome.contextMenus.onClicked.addListener(function (info, tab) {
        if (info.menuItemId === "askQwenContext" && info.selectionText) {
            var CUSTOM_PROMPT = "Answer like an experienced AWS DevOps engineer in a real interview.\n" +
                "Keep answers in point to point no big sentence. just keep 2 to 3 short bullet points.\n\n";
            var fullPrompt = CUSTOM_PROMPT + '"' + info.selectionText.trim() + '"';

            chrome.sidePanel.open({ windowId: tab.windowId }).catch(function () {});
            setTimeout(function () {
                chrome.runtime.sendMessage({
                    type: "SIDEPANEL_ASK_QWEN",
                    text: fullPrompt
                }).catch(function () {});
            }, 1200);
        }
    });
}

initiate();