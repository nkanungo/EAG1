# My Browsing History

A powerful browser extension that helps you index, search, and manage your web browsing history using AI-powered semantic search capabilities.

## Features

- **Smart Indexing**: Automatically index and store web page content for future reference
- **Semantic Search**: Search through your indexed pages using natural language queries
- **Quick Snapshots**: Get instant summaries of web pages
- **History Management**: View and manage your indexed pages with easy deletion options
- **Real-time Stats**: Monitor your indexed content with detailed statistics

## Project Structure

```
websearch/
├── backend/           # Flask backend server
├── frontend/          # Chrome extension frontend
├── requirements.txt   # Python dependencies
└── setup.py          # Project setup configuration
```

## Prerequisites

- Python 3.8 or higher
- Chrome browser
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd websearch
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows
.\.venv\Scripts\activate
# On Unix/MacOS
source .venv/bin/activate
```

3. Install backend dependencies:
```bash
pip install -r requirements.txt
```

4. Load the Chrome extension:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `frontend` directory

## Usage

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Use the extension:
   - Click the extension icon in your Chrome toolbar
   - Use "Index My Information" to store a page
   - Use the search box to query your indexed content
   - View your indexed pages and manage them through the interface



## Technologies Used

- **Backend**:
  - Flask: Web framework
  - FAISS: Vector similarity search
  - Sentence Transformers: Text embeddings
  - Flask: Tool selection and processing

- **Frontend**:
  - Chrome Extension API
  - HTML/CSS/JavaScript
  - Modern UI with responsive design



