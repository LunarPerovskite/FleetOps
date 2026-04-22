import { z } from 'zod';

// Task validation
export const taskSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title too long'),
  description: z.string().optional(),
  agent_id: z.string().min(1, 'Agent is required'),
  risk_level: z.enum(['low', 'medium', 'high', 'critical'], {
    errorMap: () => ({ message: 'Select a valid risk level' })
  }),
  priority: z.number().min(0).max(100).optional(),
  stage: z.string().optional()
});

export type TaskInput = z.infer<typeof taskSchema>;

// Agent validation
export const agentSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  provider: z.string().min(1, 'Provider is required'),
  model: z.string().optional(),
  capabilities: z.array(z.string()).optional(),
  level: z.enum(['junior', 'specialist', 'senior', 'lead'], {
    errorMap: () => ({ message: 'Select a valid level' })
  }),
  parent_id: z.string().optional()
});

export type AgentInput = z.infer<typeof agentSchema>;

// Approval validation
export const approvalSchema = z.object({
  decision: z.enum(['approve', 'reject', 'escalate'], {
    errorMap: () => ({ message: 'Select a valid decision' })
  }),
  comments: z.string().max(1000, 'Comments too long').optional()
});

export type ApprovalInput = z.infer<typeof approvalSchema>;

// User registration
export const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  name: z.string().min(1, 'Name is required'),
  org_name: z.string().min(1, 'Organization name is required')
});

export type RegisterInput = z.infer<typeof registerSchema>;

// Login
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required')
});

export type LoginInput = z.infer<typeof loginSchema>;

// Webhook
export const webhookSchema = z.object({
  url: z.string().url('Invalid URL').min(1, 'URL is required'),
  events: z.array(z.string()).min(1, 'Select at least one event'),
  secret: z.string().optional()
});

export type WebhookInput = z.infer<typeof webhookSchema>;

// Provider config
export const providerConfigSchema = z.object({
  auth_provider: z.string(),
  database: z.string(),
  hosting: z.string(),
  secrets: z.string(),
  monitoring: z.string()
});

export type ProviderConfigInput = z.infer<typeof providerConfigSchema>;
