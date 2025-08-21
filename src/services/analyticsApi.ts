import type { 
  ChatSession, 
  ChatHistory, 
  ToolUsage, 
  ToolDefinition, 
  AnalyticsData 
} from '../types/analytics';

// Analytics API runs on port 5002
const ANALYTICS_API_URL = 'http://127.0.0.1:5002/api';

export class AnalyticsAPI {
  // Chat Sessions
  static async getChatSessions(): Promise<ChatSession[]> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/chat/sessions`);
      if (!response.ok) {
        throw new Error(`Failed to fetch chat sessions: ${response.status} ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
      throw error;
    }
  }

  static async createChatSession(sessionData: Partial<ChatSession>): Promise<ChatSession> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sessionData),
      });
      if (!response.ok) {
        throw new Error(`Failed to create chat session: ${response.status} ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error creating chat session:', error);
      throw error;
    }
  }

  // Tool Usage Analytics
  static async getToolUsage(sessionId: string): Promise<ToolUsage[]> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/tools/usage/${sessionId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch tool usage: ${response.status} ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching tool usage:', error);
      throw error;
    }
  }

  // Chat Export
  static async exportChatSession(sessionId: string): Promise<Blob> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/chat/export/${sessionId}`);
      if (!response.ok) {
        throw new Error(`Failed to export chat session: ${response.status} ${response.statusText}`);
      }
      return response.blob();
    } catch (error) {
      console.error('Error exporting chat session:', error);
      throw error;
    }
  }

  // Tool Definitions
  static async getToolDefinitions(): Promise<ToolDefinition[]> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/tools/definitions`);
      if (!response.ok) {
        throw new Error(`Failed to fetch tool definitions: ${response.status} ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching tool definitions:', error);
      throw error;
    }
  }

  static async createToolDefinition(toolData: Omit<ToolDefinition, 'id' | 'created_at' | 'updated_at'>): Promise<ToolDefinition> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/tools/definitions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(toolData),
      });
      if (!response.ok) {
        throw new Error(`Failed to create tool definition: ${response.status} ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error('Error creating tool definition:', error);
      throw error;
    }
  }

  // Admin Functions
  static async clearChatHistory(): Promise<void> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/admin/clear-chat-history`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`Failed to clear chat history: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error clearing chat history:', error);
      throw error;
    }
  }

  static async clearSession(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${ANALYTICS_API_URL}/admin/clear-session/${sessionId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`Failed to clear session: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error clearing session:', error);
      throw error;
    }
  }

  // Get all chat sessions with analytics data
  static async getSessionsWithAnalytics(): Promise<ChatSession[]> {
    try {
      const sessions = await this.getChatSessions();
      // You could enhance this to get additional analytics per session
      return sessions;
    } catch (error) {
      console.error('Error fetching sessions with analytics:', error);
      throw error;
    }
  }
}