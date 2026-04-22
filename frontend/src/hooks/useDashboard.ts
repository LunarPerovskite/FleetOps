import { useState, useEffect } from 'react';
import { dashboardAPI } from '../lib/api';

export interface DashboardStats {
  active_agents: number;
  tasks_in_progress: number;
  pending_approvals: number;
  cost_today: number;
  tasks_completed_today: number;
  success_rate: number;
  total_tasks: number;
  total_agents: number;
}

export interface RecentActivity {
  id: string;
  type: 'task_created' | 'task_completed' | 'approval_required' | 
         'agent_created' | 'event_occurred' | 'error';
  description: string;
  timestamp: string;
  user?: string;
  agent?: string;
  metadata?: Record<string, any>;
}

// Hook: Dashboard Stats
export function useDashboardStats() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        const response = await dashboardAPI.stats();
        setData(response);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load stats');
        console.error('Stats error:', err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchStats();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);
  
  return { data, isLoading, error, refresh: () => {} };
}

// Hook: Recent Tasks
export function useTasks(limit: number = 5) {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setIsLoading(true);
        // Use search API to get recent tasks
        const response = await dashboardAPI.activity();
        // Filter for task-related activities
        const tasks = response
          ?.filter((a: any) => ['task_created', 'task_completed'].includes(a.type))
          ?.slice(0, limit) || [];
        setData(tasks);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load tasks');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTasks();
  }, [limit]);
  
  return { data, isLoading, error };
}

// Hook: Agents
export function useAgents() {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setIsLoading(true);
        const response = await dashboardAPI.activity();
        // Filter for agent-related activities
        const agents = response
          ?.filter((a: any) => ['agent_created'].includes(a.type))
          ?.slice(0, 5) || [];
        setData(agents);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load agents');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchAgents();
  }, []);
  
  return { data, isLoading, error };
}

// Hook: Pending Approvals
export function usePendingApprovals() {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        setIsLoading(true);
        const response = await dashboardAPI.activity();
        // Filter for approval-related activities
        const approvals = response
          ?.filter((a: any) => ['approval_required'].includes(a.type))
          ?.slice(0, 5) || [];
        setData(approvals);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load approvals');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchApprovals();
  }, []);
  
  return { data, isLoading, error };
}

// Hook: Recent Activity
export function useActivity(limit: number = 10) {
  const [data, setData] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchActivity = async () => {
      try {
        setIsLoading(true);
        const response = await dashboardAPI.activity();
        setData(response?.slice(0, limit) || []);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load activity');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchActivity();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchActivity, 30000);
    return () => clearInterval(interval);
  }, [limit]);
  
  return { data, isLoading, error };
}
