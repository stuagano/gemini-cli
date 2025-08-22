/**
 * DORA Metrics Tests
 * Comprehensive test suite for DORA metrics implementation
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DORAMetricsCollector, DeploymentEvent, IncidentEvent, DORAMetrics } from './dora-metrics.js';
import { DORADashboard } from './dora-dashboard.js';
import fs from 'fs/promises';
import path from 'path';
import { execSync } from 'child_process';

// Mock file system operations
vi.mock('fs/promises');
vi.mock('child_process');

describe('DORA Metrics System', () => {
  let collector: DORAMetricsCollector;
  let dashboard: DORADashboard;
  let tempDir: string;

  beforeEach(async () => {
    tempDir = '/tmp/dora-test';
    
    // Mock fs operations
    (fs.mkdir as any).mockResolvedValue(undefined);
    (fs.readFile as any).mockResolvedValue('[]');
    (fs.writeFile as any).mockResolvedValue(undefined);
    
    // Mock execSync for Git operations
    (execSync as any).mockImplementation((cmd: string) => {
      if (cmd.includes('git rev-parse --git-dir')) {
        return '.git';
      }
      if (cmd.includes('git log')) {
        return 'abc123|1640995200|John Doe|feat: add user authentication\ndef456|1640995300|Jane Smith|fix: resolve login bug';
      }
      if (cmd.includes('git rev-parse HEAD')) {
        return 'abc123def456';
      }
      return '';
    });

    collector = new DORAMetricsCollector({
      dataPath: tempDir,
      gitRepository: '/test/repo',
      environments: ['development', 'staging', 'production']
    });

    dashboard = new DORADashboard(collector);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('DORAMetricsCollector', () => {
    describe('Initialization', () => {
      it('should initialize successfully', async () => {
        await collector.initialize();
        expect(fs.mkdir).toHaveBeenCalledWith(tempDir, { recursive: true });
      });

      it('should load existing data on initialization', async () => {
        const mockDeployments = [
          {
            id: 'deploy_1',
            timestamp: '2023-01-01T00:00:00.000Z',
            environment: 'production',
            version: 'v1.0.0',
            commit: 'abc123',
            success: true
          }
        ];

        (fs.readFile as any).mockResolvedValueOnce(JSON.stringify(mockDeployments));

        await collector.initialize();
        const deployments = collector.getDeployments();
        expect(deployments).toHaveLength(1);
        expect(deployments[0].version).toBe('v1.0.0');
      });

      it('should handle missing data files gracefully', async () => {
        (fs.readFile as any).mockRejectedValue(new Error('File not found'));
        
        await expect(collector.initialize()).resolves.not.toThrow();
        expect(collector.getDeployments()).toHaveLength(0);
      });

      it('should load Git commits if repository exists', async () => {
        await collector.initialize();
        
        expect(execSync).toHaveBeenCalledWith(
          expect.stringContaining('git log'),
          expect.any(Object)
        );
      });
    });

    describe('Deployment Tracking', () => {
      beforeEach(async () => {
        await collector.initialize();
      });

      it('should record deployment events', async () => {
        const deployment = {
          environment: 'production' as const,
          version: 'v1.2.3',
          commit: 'abc123',
          success: true
        };

        await collector.recordDeployment(deployment);
        
        const deployments = collector.getDeployments();
        expect(deployments).toHaveLength(1);
        expect(deployments[0].version).toBe('v1.2.3');
        expect(deployments[0].environment).toBe('production');
        expect(deployments[0].success).toBe(true);
      });

      it('should generate unique deployment IDs', async () => {
        const deployment = {
          environment: 'production' as const,
          version: 'v1.0.0',
          commit: 'abc123',
          success: true
        };

        await collector.recordDeployment(deployment);
        await collector.recordDeployment(deployment);
        
        const deployments = collector.getDeployments();
        expect(deployments).toHaveLength(2);
        expect(deployments[0].id).not.toBe(deployments[1].id);
      });

      it('should save data after recording deployment', async () => {
        const deployment = {
          environment: 'production' as const,
          version: 'v1.0.0',
          commit: 'abc123',
          success: true
        };

        await collector.recordDeployment(deployment);
        
        expect(fs.writeFile).toHaveBeenCalledWith(
          expect.stringContaining('deployments.json'),
          expect.stringContaining('"version":"v1.0.0"')
        );
      });
    });

    describe('Incident Tracking', () => {
      beforeEach(async () => {
        await collector.initialize();
      });

      it('should record incident events', async () => {
        const incident = {
          environment: 'production' as const,
          severity: 'high' as const,
          description: 'API gateway timeout'
        };

        await collector.recordIncident(incident);
        
        const incidents = collector.getIncidents();
        expect(incidents).toHaveLength(1);
        expect(incidents[0].severity).toBe('high');
        expect(incidents[0].description).toBe('API gateway timeout');
        expect(incidents[0].resolved).toBe(undefined);
      });

      it('should resolve incidents and calculate MTTR', async () => {
        const incident = {
          environment: 'production' as const,
          severity: 'high' as const,
          description: 'API gateway timeout'
        };

        await collector.recordIncident(incident);
        const incidents = collector.getIncidents();
        const incidentId = incidents[0].id;

        // Wait a bit to simulate resolution time
        await new Promise(resolve => setTimeout(resolve, 10));
        
        await collector.resolveIncident(incidentId, 'Fixed by restarting service');
        
        const resolvedIncidents = collector.getIncidents();
        expect(resolvedIncidents[0].resolved).toBe(true);
        expect(resolvedIncidents[0].resolvedAt).toBeInstanceOf(Date);
        expect(resolvedIncidents[0].mttr).toBeGreaterThan(0);
      });

      it('should throw error when resolving non-existent incident', async () => {
        await expect(
          collector.resolveIncident('non-existent-id')
        ).rejects.toThrow('Incident non-existent-id not found');
      });
    });

    describe('Metrics Calculation', () => {
      beforeEach(async () => {
        await collector.initialize();
        
        // Add sample data
        const now = new Date();
        const deployments = [
          {
            environment: 'production' as const,
            version: 'v1.0.0',
            commit: 'abc123',
            success: true
          },
          {
            environment: 'production' as const,
            version: 'v1.0.1',
            commit: 'def456',
            success: true
          },
          {
            environment: 'production' as const,
            version: 'v1.0.2',
            commit: 'ghi789',
            success: false
          }
        ];

        for (const deployment of deployments) {
          await collector.recordDeployment(deployment);
        }

        const incidents = [
          {
            environment: 'production' as const,
            severity: 'high' as const,
            description: 'Database connection timeout'
          },
          {
            environment: 'production' as const,
            severity: 'medium' as const,
            description: 'Slow API response'
          }
        ];

        for (const incident of incidents) {
          await collector.recordIncident(incident);
        }

        // Resolve one incident
        const allIncidents = collector.getIncidents();
        if (allIncidents.length > 0) {
          setTimeout(async () => {
            await collector.resolveIncident(allIncidents[0].id);
          }, 50);
        }
      });

      it('should calculate deployment frequency', async () => {
        // Wait for incident resolution
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const metrics = collector.calculateMetrics();
        
        expect(metrics.deploymentFrequency.value).toBeGreaterThan(0);
        expect(metrics.deploymentFrequency.unit).toBeDefined();
        expect(metrics.deploymentFrequency.classification).toBeOneOf(['elite', 'high', 'medium', 'low']);
      });

      it('should calculate change failure rate', async () => {
        const metrics = collector.calculateMetrics();
        
        expect(metrics.changeFailureRate.value).toBeCloseTo(33.33, 1); // 1 failed out of 3
        expect(metrics.changeFailureRate.failed).toBe(1);
        expect(metrics.changeFailureRate.total).toBe(3);
        expect(metrics.changeFailureRate.classification).toBeDefined();
      });

      it('should calculate MTTR for resolved incidents', async () => {
        // Wait for incident resolution
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const metrics = collector.calculateMetrics();
        
        if (metrics.mttr.incidents > 0) {
          expect(metrics.mttr.value).toBeGreaterThan(0);
          expect(metrics.mttr.unit).toBeDefined();
          expect(metrics.mttr.classification).toBeDefined();
        }
      });

      it('should handle empty data gracefully', async () => {
        const emptyCollector = new DORAMetricsCollector({
          dataPath: '/tmp/empty-test'
        });
        
        await emptyCollector.initialize();
        const metrics = emptyCollector.calculateMetrics();
        
        expect(metrics.deploymentFrequency.value).toBe(0);
        expect(metrics.leadTime.value).toBe(0);
        expect(metrics.mttr.value).toBe(0);
        expect(metrics.changeFailureRate.value).toBe(0);
      });

      it('should calculate metrics for custom time periods', async () => {
        const endDate = new Date();
        const startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000); // 7 days
        
        const metrics = collector.calculateMetrics(startDate, endDate);
        
        expect(metrics.period.days).toBe(7);
        expect(metrics.period.start).toEqual(startDate);
        expect(metrics.period.end).toEqual(endDate);
      });
    });

    describe('DORA Classifications', () => {
      it('should classify deployment frequency correctly', async () => {
        await collector.initialize();
        
        // Test elite classification (daily deployments)
        for (let i = 0; i < 30; i++) {
          await collector.recordDeployment({
            environment: 'production' as const,
            version: `v1.0.${i}`,
            commit: `commit${i}`,
            success: true
          });
        }
        
        const metrics = collector.calculateMetrics();
        expect(metrics.deploymentFrequency.classification).toBe('elite');
      });

      it('should classify change failure rate correctly', async () => {
        await collector.initialize();
        
        // Test elite classification (<5% failure rate)
        for (let i = 0; i < 20; i++) {
          await collector.recordDeployment({
            environment: 'production' as const,
            version: `v1.0.${i}`,
            commit: `commit${i}`,
            success: true
          });
        }
        
        // Add one failure (5% failure rate)
        await collector.recordDeployment({
          environment: 'production' as const,
          version: 'v1.0.failed',
          commit: 'commitfailed',
          success: false
        });
        
        const metrics = collector.calculateMetrics();
        expect(metrics.changeFailureRate.value).toBeCloseTo(4.76, 1);
        expect(metrics.changeFailureRate.classification).toBe('elite');
      });
    });

    describe('Data Management', () => {
      beforeEach(async () => {
        await collector.initialize();
      });

      it('should export data in JSON format', async () => {
        await collector.recordDeployment({
          environment: 'production' as const,
          version: 'v1.0.0',
          commit: 'abc123',
          success: true
        });

        const exportedData = await collector.exportData('json');
        const parsed = JSON.parse(exportedData);
        
        expect(parsed.deployments).toHaveLength(1);
        expect(parsed.deployments[0].version).toBe('v1.0.0');
        expect(parsed.exportDate).toBeDefined();
      });

      it('should filter deployments by environment', async () => {
        await collector.recordDeployment({
          environment: 'production' as const,
          version: 'v1.0.0',
          commit: 'abc123',
          success: true
        });

        await collector.recordDeployment({
          environment: 'staging' as const,
          version: 'v1.1.0',
          commit: 'def456',
          success: true
        });

        const productionDeployments = collector.getDeployments('production');
        const stagingDeployments = collector.getDeployments('staging');
        
        expect(productionDeployments).toHaveLength(1);
        expect(stagingDeployments).toHaveLength(1);
        expect(productionDeployments[0].environment).toBe('production');
        expect(stagingDeployments[0].environment).toBe('staging');
      });

      it('should limit returned results', async () => {
        for (let i = 0; i < 10; i++) {
          await collector.recordDeployment({
            environment: 'production' as const,
            version: `v1.0.${i}`,
            commit: `commit${i}`,
            success: true
          });
        }

        const limitedDeployments = collector.getDeployments(undefined, 5);
        expect(limitedDeployments).toHaveLength(5);
      });

      it('should sort deployments by timestamp descending', async () => {
        const versions = ['v1.0.0', 'v1.0.1', 'v1.0.2'];
        
        for (const version of versions) {
          await collector.recordDeployment({
            environment: 'production' as const,
            version,
            commit: 'commit',
            success: true
          });
          // Small delay to ensure different timestamps
          await new Promise(resolve => setTimeout(resolve, 1));
        }

        const deployments = collector.getDeployments();
        expect(deployments[0].version).toBe('v1.0.2'); // Most recent first
        expect(deployments[2].version).toBe('v1.0.0'); // Oldest last
      });
    });
  });

  describe('DORADashboard', () => {
    beforeEach(async () => {
      await collector.initialize();
      
      // Add sample data for dashboard testing
      await collector.recordDeployment({
        environment: 'production' as const,
        version: 'v1.0.0',
        commit: 'abc123',
        success: true
      });

      await collector.recordIncident({
        environment: 'production' as const,
        severity: 'high' as const,
        description: 'API timeout'
      });
    });

    it('should display simple dashboard without errors', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const clearSpy = vi.spyOn(console, 'clear').mockImplementation(() => {});

      await dashboard.displaySimple();

      expect(clearSpy).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalled();
      
      // Check that DORA metrics are displayed
      const output = consoleSpy.mock.calls.map(call => call.join(' ')).join('\n');
      expect(output).toContain('DORA Metrics');
      expect(output).toContain('Deployment Frequency');
      expect(output).toContain('Lead Time');
      expect(output).toContain('Mean Time to Recovery');
      expect(output).toContain('Change Failure Rate');

      consoleSpy.mockRestore();
      clearSpy.mockRestore();
    });

    it('should handle dashboard configuration', () => {
      const customDashboard = new DORADashboard(collector, {
        refreshInterval: 60000,
        historicalPeriod: 60,
        showTrends: false
      });

      expect(customDashboard['config'].refreshInterval).toBe(60000);
      expect(customDashboard['config'].historicalPeriod).toBe(60);
      expect(customDashboard['config'].showTrends).toBe(false);
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete workflow: deploy -> incident -> resolve', async () => {
      await collector.initialize();

      // Record a deployment
      await collector.recordDeployment({
        environment: 'production' as const,
        version: 'v2.0.0',
        commit: 'deploy123',
        success: true
      });

      // Record an incident caused by the deployment
      await collector.recordIncident({
        environment: 'production' as const,
        severity: 'critical' as const,
        description: 'Database migration failed',
        deploymentId: collector.getDeployments()[0].id
      });

      // Resolve the incident
      const incidents = collector.getIncidents();
      const incidentId = incidents[0].id;
      
      setTimeout(async () => {
        await collector.resolveIncident(incidentId, 'Rollback deployed');
      }, 10);

      await new Promise(resolve => setTimeout(resolve, 50));

      // Calculate metrics
      const metrics = collector.calculateMetrics();

      // Should have one deployment and one resolved incident
      expect(collector.getDeployments()).toHaveLength(1);
      expect(collector.getIncidents().filter(i => i.resolved)).toHaveLength(1);
      expect(metrics.changeFailureRate.total).toBe(1);
      expect(metrics.mttr.incidents).toBe(1);
    });

    it('should maintain data consistency across operations', async () => {
      await collector.initialize();

      const initialDeployments = collector.getDeployments().length;
      const initialIncidents = collector.getIncidents().length;

      // Perform multiple operations
      await collector.recordDeployment({
        environment: 'production' as const,
        version: 'v1.0.0',
        commit: 'abc123',
        success: true
      });

      await collector.recordIncident({
        environment: 'production' as const,
        severity: 'medium' as const,
        description: 'Minor issue'
      });

      const midDeployments = collector.getDeployments().length;
      const midIncidents = collector.getIncidents().length;

      expect(midDeployments).toBe(initialDeployments + 1);
      expect(midIncidents).toBe(initialIncidents + 1);

      // Resolve incident
      const incidents = collector.getIncidents();
      await collector.resolveIncident(incidents[incidents.length - 1].id);

      const finalIncidents = collector.getIncidents();
      const resolvedIncident = finalIncidents.find(i => i.resolved);
      
      expect(resolvedIncident).toBeDefined();
      expect(resolvedIncident?.mttr).toBeGreaterThan(0);
    });

    it('should handle concurrent operations safely', async () => {
      await collector.initialize();

      // Perform concurrent deployments
      const deploymentPromises = Array.from({ length: 5 }, (_, i) =>
        collector.recordDeployment({
          environment: 'production' as const,
          version: `v1.0.${i}`,
          commit: `commit${i}`,
          success: true
        })
      );

      const incidentPromises = Array.from({ length: 3 }, (_, i) =>
        collector.recordIncident({
          environment: 'production' as const,
          severity: 'low' as const,
          description: `Incident ${i}`
        })
      );

      await Promise.all([...deploymentPromises, ...incidentPromises]);

      expect(collector.getDeployments()).toHaveLength(5);
      expect(collector.getIncidents()).toHaveLength(3);

      // All deployments should have unique IDs
      const deployments = collector.getDeployments();
      const ids = deployments.map(d => d.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(deployments.length);
    });
  });

  describe('Error Handling', () => {
    it('should handle file system errors gracefully', async () => {
      (fs.writeFile as any).mockRejectedValue(new Error('Disk full'));

      await collector.initialize();

      await expect(
        collector.recordDeployment({
          environment: 'production' as const,
          version: 'v1.0.0',
          commit: 'abc123',
          success: true
        })
      ).rejects.toThrow('Disk full');
    });

    it('should handle Git command failures', async () => {
      (execSync as any).mockImplementation(() => {
        throw new Error('Git not found');
      });

      // Should not throw during initialization
      await expect(collector.initialize()).resolves.not.toThrow();
    });

    it('should handle malformed data files', async () => {
      (fs.readFile as any).mockResolvedValue('invalid json');

      // Should handle malformed JSON gracefully
      await expect(collector.initialize()).resolves.not.toThrow();
      expect(collector.getDeployments()).toHaveLength(0);
    });
  });
});