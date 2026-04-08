// API configuration and client functions
const API_BASE = '/api';

export const api = {
  // Auth endpoints
  register: async (email, password) => {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  login: async (email, password) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  // Analysis endpoints
  analyzeRepo: async (repoUrl, githubToken = null) => {
    const response = await fetch(`${API_BASE}/analysis/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        repo_url: repoUrl,
        github_token: githubToken 
      }),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  checkAiHealth: async () => {
    const response = await fetch(`${API_BASE}/analysis/ai-health`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  // Health check
  healthCheck: async () => {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },
};

