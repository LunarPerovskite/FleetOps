import { useState, useEffect } from 'react';
import { dashboardAPI, tasksAPI, agentsAPI, approvalsAPI } from '../lib/api';
import { useWebSocket } from '../hooks/useWebSocket';

interface DashboardStats {
  totalTasks: number;
  completedTasks: number;
  activeAgents: number;
  pendingApprovals: number;
  successRate: number;
  costSavings: number;
}

interface RecentActivity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  user?: string;
  agent?: string;
}

export function useDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // WebSocket for real-time updates
  const ws = useWebSocket();
  
  useEffect(() => {
    if (ws) {
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'dashboard_update') {
          fetchDashboardData();
        }
      };
    }
  }, [ws]);
  
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch all data in parallel
      const [statsRes, activityRes, tasksRes, agentsRes, approvalsRes] = await Promise.all([
        dashboardAPI.stats().catch(() => null),
        dashboardAPI.activity().catch(() => []),
        tasksAPI.list({ status: 'active', page_size: 5 }).catch(() => []),
        agentsAPI.list().catch(() => []),
        approvalsAPI.list({ status: 'pending' }).catch(() => []),
      ]);
      
      if (statsRes) setStats(statsRes);
      if (activityRes) setActivities(activityRes);
      if (tasksRes?.tasks) setTasks(tasksRes.tasks);
      if (agentsRes?.agents) setAgents(agentsRes.agents);
      if (approvalsRes?.approvals) setApprovals(approvalsRes.approvals);
      
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Initial load
  useEffect(() => {
    fetchDashboardData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const refresh = () => {
    fetchDashboardData();
  };
  
  return {
    stats,
    activities,
    tasks,
    agents,
    approvals,
    loading,
    error,
    refresh,
  };
}
