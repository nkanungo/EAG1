const BACKEND_BASE = 'http://127.0.0.1:8000'; // Change if needed

// UI Elements
const logBtn = document.getElementById('log-page-btn');
const summarizeBtn = document.getElementById('summarize-btn');
const askInput = document.getElementById('ask-input');
const askBtn = document.getElementById('ask-btn');
const resultsDiv = document.getElementById('results');
const indexedPagesList = document.getElementById('indexed-pages-list');
const backendStatus = document.getElementById('backend-status');
const showStatsBtn = document.getElementById('show-stats-btn');
const statsModal = document.getElementById('stats-modal');
const statsContent = document.getElementById('stats-content');
const closeStats = document.getElementById('close-stats');

// Utility: Get current tab URL
async function getCurrentTabUrl() {
  return new Promise((resolve) => {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      resolve(tabs[0].url);
    });
  });
}

// Backend status check
async function checkBackendStatus() {
  try {
    const res = await fetch(`${BACKEND_BASE}/health`);
    if (res.ok) {
      backendStatus.classList.add('online');
      backendStatus.classList.remove('offline');
      backendStatus.title = 'Backend Online';
    } else {
      throw new Error();
    }
  } catch {
    backendStatus.classList.remove('online');
    backendStatus.classList.add('offline');
    backendStatus.title = 'Backend Offline';
  }
}

// Log page
logBtn.addEventListener('click', async () => {
  const url = await getCurrentTabUrl();
  logBtn.disabled = true;
  logBtn.textContent = 'Indexing...';
  fetch(`${BACKEND_BASE}/log_page`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(res => res.json())
    .then(data => {
      logBtn.textContent = 'Index My Information';
      logBtn.disabled = false;
      resultsDiv.textContent = 'Page indexed successfully!';
      listIndexedPages();
    })
    .catch(() => {
      logBtn.textContent = 'Index My Information';
      logBtn.disabled = false;
      resultsDiv.textContent = 'Error indexing page.';
    });
});

// Summarize page
summarizeBtn.addEventListener('click', async () => {
  const url = await getCurrentTabUrl();
  summarizeBtn.disabled = true;
  summarizeBtn.textContent = 'Quick Snapshot';
  fetch(`${BACKEND_BASE}/summary`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(res => res.json())
    .then(data => {
      summarizeBtn.textContent = 'Summarize Page';
      summarizeBtn.disabled = false;
      let summary = data.summary;
      if (summary) {
        // Remove markdown code block if present
        const match = summary.match(/{[\s\S]*}/);
        if (match) {
          try {
            const parsed = JSON.parse(match[0]);
            resultsDiv.innerHTML = parsed.answer.replace(/\n/g, '<br>');
          } catch {
            resultsDiv.textContent = summary;
          }
        } else {
          resultsDiv.textContent = summary;
        }
      } else {
        resultsDiv.textContent = data.error || 'No summary.';
      }
    })
    .catch(() => {
      summarizeBtn.textContent = 'Summarize Page';
      summarizeBtn.disabled = false;
      resultsDiv.textContent = 'Error summarizing.';
    });
});

// Render results using found_answer and source_urls from backend
function renderResults(data) {
  if (!data) return resultsDiv.textContent = '';
  if (data.answer) {
    resultsDiv.innerHTML = `<div style=\"margin-bottom:10px;\">${data.answer.replace(/\n/g, '<br>')}</div>`;
  }
  // Only show URLs if answer is found and source_urls is a non-empty array
  if (data.found_answer && Array.isArray(data.source_urls) && data.source_urls.length > 0) {
    data.source_urls.forEach(url => {
      const info = document.createElement('div');
      info.style.fontSize = '0.97em';
      info.style.margin = '7px 0 0 0';
      info.innerHTML = `From: <a href='${url}' target='_blank' rel='noopener noreferrer' style='color:#0078d7;text-decoration:underline;'>${url}</a>`;
      resultsDiv.appendChild(info);
    });
  }
}

// Ask about page
askBtn.addEventListener('click', async () => {
  const url = await getCurrentTabUrl();
  const query = askInput.value.trim();
  if (!query) return;
  askBtn.disabled = true;
  askBtn.textContent = 'Searching...';
  fetch(`${BACKEND_BASE}/user_query`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query, k: 5})
  })
    .then(res => res.json())
    .then(data => {
      askBtn.textContent = 'Search';
      askBtn.disabled = false;
      renderResults(data);
      // Optionally, add highlight logic here
    })
    .catch(() => {
      askBtn.textContent = 'Search';
      askBtn.disabled = false;
      resultsDiv.textContent = 'Error querying.';
    });
});

