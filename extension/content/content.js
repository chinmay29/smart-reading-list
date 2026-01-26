// Content script for Smart Reading List
// Runs in the context of web pages

// Listen for messages from the popup or background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getPageContent') {
        // Return the full HTML of the page
        sendResponse({
            html: document.documentElement.outerHTML,
            url: window.location.href,
            title: document.title
        });
    }

    if (request.action === 'getSelection') {
        // Return selected text (for future highlights feature)
        const selection = window.getSelection();
        sendResponse({
            text: selection ? selection.toString() : '',
            url: window.location.href
        });
    }

    return true; // Keep message channel open for async response
});

// Future: Add highlight functionality
// This will be used in Phase 2 for user selections
