// API Client for FleetOps Frontend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth token
function getToken(): string | null {
  return localStorage.getItem('fleetops_token');
}

// Generic fetch wrapper
async function apiClient(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }
  
  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }
  
  return response.json();
}

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    apiClient('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  
  register: (data: { email: string; password: string; name?: string; org_name?: string }) =>
    apiClient('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  me: () => apiClient('/auth/me'),
};

// Tasks API
export const tasksAPI = {
  list: (params?: { status?: string; page?: number; page_size?: number }) => {
    const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return apiClient(`/tasks${query}`);
  },
  
  get: (id: string) => apiClient(`/tasks/${id}`),
  
  create: (data: any) =>
    apiClient('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: any) =>
    apiClient(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    apiClient(`/tasks/${id}`, {
      method: 'DELETE',
    }),
  
  approve: (id: string, data: { decision: string; comments?: string }) =>
    apiClient(`/tasks/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// Agents API
export const agentsAPI = {
  list: () => apiClient('/agents'),
  
  get: (id: string) => apiClient(`/agents/${id}`),
  
  create: (data: any) =>
    apiClient('/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: any) =>
    apiClient(`/agents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    apiClient(`/agents/${id}`, {
      method: 'DELETE',
    }),
  
  subAgents: (id: string) => apiClient(`/agents/${id}/sub-agents`),
};

// Approvals API
export const approvalsAPI = {
  list: (params?: { status?: string }) => {
    const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return apiClient(`/approvals${query}`);
  },
  
  get: (id: string) => apiClient(`/approvals/${id}`),
  
  decide: (id: string, data: { decision: string; comments?: string }) =>
    apiClient(`/approvals/${id}/decide`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// Dashboard API
export const dashboardAPI = {
  stats: () => apiClient('/dashboard/stats'),
  activity: () => apiClient('/dashboard/activity'),
};

// Analytics API
export const analyticsAPI = {
  overview: () => apiClient('/analytics'),
  agents: () => apiClient('/analytics/agents'),
  costs: () => apiClient('/analytics/costs'),
};

// Search API
export const searchAPI = {
  search: (query: string, filters?: any) =>
    apiClient('/search', {
      method: 'POST',
      body: JSON.stringify({ search_text: query, ...filters }),
    }),
};

// Customer Service API
export const customerServiceAPI = {
  sessions: () => apiClient('/customer-service/sessions'),
  
  getSession: (id: string) => apiClient(`/customer-service/sessions/${id}`),
  
  sendMessage: (sessionId: string, data: { content: string; agent_id?: string }) =>
    apiClient(`/customer-service/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  handoff: (sessionId: string, data: { reason: string; notes?: string }) =>
    apiClient(`/customer-service/sessions/${sessionId}/handoff`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// Hierarchy API
export const hierarchyAPI = {
  get: () => apiClient('/hierarchy'),
  
  update: (data: any) =>
    apiClient('/hierarchy', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  validate: (data: any) =>
    apiClient('/hierarchy/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// Provider Config API
export const providerConfigAPI = {
  get: () => apiClient('/providers/config'),
  
  update: (data: any) =>
    apiClient('/providers/config', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  health: () => apiClient('/providers/health'),
};

// Events API
export const eventsAPI = {
  list: (params?: { task_id?: string; limit?: number }) => {
    const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return apiClient(`/events${query}`);
  },
  
  get: (id: string) => apiClient(`/events/${id}`),
};

// WebSocket connection
export function createWebSocketConnection(): WebSocket | null {
  const token = getToken();
  if (!token) return null;
  
  const wsUrl = API_BASE_URL.replace('http', 'ws');
  const ws = new WebSocket(`${wsUrl}/ws?token=${token}`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };
  
  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return ws;
}

export default apiClient;