// List indexed pages
async function listIndexedPages() {
  indexedPagesList.innerHTML = '<li>Loading...</li>';
  fetch(`${BACKEND_BASE}/list_pages`)
    .then(res => res.json())
    .then(data => {
      indexedPagesList.innerHTML = '';
      (data.urls || []).forEach(url => {
        const li = document.createElement('li');
        // Create a hyperlink instead of showing the full URL
        let displayText;
        try {
          const u = new URL(url);
          // Show domain + path, truncate if too long
          displayText = u.hostname + u.pathname;
          if (displayText.length > 40) {
            displayText = displayText.slice(0, 37) + '...';
          }
        } catch {
          displayText = url;
        }
        const a = document.createElement('a');
        a.href = url;
        a.textContent = displayText;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.style.color = '#0078d7';
        a.style.textDecoration = 'underline';
        a.style.flex = '1';
        a.style.fontSize = '0.81em'; // Further reduced font size for URL links to fit more text
        a.style.whiteSpace = 'nowrap'; // Prevent wrapping
        a.style.overflow = 'hidden';
        a.style.textOverflow = 'ellipsis';
        a.title = url; // Show full URL on hover
        // Add hyperlink to li
        li.appendChild(a);
        // Add delete button
        const delBtn = document.createElement('button');
        delBtn.textContent = '🗑️';
        delBtn.title = 'Delete from index';
        delBtn.onclick = () => deletePage(url);
        li.appendChild(delBtn);
        li.style.gap = '10px';
        indexedPagesList.appendChild(li);
      });
      if ((data.urls || []).length === 0) {
        indexedPagesList.innerHTML = '<li>No pages indexed.</li>';
      }
    });
}

// Delete page
async function deletePage(url) {
  fetch(`${BACKEND_BASE}/delete_page`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(res => res.json())
    .then(data => {
      listIndexedPages();
      resultsDiv.textContent = `Deleted: ${url}`;
    });
}

// Show stats modal
showStatsBtn.addEventListener('click', () => {
  statsModal.classList.remove('hidden');
  fetch(`${BACKEND_BASE}/faiss_stats`)
    .then(res => res.json())
    .then(data => {
      statsContent.innerHTML = `
        <div style="padding:10px 0 0 0;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <span style="font-size:1.2em;font-weight:bold;">📊 Index Stats</span>
          </div>
          <table style="width:100%;border-collapse:separate;border-spacing:0 6px;margin-top:10px;">
            <tr>
              <td style="font-weight:500;color:#333;">Pages Indexed</td>
              <td style="color:#0078d7;font-weight:bold;text-align:right;">${document.querySelectorAll('#indexed-pages-list li').length}</td>
            </tr>
            <tr>
              <td style="font-weight:500;color:#333;">Total Chunks</td>
              <td style="color:#0078d7;font-weight:bold;text-align:right;">${data.num_chunks ?? '-'}</td>
            </tr>
            <tr>
              <td style="font-weight:500;color:#333;">Vector Dimensions</td>
              <td style="color:#0078d7;font-weight:bold;text-align:right;">${data.embedding_dim ?? '-'}</td>
            </tr>
            <tr>
              <td style="font-weight:500;color:#333;">FAISS Index Type</td>
              <td style="color:#0078d7;font-weight:bold;text-align:right;">${data.faiss_index_type ?? '-'}</td>
            </tr>
          </table>
          <div style="margin-top:12px;">
            <ul style="font-size:0.97em;color:#444;line-height:1.5;padding-left:18px;margin:0;">
              <li><b>Pages Indexed</b>: Number of unique web pages stored.</li>
              <li><b>Total Chunks</b>: Number of text sections split and embedded for search.</li>
              <li><b>Vector Dimensions</b>: Size of each embedding vector (model dependent).</li>
              <li><b>FAISS Index Type</b>: Algorithm used for fast search.</li>
            </ul>
          </div>
        </div>
      `;
    });
});

// Make stats modal easier to close
statsModal.addEventListener('click', (e) => {
  if (e.target === statsModal) {
    statsModal.classList.add('hidden');
  }
});
document.addEventListener('keydown', (e) => {
  if (!statsModal.classList.contains('hidden') && e.key === 'Escape') {
    statsModal.classList.add('hidden');
  }
});

closeStats.addEventListener('click', () => {
  statsModal.classList.add('hidden');
});

// Auto-expand textarea
askInput.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = (this.scrollHeight + 2) + 'px';
});

