import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data || error);
  }
);

// Auth
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

// Tasks
export const tasksAPI = {
  list: (params?: any) => api.get('/tasks', { params }),
  get: (id: string) => api.get(`/tasks/${id}`),
  create: (data: any) => api.post('/tasks', data),
  update: (id: string, data: any) => api.put(`/tasks/${id}`, data),
  delete: (id: string) => api.delete(`/tasks/${id}`),
  approve: (id: string, data: any) => api.post(`/tasks/${id}/approve`, data),
  events: (id: string) => api.get(`/tasks/${id}/events`),
};

// Agents
export const agentsAPI = {
  list: (params?: any) => api.get('/agents', { params }),
  get: (id: string) => api.get(`/agents/${id}`),
  create: (data: any) => api.post('/agents', data),
  update: (id: string, data: any) => api.put(`/agents/${id}`, data),
  delete: (id: string) => api.delete(`/agents/${id}`),
  subAgents: (id: string) => api.get(`/agents/${id}/sub-agents`),
};

// Approvals
export const approvalsAPI = {
  list: (params?: any) => api.get('/approvals', { params }),
  get: (id: string) => api.get(`/approvals/${id}`),
  decide: (id: string, data: any) => api.post(`/approvals/${id}/decide`, data),
};

// Events
export const eventsAPI = {
  list: (params?: any) => api.get('/events', { params }),
  get: (id: string) => api.get(`/events/${id}`),
};

// Dashboard
export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats'),
  activity: () => api.get('/dashboard/activity'),
};

// Customer Service
export const customerServiceAPI = {
  sessions: () => api.get('/customer-service/sessions'),
  getSession: (id: string) => api.get(`/customer-service/sessions/${id}`),
  sendMessage: (id: string, data: any) => api.post(`/customer-service/sessions/${id}/messages`, data),
  handoff: (id: string, data: any) => api.post(`/customer-service/sessions/${id}/handoff`, data),
};

// Hierarchy
export const hierarchyAPI = {
  get: () => api.get('/hierarchy'),
  update: (data: any) => api.put('/hierarchy', data),
  validate: (data: any) => api.post('/hierarchy/validate', data),
};

// Analytics
export const analyticsAPI = {
  overview: () => api.get('/analytics'),
  agents: () => api.get('/analytics/agents'),
  costs: () => api.get('/analytics/costs'),
};

// Search
export const searchAPI = {
  search: (data: any) => api.post('/search', data),
};

// Organizations
export const orgsAPI = {
  list: () => api.get('/orgs'),
  get: (id: string) => api.get(`/orgs/${id}`),
  create: (data: any) => api.post('/orgs', data),
};

// Teams
export const teamsAPI = {
  list: () => api.get('/teams'),
  get: (id: string) => api.get(`/teams/${id}`),
  create: (data: any) => api.post('/teams', data),
};

// Users
export const usersAPI = {
  list: () => api.get('/users'),
  get: (id: string) => api.get(`/users/${id}`),
  update: (id: string, data: any) => api.put(`/users/${id}`, data),
};

// Provider Config
export const providerConfigAPI = {
  get: () => api.get('/providers/config'),
  update: (data: any) => api.put('/providers/config', data),
  health: () => api.get('/providers/health'),
  presets: () => api.get('/providers/presets'),
};

// Audit Log
export const auditAPI = {
  events: (params?: any) => api.get('/audit/events', { params }),
  getEvent: (id: string) => api.get(`/audit/events/${id}`),
  stats: () => api.get('/audit/stats'),
};

// Dashboard Builder
export const dashboardBuilderAPI = {
  widgets: () => api.get('/dashboard-builder/widgets'),
  list: () => api.get('/dashboard-builder/dashboards'),
  create: (data: any) => api.post('/dashboard-builder/dashboards', data),
  get: (id: string) => api.get(`/dashboard-builder/dashboards/${id}`),
  update: (id: string, data: any) => api.put(`/dashboard-builder/dashboards/${id}`, data),
  delete: (id: string) => api.delete(`/dashboard-builder/dashboards/${id}`),
};

// Onboarding
export const onboardingAPI = {
  progress: () => api.get('/onboarding/progress'),
  completeStep: (stepId: string) => api.post(`/onboarding/steps/${stepId}/complete`),
  status: () => api.get('/onboarding/status'),
};

// Health
export const healthAPI = {
  check: () => api.get('/health'),
  ready: () => api.get('/ready'),
  live: () => api.get('/live'),
  detailed: () => api.get('/health/detailed'),
};

// Webhooks
export const webhooksAPI = {
  list: () => api.get('/webhooks'),
  create: (data: any) => api.post('/webhooks', data),
  delete: (id: string) => api.delete(`/webhooks/${id}`),
  test: (id: string) => api.post(`/webhooks/${id}/test`),
};

// Billing
export const billingAPI = {
  usage: () => api.get('/billing/usage'),
  history: () => api.get('/billing/history'),
  tiers: () => api.get('/billing/tiers'),
};

export default api;
