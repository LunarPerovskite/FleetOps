import { useState, useEffect } from 'react';
import { tasksAPI } from '../lib/api';

export function useTaskList(filters?: { status?: string; page?: number; page_size?: number }) {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setIsLoading(true);
        const response = await tasksAPI.list(filters);
        setData(response?.tasks || []);
        setTotal(response?.total || 0);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load tasks');
        setData([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTasks();
  }, [filters?.status, filters?.page, filters?.page_size]);
  
  const refresh = async () => {
    try {
      setIsLoading(true);
      const response = await tasksAPI.list(filters);
      setData(response?.tasks || []);
      setTotal(response?.total || 0);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load tasks');
      setData([]);
    } finally {
      setIsLoading(false);
    }
  };

  return { data, isLoading, error, total, refresh };
}

export function useTaskDetail(id: string) {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!id) return;
    
    const fetchTask = async () => {
      try {
        setIsLoading(true);
        const response = await tasksAPI.get(id);
        setData(response);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load task');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTask();
  }, [id]);
  
  return { data, isLoading, error };
}

export function useCreateTask() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const create = async (data: any) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await tasksAPI.create(data);
      return response;
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { create, isLoading, error };
}

export function useApproveTask() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const approve = async (id: string, decision: string, comments?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await tasksAPI.approve(id, {
        decision,
        comments,
        human_id: 'current_user', // Will be replaced with actual user ID
      });
      return response;
    } catch (err: any) {
      setError(err.message || 'Failed to approve task');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { approve, isLoading, error };
}

export function useTaskEvents(taskId: string) {
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!taskId) return;
    
    const fetchEvents = async () => {
      try {
        setIsLoading(true);
        const response = await tasksAPI.events(taskId);
        setData(response?.events || []);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load events');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchEvents();
  }, [taskId]);
  
  return { data, isLoading, error };
}
