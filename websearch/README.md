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

## Backend API Endpoints

- `POST /log_page`: Index a web page
- `POST /summary`: Generate a summary of a page
- `POST /user_query`: Search through indexed content
- `GET /list_pages`: List all indexed pages
- `POST /delete_page`: Remove a page from the index
- `GET /faiss_stats`: Get statistics about the index

## Technologies Used

- **Backend**:
  - Flask: Web framework
  - FAISS: Vector similarity search
  - Sentence Transformers: Text embeddings
  - FastMCP: Tool selection and processing

- **Frontend**:
  - Chrome Extension API
  - HTML/CSS/JavaScript
  - Modern UI with responsive design

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FAISS for efficient similarity search
- Sentence Transformers for text embeddings
- Flask for the web framework
- Chrome Extension API for browser integration 