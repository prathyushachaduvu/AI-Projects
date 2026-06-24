import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { FileText, Loader2, Search, Upload } from 'lucide-react';
import './styles.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function App() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState('What is the refund policy for cancelled orders?');
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function loadDocuments() {
    const response = await fetch(`${API_URL}/documents`);
    if (response.ok) {
      setDocuments(await response.json());
    }
  }

  useEffect(() => {
    loadDocuments().catch(() => setMessage('Backend is not running yet.'));
  }, []);

  async function uploadDocument(event) {
    event.preventDefault();
    if (!file) {
      setMessage('Choose a .txt, .md, or .pdf file first.');
      return;
    }

    setBusy(true);
    setMessage('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/documents`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed.');
      }
      setFile(null);
      setMessage(`Uploaded ${data.document.filename}.`);
      await loadDocuments();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function askQuestion(event) {
    event.preventDefault();
    if (!question.trim()) {
      setMessage('Enter a question first.');
      return;
    }

    setBusy(true);
    setMessage('');
    setAnswer(null);
    setSources([]);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 4 }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Question failed.');
      }
      setAnswer(data.answer);
      setSources(data.sources);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="sidebar">
          <div>
            <h1>Local RAG</h1>
            <p className="muted">Upload documents, ask questions, and verify the source text.</p>
          </div>

          <form className="panel" onSubmit={uploadDocument}>
            <label className="file-picker">
              <Upload size={18} />
              <span>{file ? file.name : 'Choose document'}</span>
              <input
                type="file"
                accept=".txt,.md,.pdf"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </label>
            <button type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" size={18} /> : <Upload size={18} />}
              Upload
            </button>
          </form>

          <div className="document-list">
            <h2>Documents</h2>
            {documents.length === 0 ? (
              <p className="muted">No documents uploaded yet.</p>
            ) : (
              documents.map((document) => (
                <div className="document-item" key={document.id}>
                  <FileText size={17} />
                  <div>
                    <strong>{document.filename}</strong>
                    <span>{document.chunks} chunks</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        <section className="main-panel">
          <form className="ask-box" onSubmit={askQuestion}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your uploaded documents"
            />
            <button type="submit" disabled={busy}>
              {busy ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
              Ask
            </button>
          </form>

          {message && <div className="notice">{message}</div>}

          <section className="answer-area">
            <h2>Answer</h2>
            <div className="answer-card">
              {answer ? <p>{answer}</p> : <p className="muted">Ask a question after uploading a document.</p>}
            </div>
          </section>

          <section className="sources-area">
            <h2>Sources</h2>
            {sources.length === 0 ? (
              <p className="muted">Relevant chunks will appear here.</p>
            ) : (
              sources.map((source) => (
                <article className="source-card" key={source.chunk_id}>
                  <strong>{source.filename}</strong>
                  <p>{source.text}</p>
                </article>
              ))
            )}
          </section>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
