// content.js - injected into every page

let highlightClass = 'vsa-highlight-chunk';
let lastHighlights = [];

function removeHighlights() {
  lastHighlights.forEach(el => {
    el.classList.remove(highlightClass);
  });
  lastHighlights = [];
}

function highlightChunkByPosition(position, chunkSize = 1000) {
  // Find all text nodes in the body
  let walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
  let textNodes = [];
  let charCount = 0;
  while (walker.nextNode()) {
    let node = walker.currentNode;
    if (node.nodeValue.trim()) {
      textNodes.push({node, start: charCount, end: charCount + node.nodeValue.length});
      charCount += node.nodeValue.length;
    }
  }
  let start = position * chunkSize;
  let end = start + chunkSize;
  // Highlight text nodes that overlap with the chunk
  textNodes.forEach(({node, start: s, end: e}) => {
    if (e > start && s < end) {
      let span = document.createElement('span');
      span.className = highlightClass;
      span.style.background = 'yellow';
      span.style.borderRadius = '3px';
      span.style.padding = '0 2px';
      let relStart = Math.max(start - s, 0);
      let relEnd = Math.min(e, end) - s;
      let before = node.nodeValue.slice(0, relStart);
      let highlight = node.nodeValue.slice(relStart, relEnd);
      let after = node.nodeValue.slice(relEnd);
      let parent = node.parentNode;
      if (!highlight) return;
      let frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      span.textContent = highlight;
      frag.appendChild(span);
      if (after) frag.appendChild(document.createTextNode(after));
      parent.replaceChild(frag, node);
      lastHighlights.push(span);
    }
  });
  // Scroll to first highlight
  if (lastHighlights.length > 0) {
    lastHighlights[0].scrollIntoView({behavior: 'smooth', block: 'center'});
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'highlightChunks') {
    removeHighlights();
    (msg.positions || []).forEach(pos => highlightChunkByPosition(pos));
  }
});

// Clean up highlights when navigating away
window.addEventListener('beforeunload', removeHighlights);
