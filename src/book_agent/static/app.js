/**
 * Book Agent Editor - Main Application JavaScript
 */

// Application state
const state = {
    currentFile: null,
    currentContent: '',
    originalContent: '',
    isEditMode: false,
    isLoading: false,
    activeTaskId: null,
    eventSource: null,
    conversationHistory: []  // Track conversation for context
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    setupEventListeners();
    configureMarked();
});

// Configure marked.js for markdown rendering
function configureMarked() {
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });
}

// Setup event listeners
function setupEventListeners() {
    // Handle Enter key in agent input (Shift+Enter for newline)
    const agentInput = document.getElementById('agentInput');
    agentInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendToAgent();
        }
    });

    // Track content changes in editor
    const editorTextarea = document.getElementById('editorTextarea');
    editorTextarea.addEventListener('input', () => {
        state.currentContent = editorTextarea.value;
        updateSaveButtonState();
    });
}

// Load files from the server
async function loadFiles() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '<div class="loading">Loading files...</div>';

    try {
        const response = await fetch('/api/files');
        const data = await response.json();

        if (data.files.length === 0) {
            fileList.innerHTML = '<div class="loading">No files found in output folder</div>';
            return;
        }

        // Group files by folder
        const grouped = groupFilesByFolder(data.files);
        fileList.innerHTML = renderFileTree(grouped);

    } catch (error) {
        console.error('Error loading files:', error);
        fileList.innerHTML = '<div class="loading">Error loading files</div>';
    }
}

// Group files by their parent folder
function groupFilesByFolder(files) {
    const grouped = {};

    files.forEach(file => {
        const parts = file.path.split('/');
        const folder = parts.length > 1 ? parts[0] : 'root';

        if (!grouped[folder]) {
            grouped[folder] = [];
        }
        grouped[folder].push(file);
    });

    return grouped;
}

// Render the file tree HTML
function renderFileTree(grouped) {
    let html = '';

    // Sort folders, putting 'chapters' first
    const folders = Object.keys(grouped).sort((a, b) => {
        if (a === 'chapters') return -1;
        if (b === 'chapters') return 1;
        return a.localeCompare(b);
    });

    folders.forEach(folder => {
        if (folder !== 'root') {
            html += `<div class="file-folder">${folder}</div>`;
        }

        grouped[folder].forEach(file => {
            const icon = getFileIcon(file.name);
            const activeClass = state.currentFile === file.path ? 'active' : '';

            html += `
                <div class="file-item ${activeClass}" onclick="selectFile('${file.path}')" title="${file.path}">
                    ${icon}
                    <span class="file-name">${file.name}</span>
                </div>
            `;
        });
    });

    return html;
}

