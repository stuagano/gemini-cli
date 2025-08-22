/**
 * Guardian Continuous Validation Tests
 * Tests for real-time validation and CLI integration
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import GuardianContinuousValidation, { ValidationSeverity, ValidationCategory } from './guardian-continuous-validation.js';
import { Config } from '@google/gemini-cli-core';
import { EventEmitter } from 'events';

// Mock dependencies
vi.mock('chokidar', () => ({
  default: {
    watch: vi.fn(() => ({
      on: vi.fn(),
      close: vi.fn(),
      getWatched: vi.fn(() => ({ '/test': ['file1.ts', 'file2.ts'] }))
    }))
  }
}));

vi.mock('chalk', () => ({
  default: {
    blue: vi.fn((text) => text),
    green: vi.fn((text) => text),
    yellow: vi.fn((text) => text),
    red: vi.fn((text) => text),
    gray: vi.fn((text) => text),
    bold: { red: vi.fn((text) => text) }
  }
}));

// Mock fetch
global.fetch = vi.fn();

describe('GuardianContinuousValidation', () => {
  let guardian: GuardianContinuousValidation;
  let mockConfig: Config;

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockConfig = {
      apiKey: 'test-key',
      model: 'gemini-pro',
    } as Config;

    guardian = new GuardianContinuousValidation(mockConfig);
    
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(async () => {
    vi.restoreAllMocks();
    await guardian.stopContinuousValidation();
  });

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      const status = guardian.getValidationStatus();
      
      expect(status.config.real_time_validation).toBe(true);
      expect(status.config.auto_fix_enabled).toBe(true);
      expect(status.config.validation_interval).toBe(5000);
      expect(status.config.include_patterns).toContain('*.ts');
      expect(status.config.exclude_patterns).toContain('node_modules/');
    });

    it('should have initial stats', () => {
      const status = guardian.getValidationStatus();
      
      expect(status.stats.validations_run).toBe(0);
      expect(status.stats.issues_found).toBe(0);
      expect(status.stats.issues_auto_fixed).toBe(0);
      expect(status.stats.last_validation).toBeNull();
    });
  });

  describe('Configuration Management', () => {
    it('should update configuration', () => {
      const newConfig = {
        real_time_validation: false,
        validation_interval: 10000,
        auto_fix_enabled: false
      };
      
      guardian.updateConfig(newConfig);
      const status = guardian.getValidationStatus();
      
      expect(status.config.real_time_validation).toBe(false);
      expect(status.config.validation_interval).toBe(10000);
      expect(status.config.auto_fix_enabled).toBe(false);
    });

    it('should emit config_updated event', (done) => {
      guardian.on('config_updated', (config) => {
        expect(config.real_time_validation).toBe(false);
        done();
      });
      
      guardian.updateConfig({ real_time_validation: false });
    });
  });

  describe('File Validation', () => {
    beforeEach(() => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          issues: [
            {
              id: 'test-issue-1',
              rule_id: 'sec_001',
              severity: ValidationSeverity.ERROR,
              category: ValidationCategory.SECURITY,
              title: 'Test Issue',
              description: 'Test description',
              file_path: '/test/file.ts',
              line_number: 10,
              auto_fixable: false,
              resolved: false,
              timestamp: new Date()
            }
          ]
        })
      });
    });

    it('should validate a single file', async () => {
      const issues = await guardian.validateFile('/test/file.ts');
      
      expect(issues).toHaveLength(1);
      expect(issues[0].title).toBe('Test Issue');
      expect(issues[0].severity).toBe(ValidationSeverity.ERROR);
      expect(issues[0].category).toBe(ValidationCategory.SECURITY);
    });

    it('should skip excluded files', async () => {
      const issues = await guardian.validateFile('/test/node_modules/file.js');
      
      expect(issues).toHaveLength(0);
      expect(fetch).not.toHaveBeenCalled();
    });

    it('should skip files that don\'t match include patterns', async () => {
      const issues = await guardian.validateFile('/test/README.md');
      
      expect(issues).toHaveLength(0);
      expect(fetch).not.toHaveBeenCalled();
    });

    it('should emit issues_found event', (done) => {
      guardian.on('issues_found', (data) => {
        expect(data.file).toBe('/test/file.ts');
        expect(data.issues).toHaveLength(1);
        done();
      });
      
      guardian.validateFile('/test/file.ts');
    });

    it('should handle validation errors gracefully', async () => {
      (fetch as any).mockRejectedValue(new Error('Network error'));
      
      const issues = await guardian.validateFile('/test/file.ts');
      
      expect(issues).toHaveLength(0);
      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('Project Validation', () => {
    beforeEach(() => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          session_id: 'test-session-123',
          timestamp: new Date().toISOString(),
          duration_seconds: 2.5,
          files_checked: 10,
          rules_executed: 8,
          issues_found: [
            {
              id: 'issue-1',
              severity: ValidationSeverity.ERROR,
              category: ValidationCategory.SECURITY,
              title: 'Security Issue',
              file_path: '/test/file1.ts'
            },
            {
              id: 'issue-2',
              severity: ValidationSeverity.WARNING,
              category: ValidationCategory.QUALITY,
              title: 'Quality Issue',
              file_path: '/test/file2.ts'
            }
          ],
          performance_metrics: {
            files_per_second: 4.0,
            issues_per_file: 0.2
          },
          summary: {
            [ValidationSeverity.ERROR]: 1,
            [ValidationSeverity.WARNING]: 1
          }
        })
      });
    });

    it('should validate entire project', async () => {
      const report = await guardian.validateProject();
      
      expect(report.session_id).toBe('test-session-123');
      expect(report.files_checked).toBe(10);
      expect(report.rules_executed).toBe(8);
      expect(report.issues_found).toHaveLength(2);
      expect(report.summary[ValidationSeverity.ERROR]).toBe(1);
      expect(report.summary[ValidationSeverity.WARNING]).toBe(1);
    });

    it('should emit project_validated event', (done) => {
      guardian.on('project_validated', (report) => {
        expect(report.session_id).toBe('test-session-123');
        expect(report.issues_found).toHaveLength(2);
        done();
      });
      
      guardian.validateProject();
    });

    it('should update validation stats', async () => {
      await guardian.validateProject();
      
      const status = guardian.getValidationStatus();
      expect(status.stats.validations_run).toBe(1);
      expect(status.stats.issues_found).toBe(2);
      expect(status.stats.last_validation).not.toBeNull();
    });
  });

  describe('Continuous Validation', () => {
    beforeEach(() => {
      // Mock successful backend initialization
      (fetch as any).mockImplementation((url: string) => {
        if (url.includes('/status')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ active_rules: 10 })
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ issues: [] })
        });
      });
    });

    it('should start continuous validation', async () => {
      let validationStarted = false;
      guardian.on('validation_started', () => {
        validationStarted = true;
      });
      
      await guardian.startContinuousValidation('/test/project');
      
      expect(validationStarted).toBe(true);
      const status = guardian.getValidationStatus();
      expect(status.active).toBe(true);
    });

    it('should stop continuous validation', async () => {
      await guardian.startContinuousValidation('/test/project');
      
      let validationStopped = false;
      guardian.on('validation_stopped', () => {
        validationStopped = true;
      });
      
      await guardian.stopContinuousValidation();
      
      expect(validationStopped).toBe(true);
      const status = guardian.getValidationStatus();
      expect(status.active).toBe(false);
    });

    it('should handle backend initialization failure', async () => {
      (fetch as any).mockRejectedValue(new Error('Backend not available'));
      
      // Should not throw, but use fallback mode
      await expect(guardian.startContinuousValidation()).resolves.not.toThrow();
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Guardian backend not available')
      );
    });
  });

  describe('Pre-commit Validation', () => {
    beforeEach(() => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          validation_passed: false,
          issues_found: 2,
          issues: [
            {
              severity: 'error',
              title: 'Security Issue',
              file: '/test/file1.ts',
              line: 10
            },
            {
              severity: 'warning',
              title: 'Quality Issue',
              file: '/test/file2.ts',
              line: 20
            }
          ],
          blocking_reason: '2 error issues (threshold: 0)'
        })
      });
    });

    it('should validate before commit', async () => {
      const result = await guardian.validateBeforeCommit(['/test/file1.ts', '/test/file2.ts']);
      
      expect(result.validation_passed).toBe(false);
      expect(result.issues_found).toBe(2);
      expect(result.issues).toHaveLength(2);
      expect(result.blocking_reason).toBe('2 error issues (threshold: 0)');
    });

    it('should pass validation when no blocking issues', async () => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          validation_passed: true,
          issues_found: 1,
          issues: [
            {
              severity: 'info',
              title: 'Info Issue',
              file: '/test/file1.ts',
              line: 5
            }
          ]
        })
      });
      
      const result = await guardian.validateBeforeCommit(['/test/file1.ts']);
      
      expect(result.validation_passed).toBe(true);
      expect(result.issues_found).toBe(1);
    });

    it('should handle API errors gracefully', async () => {
      (fetch as any).mockRejectedValue(new Error('API Error'));
      
      const result = await guardian.validateBeforeCommit(['/test/file1.ts']);
      
      expect(result.validation_passed).toBe(false);
      expect(result.blocking_reason).toContain('Validation service error');
    });
  });

  describe('Pre-deployment Validation', () => {
    beforeEach(() => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          deployment_approved: true,
          validation_report: {
            session_id: 'deploy-session-123',
            issues_found: [],
            files_checked: 50,
            duration_seconds: 10.0
          }
        })
      });
    });

    it('should validate before deployment', async () => {
      const result = await guardian.validateBeforeDeployment('staging');
      
      expect(result.deployment_approved).toBe(true);
      expect(result.validation_report.session_id).toBe('deploy-session-123');
      expect(result.validation_report.files_checked).toBe(50);
    });

    it('should reject deployment with critical issues', async () => {
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          deployment_approved: false,
          validation_report: {
            session_id: 'deploy-session-456',
            issues_found: [
              {
                severity: ValidationSeverity.CRITICAL,
                title: 'Critical Security Issue'
              }
            ]
          },
          blocking_reason: '1 critical issues (threshold: 0)'
        })
      });
      
      const result = await guardian.validateBeforeDeployment('production');
      
      expect(result.deployment_approved).toBe(false);
      expect(result.blocking_reason).toBe('1 critical issues (threshold: 0)');
    });
  });

  describe('Auto-fixing', () => {
    beforeEach(() => {
      guardian.updateConfig({ auto_fix_enabled: true });
    });

    it('should attempt auto-fixes for fixable issues', async () => {
      // Mock file validation with auto-fixable issue
      (fetch as any).mockImplementation((url: string) => {
        if (url.includes('/validate-file')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              issues: [
                {
                  id: 'fixable-issue',
                  auto_fixable: true,
                  title: 'Auto-fixable Issue'
                }
              ]
            })
          });
        }
        if (url.includes('/auto-fix')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ fixes_applied: 1 })
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });
      
      let autoFixesApplied = false;
      guardian.on('auto_fixes_applied', (data) => {
        expect(data.file).toBe('/test/file.ts');
        expect(data.fixes).toBe(1);
        autoFixesApplied = true;
      });
      
      await guardian.validateFile('/test/file.ts');
      
      expect(autoFixesApplied).toBe(true);
    });

    it('should not attempt auto-fixes when disabled', async () => {
      guardian.updateConfig({ auto_fix_enabled: false });
      
      (fetch as any).mockImplementation((url: string) => {
        if (url.includes('/validate-file')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              issues: [{ id: 'fixable-issue', auto_fixable: true }]
            })
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });
      
      await guardian.validateFile('/test/file.ts');
      
      // Should not call auto-fix endpoint
      expect(fetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/auto-fix'),
        expect.any(Object)
      );
    });
  });

  describe('Event Handling', () => {
    it('should emit validation_error on API failure', (done) => {
      (fetch as any).mockRejectedValue(new Error('API Error'));
      
      guardian.on('validation_error', (data) => {
        expect(data.file).toBe('/test/file.ts');
        expect(data.error).toBeInstanceOf(Error);
        done();
      });
      
      guardian.validateFile('/test/file.ts');
    });

    it('should emit blocking_issues when thresholds exceeded', async () => {
      const report = {
        issues_found: [
          { severity: ValidationSeverity.CRITICAL, title: 'Critical Issue' },
          { severity: ValidationSeverity.ERROR, title: 'Error Issue 1' },
          { severity: ValidationSeverity.ERROR, title: 'Error Issue 2' }
        ]
      };
      
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => report
      });
      
      let blockingIssuesDetected = false;
      guardian.on('blocking_issues', (issues) => {
        expect(issues).toContain('1 critical issues (threshold: 0)');
        blockingIssuesDetected = true;
      });
      
      await guardian.validateProject();
      
      expect(blockingIssuesDetected).toBe(true);
    });
  });

  describe('Status and Reporting', () => {
    it('should return comprehensive status', () => {
      const status = guardian.getValidationStatus();
      
      expect(status).toHaveProperty('active');
      expect(status).toHaveProperty('stats');
      expect(status).toHaveProperty('recent_issues');
      expect(status).toHaveProperty('config');
      
      expect(status.stats).toHaveProperty('validations_run');
      expect(status.stats).toHaveProperty('issues_found');
      expect(status.stats).toHaveProperty('issues_auto_fixed');
      expect(status.stats).toHaveProperty('avg_validation_time');
      expect(status.stats).toHaveProperty('files_monitored');
      expect(status.stats).toHaveProperty('last_validation');
    });

    it('should store recent issues', async () => {
      const mockIssues = Array.from({ length: 60 }, (_, i) => ({
        id: `issue-${i}`,
        title: `Issue ${i}`,
        severity: ValidationSeverity.WARNING,
        category: ValidationCategory.QUALITY
      }));
      
      (fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({
          session_id: 'test-session',
          timestamp: new Date().toISOString(),
          duration_seconds: 1.0,
          files_checked: 1,
          rules_executed: 1,
          issues_found: mockIssues,
          performance_metrics: {},
          summary: {}
        })
      });
      
      await guardian.validateProject();
      
      const status = guardian.getValidationStatus();
      // Should only keep last 50 issues
      expect(status.recent_issues).toHaveLength(50);
    });
  });

  describe('Performance', () => {
    it('should track validation timing', async () => {
      (fetch as any).mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ issues: [] })
          }), 100)
        )
      );
      
      const startTime = Date.now();
      await guardian.validateFile('/test/file.ts');
      const endTime = Date.now();
      
      const status = guardian.getValidationStatus();
      expect(status.stats.avg_validation_time).toBeGreaterThan(0);
      expect(status.stats.avg_validation_time).toBeLessThan(endTime - startTime + 50); // Allow some margin
    });
  });
});