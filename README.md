# AI PDF Chatbot 🤖📄

An AI-powered PDF chatbot built using Streamlit, Google Gemini API, FAISS, and Python.  
Users can upload PDFs and ask questions based on the document content.

## Features 🚀

- Upload multiple PDFs
- AI-based question answering
- Chat history support
- Fast document search using FAISS
- User login system
- Clean Streamlit UI
- Secure environment variable support

## Tech Stack 🛠️

- Python
- Streamlit
- Google Gemini API
- FAISS
- PyPDF2
- SQLite
- dotenv

## Installation ⚙️

Clone the repository:

```bash
git clone https://github.com/yourusername/AI_PDF_Chatbot.git
cd AI_PDF_Chatbot
```

Create virtual environment:

```bash
python -m venv ai_pdf
```

Activate virtual environment:

### Windows

```bash
ai_pdf\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables 🔑

Create a `.env` file and add:

```env
GOOGLE_API_KEY=your_api_key_here
```

## Run the App ▶️

```bash
streamlit run app.py
```

## Project Structure 📂

```bash
AI_PDF_Chatbot/
│── app.py
│── requirements.txt
│── .gitignore
│── users.db
│── README.md
```

## Future Improvements 🌟

- Admin dashboard
- Cloud database
- PDF summarization
- Voice assistant support
- Dark mode UI

## Author 👨‍💻

Sudeepthi Barla