// Get icon SVG based on file type
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();

    if (ext === 'md') {
        return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
        </svg>`;
    }

    if (ext === 'json') {
        return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <path d="M8 13h2"/>
            <path d="M8 17h2"/>
        </svg>`;
    }

    return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
    </svg>`;
}

// Close the current file
function closeFile() {
    // Check for unsaved changes
    if (state.currentContent !== state.originalContent) {
        if (!confirm('You have unsaved changes. Discard them?')) {
            return;
        }
    }

    // Clear state
    state.currentFile = null;
    state.currentContent = '';
    state.originalContent = '';
    state.isEditMode = false;

    // Update UI
    document.getElementById('editorTitle').textContent = 'Select a file';
    document.getElementById('toggleMode').disabled = true;
    document.getElementById('saveBtn').disabled = true;
    document.getElementById('closeBtn').style.display = 'none';

    // Show placeholder, hide editor/preview
    document.querySelector('.editor-placeholder').style.display = 'block';
    document.getElementById('markdownPreview').style.display = 'none';
    document.getElementById('editorTextarea').style.display = 'none';

    // Clear file list selection
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('active');
    });

    addAgentMessage('File closed.', 'assistant');
}

// Select and load a file
async function selectFile(filePath) {
    // Check for unsaved changes
    if (state.currentContent !== state.originalContent) {
        if (!confirm('You have unsaved changes. Discard them?')) {
            return;
        }
    }

    state.currentFile = filePath;
    state.isEditMode = false;

    // Update file list selection
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');

    // Update editor title
    const fileName = filePath.split('/').pop();
    document.getElementById('editorTitle').textContent = fileName;

    // Show close button
    document.getElementById('closeBtn').style.display = 'inline-flex';

    // Enable buttons
    document.getElementById('toggleMode').disabled = false;
    document.getElementById('saveBtn').disabled = true;

    // Load file content
    try {
        const response = await fetch(`/api/file/${encodeURIComponent(filePath)}`);
        const data = await response.json();

        state.currentContent = data.content;
        state.originalContent = data.content;

        // Show preview mode by default
        showPreviewMode();

        // Add status message to agent
        addAgentMessage(`Loaded file: **${fileName}**`, 'assistant');

    } catch (error) {
        console.error('Error loading file:', error);
        showToast('Error loading file', 'error');
    }
}

// Show markdown preview mode
function showPreviewMode() {
    const preview = document.getElementById('markdownPreview');
    const textarea = document.getElementById('editorTextarea');
    const placeholder = document.querySelector('.editor-placeholder');
    const modeLabel = document.getElementById('modeLabel');

    placeholder.style.display = 'none';
    textarea.style.display = 'none';
    preview.style.display = 'block';

    // Render markdown
    preview.innerHTML = marked.parse(state.currentContent);

    // Apply syntax highlighting to code blocks
    preview.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    modeLabel.textContent = 'Edit';
    state.isEditMode = false;
}

// Show edit mode
function showEditMode() {
    const preview = document.getElementById('markdownPreview');
    const textarea = document.getElementById('editorTextarea');
    const placeholder = document.querySelector('.editor-placeholder');
    const modeLabel = document.getElementById('modeLabel');

    placeholder.style.display = 'none';
    preview.style.display = 'none';
    textarea.style.display = 'block';

    textarea.value = state.currentContent;
    textarea.focus();

    modeLabel.textContent = 'Preview';
    state.isEditMode = true;
}

// Toggle between edit and preview mode
function toggleEditMode() {
    if (state.isEditMode) {
        // Save textarea content before switching
        state.currentContent = document.getElementById('editorTextarea').value;
        showPreviewMode();
    } else {
        showEditMode();
    }
}

// Update save button state based on changes
function updateSaveButtonState() {
    const saveBtn = document.getElementById('saveBtn');
    saveBtn.disabled = state.currentContent === state.originalContent;
}

// Save the current file
async function saveFile() {
    if (!state.currentFile) return;

    const saveBtn = document.getElementById('saveBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = 'Saving...';
    saveBtn.disabled = true;

    try {
        const response = await fetch(`/api/file/${encodeURIComponent(state.currentFile)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: state.currentFile,
                content: state.currentContent
            })
        });

        if (response.ok) {
            state.originalContent = state.currentContent;
            showToast('File saved successfully', 'success');
            addAgentMessage(`Saved file: **${state.currentFile.split('/').pop()}**`, 'assistant');
        } else {
            throw new Error('Save failed');
        }

    } catch (error) {
        console.error('Error saving file:', error);
        showToast('Error saving file', 'error');
    } finally {
        saveBtn.innerHTML = originalText;
        updateSaveButtonState();
    }
}

