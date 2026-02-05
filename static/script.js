let currentSessionId = null;
let currentSessionType = 'table';
let autoSaveTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
    
    // File Input Listener
    const fileInput = document.getElementById('fileInput');
    if(fileInput) {
        fileInput.addEventListener('change', function() {
            console.log("File selected:", this.files);
            handleFiles(this.files);
            this.value = ''; // Reset so the same file can be selected again
        });
    }
    
    const dropZone = document.getElementById('upload-zone');
    if(dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.backgroundColor = '#f1f8ff';
        });
        
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.backgroundColor = 'white';
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.backgroundColor = 'white';
            handleFiles(e.dataTransfer.files);
        });
    }
});

async function handleFiles(files) {
    console.log("Processing files...", files);
    if (!files.length) return;
    
    const loader = document.getElementById('loader');
    const uploadZone = document.getElementById('upload-zone');
    
    loader.style.display = 'block';
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', currentSessionType);
        
        try {
            const response = await fetch('/ocr', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'OCR Failed');
            }
            
            const data = await response.json();
            addTableToWorkspace(data.html, data.filename);
            
        } catch (err) {
            console.error(err);
            alert(`Error processing ${file.name}: ${err.message}`);
        }
    }
    
    loader.style.display = 'none';
    uploadZone.style.display = 'none'; // Hide big dropzone after first upload
    
    autoSave(); // Trigger save after adding files
}

