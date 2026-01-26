// Background service worker for Smart Reading List extension

const API_BASE = 'http://localhost:8000/api';

// Handle extension icon click (alternative to popup)
chrome.action.onClicked.addListener(async (tab) => {
    // This only fires if no popup is defined
    // We have a popup, so this is just for future keyboard shortcut support
});

// Handle keyboard shortcuts (if defined in manifest)
chrome.commands?.onCommand?.addListener(async (command) => {
    if (command === 'save-article') {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab) {
            await quickSave(tab);
        }
    }
});

// Quick save without popup (for keyboard shortcuts)
async function quickSave(tab) {
    try {
        // Get page HTML
        const [result] = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => document.documentElement.outerHTML
        });

        const response = await fetch(`${API_BASE}/documents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: tab.url,
                title: tab.title,
                html_content: result.result,
                tags: [],
                source_type: 'web_article'
            })
        });

        if (response.ok) {
            // Show success badge
            chrome.action.setBadgeText({ text: '✓', tabId: tab.id });
            chrome.action.setBadgeBackgroundColor({ color: '#2ed573', tabId: tab.id });

            setTimeout(() => {
                chrome.action.setBadgeText({ text: '', tabId: tab.id });
            }, 2000);
        } else {
            throw new Error('Save failed');
        }

    } catch (error) {
        console.error('Quick save error:', error);
        chrome.action.setBadgeText({ text: '!', tabId: tab.id });
        chrome.action.setBadgeBackgroundColor({ color: '#ff4757', tabId: tab.id });
    }
}

// Check backend health periodically
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        return response.ok;
    } catch {
        return false;
    }
}

// Log startup
console.log('Smart Reading List extension loaded');