// Enhanced main popup layout styling and markup
document.addEventListener('DOMContentLoaded', () => {
  // Enhance container
  const container = document.querySelector('body > div');
  if (container) {
    container.style.background = '#fff';
    container.style.borderRadius = '12px';
    container.style.boxShadow = '0 2px 16px rgba(0,0,0,0.13)';
    container.style.padding = '0 0 18px 0';
    container.style.maxWidth = '430px';
    container.style.margin = '0 auto';
    container.style.fontFamily = 'Segoe UI, Arial, sans-serif';
  }

  // Header with only green dot
  const header = document.querySelector('body > div > div');
  if (header) {
    header.style.background = '#2d3a4f';
    header.style.color = '#fff';
    header.style.borderRadius = '12px 12px 0 0';
    header.style.padding = '12px 18px 8px 18px';
    header.style.fontSize = '1.25em';
    header.style.fontWeight = 'bold';
    header.style.letterSpacing = '0.5px';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.justifyContent = 'flex-start';
    // Only green dot
    let dot = document.createElement('span');
    dot.style.display = 'inline-block';
    dot.style.width = '10px';
    dot.style.height = '10px';
    dot.style.background = '#36b37e';
    dot.style.borderRadius = '50%';
    dot.style.marginRight = '11px';
    header.insertBefore(dot, header.firstChild);
  }

  // Style the button row
  const btns = document.querySelectorAll('button');
  btns.forEach(btn => {
    btn.style.background = '#25314a';
    btn.style.color = '#fff';
    btn.style.border = 'none';
    btn.style.borderRadius = '7px';
    btn.style.padding = '8px 18px';
    btn.style.marginRight = '10px';
    btn.style.fontWeight = '500';
    btn.style.fontSize = '1em';
    btn.style.cursor = 'pointer';
    btn.style.boxShadow = '0 2px 6px rgba(44,62,80,0.07)';
    btn.addEventListener('mouseenter', () => btn.style.background = '#0078d7');
    btn.addEventListener('mouseleave', () => btn.style.background = '#25314a');
  });
  // Log Page button blue when active
  const logBtn = Array.from(btns).find(b => b.textContent.trim() === 'Capture My Information');
  if (logBtn) {
    logBtn.addEventListener('click', () => {
      btns.forEach(b => b.style.background = '#25314a');
      logBtn.style.background = '#0078d7';
    });
  }
  // Style ask button separately (green)
  const askBtn = Array.from(btns).find(b => b.textContent.trim() === 'Search');
  if (askBtn) {
    askBtn.style.background = '#36b37e';
    askBtn.style.color = '#fff';
    askBtn.style.fontWeight = 'bold';
    askBtn.style.fontSize = '1.09em';
    askBtn.style.boxShadow = '0 2px 6px rgba(44,62,80,0.07)';
    askBtn.style.marginLeft = '8px';
    askBtn.addEventListener('mouseenter', () => askBtn.style.background = '#22a06b');
    askBtn.addEventListener('mouseleave', () => askBtn.style.background = '#36b37e');
  }

  // Style input area
  const textarea = document.querySelector('textarea');
  if (textarea) {
    textarea.style.border = '1.5px solid #e0e7ef';
    textarea.style.borderRadius = '7px';
    textarea.style.padding = '10px 12px';
    textarea.style.fontSize = '1.08em';
    textarea.style.marginTop = '10px';
    textarea.style.marginBottom = '8px';
    textarea.style.width = 'calc(100% - 24px)';
    textarea.style.boxSizing = 'border-box';
    textarea.style.background = '#f9fbfd';
    textarea.style.resize = 'vertical';
    textarea.style.color = '#222';
  }

  // Results box
  const results = document.querySelector('#resultsDiv, #results, .results');
  if (results) {
    results.style.background = '#f4f6fa';
    results.style.borderRadius = '8px';
    results.style.minHeight = '62px';
    results.style.marginTop = '8px';
    results.style.padding = '14px 12px 14px 12px';
    results.style.fontSize = '1.07em';
    results.style.color = '#2d3a4f';
    results.style.boxShadow = '0 1px 4px rgba(44,62,80,0.07)';
  }

  // My Indexed Pages and Show Stats button
  const statsBtn = document.getElementById('show-stats-btn');
  if (statsBtn) {
    statsBtn.style.background = '#e9ecf2';
    statsBtn.style.color = '#25314a';
    statsBtn.style.border = 'none';
    statsBtn.style.borderRadius = '7px';
    statsBtn.style.fontWeight = '500';
    statsBtn.style.fontSize = '1em';
    statsBtn.style.marginTop = '8px';
    statsBtn.style.marginLeft = '2px';
    statsBtn.style.padding = '8px 18px';
    statsBtn.style.boxShadow = '0 2px 6px rgba(44,62,80,0.07)';
    statsBtn.addEventListener('mouseenter', () => statsBtn.style.background = '#d3dbe7');
    statsBtn.addEventListener('mouseleave', () => statsBtn.style.background = '#e9ecf2');
  }

  // Section headings
  const headings = document.querySelectorAll('h3, h4, .section-heading');
  headings.forEach(h => {
    h.style.marginTop = '18px';
    h.style.marginBottom = '8px';
    h.style.fontWeight = 'bold';
    h.style.color = '#2d3a4f';
    h.style.fontSize = '1.08em';
  });

  // --- Style My Indexed Pages section ---
  const indexedSection = document.querySelector('#indexed-pages-list');
  if (indexedSection) {
    indexedSection.style.listStyle = 'none';
    indexedSection.style.padding = '0';
    indexedSection.style.margin = '0';
    indexedSection.style.fontSize = '1.01em';
    indexedSection.style.maxHeight = '110px';
    indexedSection.style.overflowY = 'auto';
  }
  // Style each indexed page row
  const indexedItems = document.querySelectorAll('#indexed-pages-list li');
  indexedItems.forEach(li => {
    li.style.background = '#f9fbfd';
    li.style.borderRadius = '7px';
    li.style.padding = '6px 12px 6px 8px';
    li.style.margin = '5px 0';
    li.style.display = 'flex';
    li.style.alignItems = 'center';
    li.style.justifyContent = 'space-between';
    li.style.wordBreak = 'break-all';
    li.style.boxShadow = '0 1px 3px rgba(44,62,80,0.06)';
    // Style the delete/trash icon
    const trash = li.querySelector('svg, .delete-btn, .fa-trash, img');
    if (trash) {
      trash.style.marginLeft = '10px';
      trash.style.cursor = 'pointer';
      trash.style.opacity = '0.7';
      trash.addEventListener('mouseenter', () => trash.style.opacity = '1');
      trash.addEventListener('mouseleave', () => trash.style.opacity = '0.7');
    }
  });
});

// On popup open
checkBackendStatus();
listIndexedPages();
