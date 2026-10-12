import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for large indexing / Groq operations
});

/**
 * Extract user-friendly error message from Axios error
 */
export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    if (typeof error.response.data.detail === 'string') {
      return error.response.data.detail;
    }
    return JSON.stringify(error.response.data.detail);
  }
  if (error.message === 'Network Error') {
    return 'Could not connect to FastAPI backend at http://127.0.0.1:8000. Please ensure uvicorn is running.';
  }
  return error.message || 'An unexpected error occurred';
};

/**
 * Health check endpoint
 */
export const checkHealth = async () => {
  const response = await client.get('/health');
  return response.data;
};

/**
 * Index a GitHub repository
 * @param {string} repoUrl
 * @param {string|null} branch
 */
export const indexRepository = async (repoUrl, branch = null) => {
  const payload = {
    repo_url: repoUrl.trim(),
    branch: branch && branch.trim() ? branch.trim() : null,
  };
  const response = await client.post('/repo/index', payload);
  return response.data;
};

/**
 * Ask a question about an indexed repository
 * @param {string} repoUrl
 * @param {string|null} branch
 * @param {string} question
 */
export const askQuestion = async (repoUrl, branch = null, question) => {
  const payload = {
    repo_url: repoUrl.trim(),
    branch: branch && branch.trim() ? branch.trim() : null,
    question: question.trim(),
  };
  const response = await client.post('/repo/ask', payload);
  return response.data;
};
