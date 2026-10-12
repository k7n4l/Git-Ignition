import React, { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { indexRepository, askQuestion, getErrorMessage } from './services/api';
import './App.css';

export default function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexMessage, setIndexMessage] = useState(null);
  const [indexError, setIndexError] = useState(null);
  const [isIndexed, setIsIndexed] = useState(false);

  const [question, setQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [askError, setAskError] = useState(null);
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);

  // 1. Index Repository handler
  const handleIndex = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim() || isIndexing) return;

    setIsIndexing(true);
    setIndexError(null);
    setIndexMessage(null);
    setAnswer(null);
    setSources([]);
    setAskError(null);

    try {
      const data = await indexRepository(repoUrl);
      setIndexMessage(
        `Successfully indexed ${data.owner}/${data.repo} (Branch: ${data.branch}, Files: ${data.files_processed}, Chunks: ${data.chunks_stored})`
      );
      setIsIndexed(true);
    } catch (err) {
      setIndexError(getErrorMessage(err));
      setIsIndexed(false);
    } finally {
      setIsIndexing(false);
    }
  };

  // 2. Ask Question handler
  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim() || isAsking || !isIndexed) return;

    setIsAsking(true);
    setAskError(null);

    try {
      const data = await askQuestion(repoUrl, null, question);
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (err) {
      setAskError(getErrorMessage(err));
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Git-Ignition</h1>
        <p className="subtitle">Minimal Retrieval-Augmented Generation (RAG) for GitHub codebases</p>
      </header>

      {/* 1 & 2: GitHub Repository URL & Index Button */}
      <section className="card">
        <form onSubmit={handleIndex} className="form-group">
          <label htmlFor="repo-url" className="label">
            GitHub Repository URL
          </label>
          <div className="row">
            <input
              id="repo-url"
              type="url"
              className="input flex-input"
              placeholder="https://github.com/owner/repository"
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value);
                setIsIndexed(false);
                setIndexMessage(null);
                setIndexError(null);
              }}
              disabled={isIndexing}
              required
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isIndexing || !repoUrl.trim()}
            >
              {isIndexing ? 'Indexing...' : 'Index Repository'}
            </button>
          </div>
        </form>

        {indexMessage && <div className="alert alert-success">{indexMessage}</div>}
        {indexError && <div className="alert alert-error">{indexError}</div>}
      </section>

      {/* 3: Ask a Question & Send Button */}
      <section className="card">
        <form onSubmit={handleAsk} className="form-group">
          <label htmlFor="question-input" className="label">
            Ask a Question
          </label>
          <div className="row">
            <input
              id="question-input"
              type="text"
              className="input flex-input"
              placeholder={
                isIndexed
                  ? 'Ask a question about the indexed code (e.g., How does authentication work?)'
                  : 'Please index a repository first...'
              }
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={!isIndexed || isAsking}
              required
            />
            <button
              type="submit"
              className="btn btn-secondary"
              disabled={!isIndexed || isAsking || !question.trim()}
            >
              {isAsking ? 'Thinking...' : 'Send'}
            </button>
          </div>
          {!isIndexed && (
            <small className="hint-text">
              * Enter a repository URL and click <strong>Index Repository</strong> to enable questions.
            </small>
          )}
        </form>

        {askError && <div className="alert alert-error">{askError}</div>}
      </section>

      {/* 4 & 5: Answer & Sources */}
      {answer && (
        <section className="card answer-card">
          <h2>Answer</h2>
          <div className="markdown-content">
            <Markdown remarkPlugins={[remarkGfm]}>{answer}</Markdown>
          </div>

          {sources && sources.length > 0 && (
            <div className="sources-section">
              <h3>Sources:</h3>
              <ul className="sources-list">
                {sources.map((src, idx) => (
                  <li key={idx} className="source-item">
                    <code>{src}</code>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