// Send prompt to the agent
async function sendToAgent() {
    const input = document.getElementById('agentInput');
    const prompt = input.value.trim();

    if (!prompt || state.isLoading) return;

    state.isLoading = true;
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;

    // Add user message to UI
    addAgentMessage(prompt, 'user');
    input.value = '';

    // Add loading indicator
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('/api/agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                file_content: state.currentFile ? state.currentContent : null,
                file_path: state.currentFile,
                history: state.conversationHistory
            })
        });

        const data = await response.json();

        // Remove loading indicator
        removeLoadingMessage(loadingId);

        if (response.ok) {
            // Add to conversation history (without file content)
            state.conversationHistory.push({ role: 'user', content: prompt });
            state.conversationHistory.push({ role: 'assistant', content: data.response });

            // Keep history manageable (last 20 messages)
            if (state.conversationHistory.length > 20) {
                state.conversationHistory = state.conversationHistory.slice(-20);
            }

            addAgentMessage(data.response, 'assistant');

            // Check if this is a book edit task with a task_id
            if (data.task_id) {
                state.activeTaskId = data.task_id;
                subscribeToTaskUpdates(data.task_id);
            }
        } else {
            addAgentMessage(`Error: ${data.detail || 'Unknown error'}`, 'assistant');
        }

    } catch (error) {
        console.error('Agent error:', error);
        removeLoadingMessage(loadingId);
        addAgentMessage('Error: Could not connect to agent', 'assistant');
    } finally {
        state.isLoading = false;
        submitBtn.disabled = false;
    }
}

// Subscribe to task status updates via SSE
function subscribeToTaskUpdates(taskId, progressId = null, retryCount = 0) {
    const maxRetries = 5;
    const retryDelay = 2000; // 2 seconds

    // Close any existing connection
    if (state.eventSource) {
        state.eventSource.close();
    }

    // Add a progress container (only on first call)
    if (!progressId) {
        progressId = addProgressMessage(taskId);
    }

    state.eventSource = new EventSource(`/api/task/${taskId}/stream`);

    state.eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'message') {
            updateProgressMessage(progressId, data);
        }

        if (data.type === 'complete' || data.completed) {
            state.eventSource.close();
            state.eventSource = null;
            state.activeTaskId = null;

            // Finalize progress message
            finalizeProgressMessage(progressId, data.error);

            // Refresh the file list to show updated content
            loadFiles();

            // If a file is currently open, reload it
            if (state.currentFile) {
                reloadCurrentFile();
            }
        }
    };

    state.eventSource.onerror = async () => {
        console.error('SSE connection error');
        state.eventSource.close();
        state.eventSource = null;

        // Try to reconnect
        if (retryCount < maxRetries) {
            addLogToProgress(progressId, `Connection lost. Reconnecting (${retryCount + 1}/${maxRetries})...`);

            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, retryDelay));

            // Check if task is still active before reconnecting
            try {
                const response = await fetch(`/api/task/${taskId}`);
                if (response.ok) {
                    const taskData = await response.json();
                    if (!taskData.completed) {
                        subscribeToTaskUpdates(taskId, progressId, retryCount + 1);
                        return;
                    } else {
                        // Task completed while disconnected
                        finalizeProgressMessage(progressId, taskData.error);
                        loadFiles();
                        if (state.currentFile) reloadCurrentFile();
                        return;
                    }
                }
            } catch (e) {
                console.error('Failed to check task status:', e);
            }
        }

        state.activeTaskId = null;
        addAgentMessage('Connection lost. Check task status manually or refresh the page.', 'assistant');
    };
}

// Add a log entry to existing progress message
function addLogToProgress(progressId, message) {
    const progressDiv = document.getElementById(progressId);
    if (!progressDiv) return;

    const progressLog = progressDiv.querySelector('.progress-log');
    if (progressLog) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = message;
        progressLog.appendChild(logEntry);
        progressLog.scrollTop = progressLog.scrollHeight;
    }
}