function addTableToWorkspace(htmlContent, title = "Table") {
    const wrapper = document.getElementById('tables-wrapper');
    const id = 'tbl-' + Date.now() + Math.random().toString(36).substr(2, 9);
    
    const div = document.createElement('div');
    div.className = 'table-container generated-content';
    div.id = id;
    
    let contentHtml = '';
    if (currentSessionType === 'text') {
        // Text mode: Render as a pre-like editable div
        contentHtml = `<div class="p-3 border rounded bg-light text-content" style="white-space: pre-wrap; font-family: monospace;" contenteditable="true">${htmlContent}</div>`;
    } else {
        // Table mode: Render as responsive table container
        contentHtml = `<div class="table-responsive table-content">${htmlContent}</div>`;
    }
    
    // Header for the block
    div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2 border-bottom pb-2">
            <div class="form-check">
                <input class="form-check-input table-selector" type="checkbox" value="${id}" id="check-${id}">
                <label class="form-check-label fw-bold" for="check-${id}">${title}</label>
            </div>
            <button class="btn btn-sm btn-outline-danger" onclick="removeTable('${id}')"><i class="bi bi-trash"></i></button>
        </div>
        ${contentHtml}
    `;
    
    wrapper.appendChild(div);
    makeEditable(div);
}

function makeEditable(container) {
    if (currentSessionType === 'text') {
        const textDiv = container.querySelector('.text-content');
        if (textDiv) {
            textDiv.addEventListener('input', () => {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(autoSave, 1000);
            });
        }
    } else {
        const cells = container.querySelectorAll('th, td');
        cells.forEach(cell => {
            cell.contentEditable = true;
            cell.classList.add('editable-cell');
            
            // Auto-save on input
            cell.addEventListener('input', () => {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(autoSave, 1000); // Debounce 1s
            });
        });
    }
}

function removeTable(id) {
    // Removed confirmation as requested
    const el = document.getElementById(id);
    if (el) {
        el.remove();
        autoSave();
    }
}

function mergeSelectedTables() {
    const checkboxes = document.querySelectorAll('.table-selector:checked');
    if (checkboxes.length < 2) {
        alert("Select at least 2 tables to merge.");
        return;
    }
    
    const selectedIds = Array.from(checkboxes).map(cb => cb.value);
    const containers = selectedIds.map(id => document.getElementById(id));
    
    // Strategy: Use first table as base. Append rows from others.
    const baseContainer = containers[0];
    const baseTable = baseContainer.querySelector('table');
    const baseTbody = baseTable.querySelector('tbody');
    
    // If base table doesn't have tbody (some HTML might differ), wrap it
    if (!baseTbody) {
        alert("Table structure incompatible for auto-merge.");
        return;
    }

    for (let i = 1; i < containers.length; i++) {
        const targetTable = containers[i].querySelector('table');
        const rows = targetTable.querySelectorAll('tbody tr');
        rows.forEach(row => {
            // Clone row
            const newRow = row.cloneNode(true);
            baseTbody.appendChild(newRow);
        });
        
        // Remove the merged table container
        containers[i].remove();
    }
    
    // Make new rows editable
    makeEditable(baseContainer);
    
    // Update title
    baseContainer.querySelector('label').innerText += " (Merged)";
    
    // Uncheck
    checkboxes[0].checked = false;
    
    autoSave();
}

async function autoSave() {
    const wrapper = document.getElementById('tables-wrapper');
    if (!wrapper) return;
    
    // Don't save if empty and no session ID (clean state)
    if (wrapper.innerHTML.trim() === "" && !currentSessionId) return;

    let title = document.getElementById('session-title').innerText;
    const html = wrapper.innerHTML;
    
    try {
        const response = await fetch('/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: title, 
                content: html,
                id: currentSessionId 
            })
        });
        
        const res = await response.json();
        if (res.status === 'success') {
            currentSessionId = res.id;
            loadHistory(); // Update timestamps in list
            
            // Optional: Visual indicator that save happened
            const statusIndicator = document.getElementById('session-title');
            const originalColor = statusIndicator.style.color;
            statusIndicator.style.color = 'green';
            setTimeout(() => {
                statusIndicator.style.color = originalColor;
            }, 500);
        }
    } catch(e) {
        console.error("Auto-save failed", e);
    }
}

async function saveCurrentWork() {
    // Manual trigger allows renaming
    const currentName = document.getElementById('session-title').innerText;
    const name = prompt("Name this session:", currentName);
    
    if (name) {
        document.getElementById('session-title').innerText = name;
        await autoSave();
    }
}

async function loadHistory() {
    const list = document.getElementById('history-list');
    if(!list) return;

    const response = await fetch('/history');
    const files = await response.json();
    
    list.innerHTML = '';
    files.forEach(f => {
        const item = document.createElement('div');
        item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
        
        // Content area acts as load button
        const contentDiv = document.createElement('div');
        contentDiv.style.flexGrow = '1';
        contentDiv.style.cursor = 'pointer';
        contentDiv.innerHTML = `
            <h6 class="mb-1">${f.name}</h6>
            <small class="text-muted">${f.timestamp}</small>
        `;
        contentDiv.onclick = () => loadSession(f);
        
        // Delete button
        const delBtn = document.createElement('button');
        delBtn.className = 'btn btn-sm btn-outline-danger ms-2';
        delBtn.innerHTML = '<i class="bi bi-trash"></i>';
        delBtn.onclick = (e) => {
            e.stopPropagation(); // Prevent loading session when deleting
            deleteSession(f.id);
        };
        
        item.appendChild(contentDiv);
        item.appendChild(delBtn);
        list.appendChild(item);
    });
}

async function deleteSession(id) {
    if(!confirm("Delete this session?")) return;
    
    try {
        const response = await fetch('/session/' + id, { method: 'DELETE' });
        if(response.ok) {
            if(currentSessionId === id) {
                startNewSession(); // Reset if we deleted the active session
            }
            loadHistory();
        } else {
            alert("Failed to delete session");
        }
    } catch(e) {
        console.error(e);
        alert("Error deleting session");
    }
}

function loadSession(sessionData) {
    // Removed confirmation as requested
    currentSessionId = sessionData.id;
    
    const wrapper = document.getElementById('tables-wrapper');
    wrapper.innerHTML = sessionData.content;
    
    // Infer type based on content
    if (wrapper.querySelector('.text-content')) {
        currentSessionType = 'text';
        document.getElementById('session-title').innerHTML = `<i class="bi bi-file-text"></i> ${sessionData.name}`;
    } else {
        currentSessionType = 'table';
        document.getElementById('session-title').innerHTML = `<i class="bi bi-table"></i> ${sessionData.name}`;
    }

    document.getElementById('upload-zone').style.display = 'none';
    
    // Re-attach listeners because innerHTML replaced elements
    const containers = wrapper.querySelectorAll('.generated-content');
    containers.forEach(div => makeEditable(div));
}

function startNewSession(type = 'table') {
    currentSessionType = type;
    document.getElementById('tables-wrapper').innerHTML = '';
    document.getElementById('upload-zone').style.display = 'block';
    
    const titleEl = document.getElementById('session-title');
    const loaderText = document.getElementById('loader-text');
    
    if (type === 'table') {
        titleEl.innerHTML = '<i class="bi bi-table"></i> Untitled Session (Table)';
        if(loaderText) loaderText.innerText = "Extracting tables...";
    } else {
        titleEl.innerHTML = '<i class="bi bi-file-text"></i> Untitled Session (Text)';
        if(loaderText) loaderText.innerText = "Extracting text...";
    }
    
    currentSessionId = null;
}

function exportToCSV() {
    const tables = document.querySelectorAll('#tables-wrapper table');
    if (tables.length === 0) {
        alert("No tables to export");
        return;
    }
    
    let csvContent = "data:text/csv;charset=utf-8,";
    
    tables.forEach((table, index) => {
        if(index > 0) csvContent += "\n\n--- Table " + (index+1) + " ---\n";
        
        const rows = table.querySelectorAll("tr");
        rows.forEach(row => {
            const cols = row.querySelectorAll("td, th");
            const rowData = Array.from(cols).map(c => '"' + c.innerText.replace( /"/g, '""') + '"').join(",");
            csvContent += rowData + "\r\n";
        });
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "extracted_tables.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportToTXT() {
    const containers = document.querySelectorAll('.generated-content');
    if (containers.length === 0) {
        alert("No content to export");
        return;
    }
    
    let txtContent = "";
    
    containers.forEach((container, index) => {
        if(index > 0) txtContent += "\n\n" + "=".repeat(20) + "\n\n";
        
        // Check if text mode or table mode content
        const textContent = container.querySelector('.text-content');
        if (textContent) {
             txtContent += textContent.innerText;
        } else {
             // Fallback for table mode: simplistic text dump
             const table = container.querySelector('table');
             if(table) txtContent += table.innerText;
        }
    });
    
    const blob = new Blob([txtContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "extracted_text.txt");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}