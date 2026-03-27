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
  analyzeRepo: async (repoUrl, options = {}) => {
    const response = await fetch(`${API_BASE}/analysis/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repo_url: repoUrl,
        vulnerability_type: options.vulnerability_type || 'SQL_INJECTION',
        affected_file: options.affected_file || 'main.py',
        affected_line: options.affected_line || null,
        github_token: options.github_token || null,
        bug_description: options.bug_description || '',
      }),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  getResults: async (limit = 50, offset = 0) => {
    const response = await fetch(`${API_BASE}/analysis/results?limit=${limit}&offset=${offset}`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  getStatus: async (analysisId) => {
    const response = await fetch(`${API_BASE}/analysis/status/${analysisId}`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  deleteAnalysis: async (analysisId) => {
    const response = await fetch(`${API_BASE}/analysis/analyses/${analysisId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  downloadReport: async (analysisId, format = 'html') => {
    const response = await fetch(`${API_BASE}/analysis/reports/${analysisId}/${format}`);
    if (!response.ok) throw new Error(await response.text());
    return response.blob();
  },

  checkAiHealth: async () => {
    const response = await fetch(`${API_BASE}/analysis/ai-health`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  // Stats
  getStats: async () => {
    const response = await fetch(`${API_BASE}/stats`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  // Logs
  getLogs: async (params = {}) => {
    const query = new URLSearchParams();
    if (params.analysis_id) query.set('analysis_id', params.analysis_id);
    if (params.level) query.set('level', params.level);
    if (params.limit) query.set('limit', params.limit.toString());
    const response = await fetch(`${API_BASE}/logs?${query.toString()}`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  // Settings
  getSettings: async () => {
    const response = await fetch(`${API_BASE}/settings`);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  updateSettings: async (updates) => {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
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