// Add progress message container
function addProgressMessage(taskId) {
    const messagesContainer = document.getElementById('agentMessages');
    const progressDiv = document.createElement('div');
    const progressId = 'progress-' + taskId;

    progressDiv.id = progressId;
    progressDiv.className = 'agent-message assistant progress-message';
    progressDiv.innerHTML = `
        <div class="progress-header">
            <strong>Book Edit Progress</strong>
            <button class="cancel-task-btn" onclick="cancelTask('${taskId}')" title="Cancel">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <div class="progress-bar-container">
            <div class="progress-bar" style="width: 0%"></div>
        </div>
        <div class="progress-status">Starting...</div>
        <div class="progress-log"></div>
    `;

    messagesContainer.appendChild(progressDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return progressId;
}

// Update progress message
function updateProgressMessage(progressId, data) {
    const progressDiv = document.getElementById(progressId);
    if (!progressDiv) return;

    const progressBar = progressDiv.querySelector('.progress-bar');
    const progressStatus = progressDiv.querySelector('.progress-status');
    const progressLog = progressDiv.querySelector('.progress-log');

    // Update progress bar
    const percent = data.total > 0 ? Math.round((data.progress / data.total) * 100) : 0;
    progressBar.style.width = `${percent}%`;

    // Update status
    progressStatus.textContent = `${data.progress} of ${data.total} chapters (${percent}%)`;

    // Add log message
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = data.message;
    progressLog.appendChild(logEntry);

    // Scroll to show latest log
    progressLog.scrollTop = progressLog.scrollHeight;

    // Scroll messages container
    const messagesContainer = document.getElementById('agentMessages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Finalize progress message
function finalizeProgressMessage(progressId, error) {
    const progressDiv = document.getElementById(progressId);
    if (!progressDiv) return;

    const progressBar = progressDiv.querySelector('.progress-bar');
    const cancelBtn = progressDiv.querySelector('.cancel-task-btn');

    if (cancelBtn) {
        cancelBtn.remove();
    }

    if (error) {
        progressBar.classList.add('error');
        progressDiv.querySelector('.progress-status').textContent = `Error: ${error}`;
    } else {
        progressBar.style.width = '100%';
        progressBar.classList.add('complete');
        progressDiv.querySelector('.progress-status').textContent = 'Completed!';
    }
}

// Cancel a running task
async function cancelTask(taskId) {
    try {
        await fetch(`/api/task/${taskId}/cancel`, { method: 'POST' });
        addAgentMessage('Cancellation requested...', 'assistant');
    } catch (error) {
        console.error('Error cancelling task:', error);
    }
}

// Reload current file
async function reloadCurrentFile() {
    if (!state.currentFile) return;

    try {
        const response = await fetch(`/api/file/${encodeURIComponent(state.currentFile)}`);
        const data = await response.json();

        state.currentContent = data.content;
        state.originalContent = data.content;

        // Refresh the view
        if (state.isEditMode) {
            document.getElementById('editorTextarea').value = data.content;
        } else {
            showPreviewMode();
        }

        showToast('File reloaded with updates', 'success');
    } catch (error) {
        console.error('Error reloading file:', error);
    }
}

// Add a message to the agent chat
function addAgentMessage(content, role) {
    const messagesContainer = document.getElementById('agentMessages');

    // Remove welcome message if present
    const welcome = messagesContainer.querySelector('.agent-welcome');
    if (welcome) {
        welcome.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `agent-message ${role}`;

    if (role === 'assistant') {
        // Render markdown for assistant messages
        messageDiv.innerHTML = marked.parse(content);
    } else {
        messageDiv.textContent = content;
    }

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add loading message
function addLoadingMessage() {
    const messagesContainer = document.getElementById('agentMessages');
    const loadingDiv = document.createElement('div');
    const loadingId = 'loading-' + Date.now();

    loadingDiv.id = loadingId;
    loadingDiv.className = 'agent-message assistant loading';
    loadingDiv.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return loadingId;
}

// Remove loading message
function removeLoadingMessage(loadingId) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Clear the agent chat
function clearChat() {
    // Cancel any active task
    if (state.activeTaskId) {
        cancelTask(state.activeTaskId);
    }

    // Close SSE connection
    if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
    }

    // Clear conversation history
    state.conversationHistory = [];

    const messagesContainer = document.getElementById('agentMessages');
    messagesContainer.innerHTML = `
        <div class="agent-welcome">
            <p>Welcome! I'm your writing assistant. I can help you:</p>
            <ul>
                <li>Review and improve your content</li>
                <li>Suggest edits and fixes</li>
                <li>Answer questions about your writing</li>
                <li>Help with formatting and structure</li>
            </ul>
            <p><strong>Book Editing:</strong> To edit chapters, include "chapter" or "all chapters" in your prompt.</p>
            <p>Select a file and ask me anything!</p>
        </div>
    `;
}

// Show toast notification
function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
