import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hazeon_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401 (expired / invalid token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('hazeon_token');
      localStorage.removeItem('hazeon_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ── In-memory cache for read-only page data ───────────
// Prevents re-fetching on every page switch (same session).
const _cache = new Map();   // key → { data, ts }

function cachedGet(url, params, ttl) {
  const key = url + (params ? JSON.stringify(params) : '');
  const hit = _cache.get(key);
  if (hit && Date.now() - hit.ts < ttl) return Promise.resolve(hit.data);
  return api.get(url, params ? { params } : {}).then(res => {
    _cache.set(key, { data: res, ts: Date.now() });
    return res;
  });
}

export function invalidateCache(urlPrefix) {
  for (const key of _cache.keys()) {
    if (key.startsWith(urlPrefix)) _cache.delete(key);
  }
}

// Auth
export const login = (email, password) =>
  api.post('/auth/login', { email, password });

export const register = (data) =>
  api.post('/auth/register', data);

export const getMe = () => api.get('/auth/me');

export const getInstitutes = () => api.get('/auth/institutes');

export const forgotPassword = (email) =>
  api.post('/auth/forgot-password', { email });

export const resetPassword = (email, code, new_password) =>
  api.post('/auth/reset-password', { email, code, new_password });

// Submissions
export const uploadAnswer = (formData) =>
  api.post('/submissions/upload', formData, {
    timeout: 120000,   // 2 min — Groq free tier can be slow under load
    headers: { 'Content-Type': undefined },
  }).then(res => { invalidateCache('/submissions/my-submissions'); return res; });

export const getMySubmissions = () =>
  cachedGet('/submissions/my-submissions', null, 10_000);

export const getSubmission = (id) =>
  api.get(`/submissions/${id}`);

// Dashboard
export const getBatchAnalytics = () =>
  cachedGet('/dashboard/batch-analytics', null, 30_000);

export const getStudentProgress = (studentId) =>
  cachedGet(`/dashboard/student/${studentId}/progress`, null, 30_000);

export const getStudents = () =>
  cachedGet('/dashboard/students', null, 30_000);

export const getQuestions = () =>
  cachedGet('/dashboard/questions', null, 300_000);

const _bustQuestions = () => invalidateCache('/dashboard/questions');

export const createQuestion = (data) =>
  api.post('/dashboard/questions', data).then(res => { _bustQuestions(); return res; });

export const updateQuestion = (id, data) =>
  api.put(`/dashboard/questions/${id}`, data).then(res => { _bustQuestions(); return res; });

export const deleteQuestion = (id) =>
  api.delete(`/dashboard/questions/${id}`).then(res => { _bustQuestions(); return res; });

// Topper Answers
export const getTopperAnswers = (params = {}) =>
  cachedGet('/topper-answers/', params, 60_000);

export const getTopperAnswer = (id) =>
  api.get(`/topper-answers/${id}`);

export const uploadTopperAnswer = (formData) =>
  api.post('/topper-answers/upload', formData);

// MCQ Generator
export const uploadMCQDocument = (formData) =>
  api.post('/mcq/upload', formData, {
    timeout: 120000,
    headers: { 'Content-Type': undefined },  // let browser set multipart boundary
  });

export const getMCQDocuments = () => cachedGet('/mcq/documents', null, 3_000);

export const getMCQDocument = (id) => api.get(`/mcq/documents/${id}`, { timeout: 15000 });

export const deleteMCQDocument = (id) => api.delete(`/mcq/documents/${id}`);

export const regenerateMCQs = (id, numQuestions = 10) =>
  api.post(`/mcq/regenerate/${id}?num_questions=${numQuestions}`);

export default api;
