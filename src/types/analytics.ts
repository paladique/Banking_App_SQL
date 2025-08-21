export interface ChatSession {
  session_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatHistory {
  id: string;
  session_id: string;
  user_id: string;
  message_type: 'human' | 'ai' | 'system' | 'tool_call' | 'tool_result';
  content: string;
  timestamp: string;
  created_at: string;
  updated_at: string;
  additional_kwargs?: Record<string, any>;
  response_md?: Record<string, any>;
  tool_call_id?: string;
  tool_name?: string;
  tool_input?: Record<string, any>;
  tool_output?: Record<string, any>;
  tool_error?: string;
  tool_execution_time_ms?: number;
}

export interface ToolUsage {
  id: string;
  session_id: string;
  user_id: string;
  message_id: string;
  tool_call_id: string;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output?: Record<string, any>;
  tool_error?: string;
  execution_time_ms: number;
  status: 'pending' | 'success' | 'error' | 'timeout';
  started_at: string;
  completed_at?: string;
  cost_cents?: number;
  tokens_used?: number;
  rate_limit_hit: boolean;
  retry_count: number;
}

export interface ToolDefinition {
  id: string;
  name: string;
  description?: string;
  input_schema: Record<string, any>;
  version: string;
  cost_per_call_cents: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsData {
  totalSessions: number;
  totalMessages: number;
  totalToolCalls: number;
  averageSessionLength: number;
  mostUsedTools: Array<{
    tool_name: string;
    usage_count: number;
    avg_execution_time: number;
  }>;
  errorRate: number;
  totalCost: number;
}