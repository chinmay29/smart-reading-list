// Popup script for Smart Reading List extension

const API_BASE = 'http://localhost:8000/api';

// DOM Elements
const articleTitle = document.getElementById('article-title');
const articleUrl = document.getElementById('article-url');
const tagsInput = document.getElementById('tags');
const saveBtn = document.getElementById('save-btn');
const btnText = saveBtn.querySelector('.btn-text');
const btnLoading = saveBtn.querySelector('.btn-loading');
const statusDiv = document.getElementById('status');

// Current tab info
let currentTab = null;

// Initialize popup
async function init() {
    try {
        // Get current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        currentTab = tab;

        articleTitle.textContent = tab.title || 'Untitled';
        articleUrl.textContent = tab.url;

        // Load saved tags for this URL (if previously saved)
        const saved = await chrome.storage.local.get(tab.url);
        if (saved[tab.url]) {
            tagsInput.value = saved[tab.url].tags || '';
        }
    } catch (error) {
        showStatus('Failed to get page info', 'error');
    }
}

// Save article
async function saveArticle() {
    if (!currentTab) {
        showStatus('No page to save', 'error');
        return;
    }

    // Update UI to loading state
    setLoading(true);
    hideStatus();

    try {
        // Get page HTML from content script
        const [result] = await chrome.scripting.executeScript({
            target: { tabId: currentTab.id },
            func: () => document.documentElement.outerHTML
        });

        const htmlContent = result.result;

        // Parse tags
        const tags = tagsInput.value
            .split(',')
            .map(t => t.trim().toLowerCase())
            .filter(t => t.length > 0);

        // Send to backend
        const response = await fetch(`${API_BASE}/documents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentTab.url,
                title: currentTab.title,
                html_content: htmlContent,
                tags: tags,
                source_type: 'web_article'
            })
        });

        if (response.ok) {
            const data = await response.json();

            // Save tags for quick access
            await chrome.storage.local.set({
                [currentTab.url]: { tags: tagsInput.value, savedAt: Date.now() }
            });

            showStatus('✓ Article saved! Summary generating...', 'success');

            // Update button to show saved state
            btnText.textContent = 'Saved!';
            saveBtn.disabled = true;

        } else if (response.status === 409) {
            showStatus('Article already saved', 'error');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save');
        }

    } catch (error) {
        console.error('Save error:', error);

        if (error.message.includes('Failed to fetch')) {
            showStatus('Backend not running. Start the server first.', 'error');
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
    } finally {
        setLoading(false);
    }
}

// UI Helpers
function setLoading(loading) {
    saveBtn.disabled = loading;
    btnText.classList.toggle('hidden', loading);
    btnLoading.classList.toggle('hidden', !loading);
}

function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
}

function hideStatus() {
    statusDiv.className = 'status hidden';
}

// Event listeners
saveBtn.addEventListener('click', saveArticle);

// Allow Enter key in tags input to save
tagsInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        saveArticle();
    }
});

// Initialize
init();
