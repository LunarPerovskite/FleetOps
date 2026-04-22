import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fleetops_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/overview')
      return data
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  })
}

export function useTasks(status?: string) {
  return useQuery({
    queryKey: ['tasks', status],
    queryFn: async () => {
      const params = status ? { status } : {}
      const { data } = await api.get('/tasks/', { params })
      return data
    },
    refetchInterval: 10000
  })
}

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await api.get('/agents/')
      return data
    },
    refetchInterval: 30000
  })
}

export function usePendingApprovals() {
  return useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: async () => {
      const { data } = await api.get('/approvals/pending')
      return data
    },
    refetchInterval: 5000 // Check every 5 seconds
  })
}

export function useEvents(taskId?: string) {
  return useQuery({
    queryKey: ['events', taskId],
    queryFn: async () => {
      const params = taskId ? { task_id: taskId } : {}
      const { data } = await api.get('/events/', { params })
      return data
    },
    refetchInterval: 10000
  })
}

export function useQueueStats() {
  return useQuery({
    queryKey: ['customer-service', 'queue-stats'],
    queryFn: async () => {
      const { data } = await api.get('/customer-service/queue/stats')
      return data
    },
    refetchInterval: 10000
  })
}
