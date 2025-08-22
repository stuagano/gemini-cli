/**
 * Real-Time Status Tests
 * Comprehensive tests for real-time status monitoring and updates
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import RealTimeStatus, { StatusUpdate, AgentStatus, SystemMetrics } from './real-time-status.js';
import { createMockConfig, MockWebSocket, mockConsole, AsyncTestUtils } from '../test-utils/test-helpers.js';
import { Config } from '@google/gemini-cli-core';

// Mock WebSocket
vi.mock('ws', () => ({
  default: vi.fn(() => new MockWebSocket('ws://localhost:8080'))
}));

describe('RealTimeStatus', () => {
  let statusMonitor: RealTimeStatus;
  let mockConfig: Config;
  let consoleMock: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfig = createMockConfig();
    consoleMock = mockConsole();
    statusMonitor = new RealTimeStatus(mockConfig);
  });

  afterEach(() => {
    consoleMock.restore();
    statusMonitor.disconnect();
    vi.restoreAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      expect(statusMonitor).toBeDefined();
      expect(statusMonitor.isConnected()).toBe(false);
      expect(statusMonitor.getUpdateInterval()).toBe(1000);
    });

    it('should set up status tracking for all agents', () => {
      const agentStatuses = statusMonitor.getAllAgentStatuses();
      expect(agentStatuses).toBeDefined();
      expect(Object.keys(agentStatuses)).toHaveLength(0); // Initially empty
    });
  });

  describe('Connection Management', () => {
    it('should connect to status server successfully', async () => {
      await statusMonitor.connect();
      
      expect(statusMonitor.isConnected()).toBe(true);
    });

    it('should handle connection failures gracefully', async () => {
      const mockError = new Error('Connection failed');
      vi.spyOn(statusMonitor, 'connect').mockRejectedValueOnce(mockError);

      await expect(statusMonitor.connect()).rejects.toThrow('Connection failed');
      expect(statusMonitor.isConnected()).toBe(false);
    });

    it('should reconnect automatically on connection loss', async () => {
      await statusMonitor.connect();
      
      const reconnectEvents: any[] = [];
      statusMonitor.on('reconnected', (data) => {
        reconnectEvents.push(data);
      });

      // Simulate connection loss
      statusMonitor.emit('connection_lost');
      
      // Wait for auto-reconnect
      await AsyncTestUtils.delay(100);
      
      expect(reconnectEvents.length).toBe(1);
    });

    it('should disconnect cleanly', async () => {
      await statusMonitor.connect();
      expect(statusMonitor.isConnected()).toBe(true);
      
      statusMonitor.disconnect();
      expect(statusMonitor.isConnected()).toBe(false);
    });
  });

  describe('Status Updates', () => {
    beforeEach(async () => {
      await statusMonitor.connect();
    });

    it('should update agent status correctly', () => {
      const statusUpdate: StatusUpdate = {
        agentId: 'scout',
        status: 'running',
        operation: 'analyzing_code',
        progress: 50,
        timestamp: new Date(),
        metadata: { filesProcessed: 25, totalFiles: 50 }
      };

      statusMonitor.updateAgentStatus(statusUpdate);

      const agentStatus = statusMonitor.getAgentStatus('scout');
      expect(agentStatus.status).toBe('running');
      expect(agentStatus.operation).toBe('analyzing_code');
      expect(agentStatus.progress).toBe(50);
      expect(agentStatus.metadata.filesProcessed).toBe(25);
    });

    it('should track status history', () => {
      const updates: StatusUpdate[] = [
        {
          agentId: 'developer',
          status: 'idle',
          timestamp: new Date()
        },
        {
          agentId: 'developer',
          status: 'running',
          operation: 'generating_code',
          timestamp: new Date()
        },
        {
          agentId: 'developer',
          status: 'completed',
          operation: 'generating_code',
          timestamp: new Date()
        }
      ];

      updates.forEach(update => statusMonitor.updateAgentStatus(update));

      const history = statusMonitor.getStatusHistory('developer');
      expect(history.length).toBe(3);
      expect(history[0].status).toBe('idle');
      expect(history[2].status).toBe('completed');
    });

    it('should emit status change events', () => {
      const statusEvents: any[] = [];
      statusMonitor.on('status_changed', (data) => {
        statusEvents.push(data);
      });

      const statusUpdate: StatusUpdate = {
        agentId: 'guardian',
        status: 'running',
        operation: 'security_scan',
        timestamp: new Date()
      };

      statusMonitor.updateAgentStatus(statusUpdate);

      expect(statusEvents.length).toBe(1);
      expect(statusEvents[0].agentId).toBe('guardian');
      expect(statusEvents[0].status).toBe('running');
    });

    it('should handle bulk status updates efficiently', () => {
      const bulkUpdates: StatusUpdate[] = Array.from({ length: 100 }, (_, i) => ({
        agentId: `agent-${i % 5}`,
        status: 'running',
        operation: `operation-${i}`,
        progress: Math.floor(Math.random() * 100),
        timestamp: new Date()
      }));

      const startTime = Date.now();
      statusMonitor.updateMultipleAgentStatuses(bulkUpdates);
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(1000); // Should process 100 updates quickly
      expect(statusMonitor.getAllAgentStatuses()).toBeDefined();
    });
  });

  describe('System Metrics', () => {
    beforeEach(async () => {
      await statusMonitor.connect();
    });

    it('should collect system performance metrics', () => {
      const metrics: SystemMetrics = {
        cpuUsage: 45.5,
        memoryUsage: 768,
        networkLatency: 50,
        activeConnections: 12,
        throughput: 250,
        timestamp: new Date()
      };

      statusMonitor.updateSystemMetrics(metrics);

      const currentMetrics = statusMonitor.getSystemMetrics();
      expect(currentMetrics.cpuUsage).toBe(45.5);
      expect(currentMetrics.memoryUsage).toBe(768);
      expect(currentMetrics.networkLatency).toBe(50);
    });

    it('should track metrics history for trend analysis', () => {
      const metricsUpdates: SystemMetrics[] = [
        { cpuUsage: 30, memoryUsage: 500, networkLatency: 45, activeConnections: 8, throughput: 200, timestamp: new Date() },
        { cpuUsage: 45, memoryUsage: 600, networkLatency: 55, activeConnections: 10, throughput: 220, timestamp: new Date() },
        { cpuUsage: 60, memoryUsage: 750, networkLatency: 70, activeConnections: 15, throughput: 180, timestamp: new Date() }
      ];

      metricsUpdates.forEach(metrics => statusMonitor.updateSystemMetrics(metrics));

      const history = statusMonitor.getMetricsHistory();
      expect(history.length).toBe(3);
      expect(history[0].cpuUsage).toBe(30);
      expect(history[2].cpuUsage).toBe(60);
    });

    it('should detect performance anomalies', () => {
      // Simulate normal metrics
      for (let i = 0; i < 10; i++) {
        statusMonitor.updateSystemMetrics({
          cpuUsage: 30 + Math.random() * 10,
          memoryUsage: 500 + Math.random() * 100,
          networkLatency: 50 + Math.random() * 10,
          activeConnections: 8,
          throughput: 200,
          timestamp: new Date()
        });
      }

      // Simulate anomaly
      statusMonitor.updateSystemMetrics({
        cpuUsage: 95, // High CPU
        memoryUsage: 1200, // High memory
        networkLatency: 500, // High latency
        activeConnections: 8,
        throughput: 50, // Low throughput
        timestamp: new Date()
      });

      const anomalies = statusMonitor.detectAnomalies();
      expect(anomalies.length).toBeGreaterThan(0);
      expect(anomalies.some(a => a.metric === 'cpuUsage')).toBe(true);
      expect(anomalies.some(a => a.metric === 'networkLatency')).toBe(true);
    });
  });

  describe('Real-Time Notifications', () => {
    beforeEach(async () => {
      await statusMonitor.connect();
    });

    it('should send notifications for critical status changes', () => {
      const notifications: any[] = [];
      statusMonitor.on('critical_notification', (data) => {
        notifications.push(data);
      });

      const criticalUpdate: StatusUpdate = {
        agentId: 'guardian',
        status: 'error',
        operation: 'security_scan',
        error: new Error('Security breach detected'),
        timestamp: new Date()
      };

      statusMonitor.updateAgentStatus(criticalUpdate);

      expect(notifications.length).toBe(1);
      expect(notifications[0].severity).toBe('critical');
      expect(notifications[0].message).toContain('security');
    });

    it('should throttle notification frequency', async () => {
      const notifications: any[] = [];
      statusMonitor.on('notification', (data) => {
        notifications.push(data);
      });

      // Send multiple notifications quickly
      for (let i = 0; i < 10; i++) {
        statusMonitor.updateAgentStatus({
          agentId: 'spam-agent',
          status: 'warning',
          operation: 'test',
          timestamp: new Date()
        });
      }

      await AsyncTestUtils.delay(100);

      // Should be throttled to prevent spam
      expect(notifications.length).toBeLessThan(10);
    });

    it('should format notifications for different channels', () => {
      const statusUpdate: StatusUpdate = {
        agentId: 'architect',
        status: 'completed',
        operation: 'design_review',
        timestamp: new Date(),
        metadata: { componentsReviewed: 15, issuesFound: 3 }
      };

      const slackNotification = statusMonitor.formatNotification(statusUpdate, 'slack');
      const emailNotification = statusMonitor.formatNotification(statusUpdate, 'email');

      expect(slackNotification).toContain('architect');
      expect(slackNotification).toContain('completed');
      expect(emailNotification).toContain('componentsReviewed');
    });
  });

  describe('Dashboard Integration', () => {
    beforeEach(async () => {
      await statusMonitor.connect();
    });

    it('should provide dashboard data in required format', () => {
      // Add some sample data
      statusMonitor.updateAgentStatus({
        agentId: 'scout',
        status: 'running',
        operation: 'code_analysis',
        progress: 75,
        timestamp: new Date()
      });

      statusMonitor.updateSystemMetrics({
        cpuUsage: 55,
        memoryUsage: 800,
        networkLatency: 65,
        activeConnections: 12,
        throughput: 300,
        timestamp: new Date()
      });

      const dashboardData = statusMonitor.getDashboardData();

      expect(dashboardData.agents).toBeDefined();
      expect(dashboardData.systemMetrics).toBeDefined();
      expect(dashboardData.alerts).toBeDefined();
      expect(dashboardData.timestamp).toBeDefined();
    });

    it('should support real-time dashboard updates via WebSocket', async () => {
      const dashboardUpdates: any[] = [];
      statusMonitor.on('dashboard_update', (data) => {
        dashboardUpdates.push(data);
      });

      // Simulate status changes that should trigger dashboard updates
      statusMonitor.updateAgentStatus({
        agentId: 'developer',
        status: 'running',
        operation: 'code_generation',
        timestamp: new Date()
      });

      expect(dashboardUpdates.length).toBe(1);
      expect(dashboardUpdates[0].type).toBe('agent_status_change');
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle high-frequency status updates efficiently', async () => {
      await statusMonitor.connect();

      const updateCount = 1000;
      const startTime = Date.now();

      // Generate high-frequency updates
      for (let i = 0; i < updateCount; i++) {
        statusMonitor.updateAgentStatus({
          agentId: `agent-${i % 10}`,
          status: 'running',
          operation: `operation-${i}`,
          progress: Math.floor(Math.random() * 100),
          timestamp: new Date()
        });
      }

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(2000); // Should handle 1000 updates in under 2 seconds
    });

    it('should cleanup old status records to prevent memory leaks', async () => {
      await statusMonitor.connect();

      // Generate many status updates
      for (let i = 0; i < 500; i++) {
        statusMonitor.updateAgentStatus({
          agentId: 'test-agent',
          status: 'running',
          operation: `operation-${i}`,
          timestamp: new Date(Date.now() - i * 1000) // Spread over time
        });
      }

      statusMonitor.cleanup();

      const history = statusMonitor.getStatusHistory('test-agent');
      expect(history.length).toBeLessThan(500); // Should have cleaned up old records
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle WebSocket connection errors gracefully', async () => {
      const errorEvents: any[] = [];
      statusMonitor.on('connection_error', (data) => {
        errorEvents.push(data);
      });

      // Simulate WebSocket error
      statusMonitor.emit('error', new Error('WebSocket connection failed'));

      expect(errorEvents.length).toBe(1);
      expect(statusMonitor.isConnected()).toBe(false);
    });

    it('should continue local operations when disconnected', () => {
      // Ensure we're disconnected
      statusMonitor.disconnect();

      const statusUpdate: StatusUpdate = {
        agentId: 'offline-agent',
        status: 'running',
        operation: 'offline_test',
        timestamp: new Date()
      };

      // Should not throw error
      expect(() => {
        statusMonitor.updateAgentStatus(statusUpdate);
      }).not.toThrow();

      const agentStatus = statusMonitor.getAgentStatus('offline-agent');
      expect(agentStatus.status).toBe('running');
    });

    it('should sync local changes when reconnected', async () => {
      // Start disconnected
      statusMonitor.disconnect();

      // Make local changes
      statusMonitor.updateAgentStatus({
        agentId: 'sync-agent',
        status: 'completed',
        operation: 'offline_work',
        timestamp: new Date()
      });

      // Reconnect
      await statusMonitor.connect();

      const syncEvents: any[] = [];
      statusMonitor.on('sync_completed', (data) => {
        syncEvents.push(data);
      });

      // Wait for sync
      await AsyncTestUtils.delay(100);

      expect(syncEvents.length).toBe(1);
      expect(syncEvents[0].changesSynced).toBeGreaterThan(0);
    });
  });

  describe('Configuration and Customization', () => {
    it('should update monitoring configuration', () => {
      const newConfig = {
        updateInterval: 500,
        maxHistorySize: 200,
        enableMetrics: false
      };

      statusMonitor.updateConfiguration(newConfig);
      const config = statusMonitor.getConfiguration();

      expect(config.updateInterval).toBe(500);
      expect(config.maxHistorySize).toBe(200);
      expect(config.enableMetrics).toBe(false);
    });

    it('should support custom status filters', () => {
      const filter = (status: AgentStatus) => status.agentId.startsWith('important-');

      statusMonitor.addStatusFilter('important_only', filter);

      // Add mixed statuses
      statusMonitor.updateAgentStatus({
        agentId: 'important-agent-1',
        status: 'running',
        timestamp: new Date()
      });

      statusMonitor.updateAgentStatus({
        agentId: 'regular-agent',
        status: 'running',
        timestamp: new Date()
      });

      const filteredStatuses = statusMonitor.getFilteredStatuses('important_only');
      expect(filteredStatuses.length).toBe(1);
      expect(filteredStatuses[0].agentId).toBe('important-agent-1');
    });
  });
});