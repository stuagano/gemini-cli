/**
 * Scaling Detector Tests
 * Comprehensive tests for the scaling issue detection system
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import ScalingDetector, { ScalingAnalysisRequest, ScalingIssue } from './scaling-detector.js';
import { DEMO_SCENARIOS } from './scaling-demo-scenarios.js';

describe('ScalingDetector', () => {
  let detector: ScalingDetector;

  beforeEach(() => {
    detector = new ScalingDetector();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('N+1 Query Detection', () => {
    it('should detect N+1 queries in for loops', async () => {
      const code = `
        for (const user of users) {
          const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
          user.orders = orders;
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      expect(result.issues).toBeDefined();
      expect(result.issues.length).toBeGreaterThan(0);

      const nPlusOneIssues = result.issues.filter(issue => issue.type === 'n_plus_one');
      expect(nPlusOneIssues.length).toBeGreaterThan(0);

      const criticalIssue = nPlusOneIssues.find(issue => issue.severity === 'critical');
      expect(criticalIssue).toBeDefined();
      expect(criticalIssue!.title).toContain('N+1 Query');
      expect(criticalIssue!.recommendation.solution).toContain('batch');
    });

    it('should detect N+1 queries in Array.map', async () => {
      const code = `
        const enrichedUsers = users.map(async user => ({
          ...user,
          profile: await getProfile(user.id)
        }));
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const mapIssues = result.issues.filter(issue => 
        issue.type === 'n_plus_one' && issue.title.includes('map')
      );
      
      expect(mapIssues.length).toBeGreaterThan(0);
      expect(mapIssues[0].severity).toBe('critical');
      expect(mapIssues[0].impact.loadIncrease).toBeGreaterThan(1000);
    });

    it('should detect N+1 queries in forEach', async () => {
      const code = `
        users.forEach(async user => {
          await updateUserStats(user.id);
        });
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const forEachIssues = result.issues.filter(issue => 
        issue.type === 'n_plus_one' && issue.title.includes('forEach')
      );
      
      expect(forEachIssues.length).toBeGreaterThan(0);
      expect(forEachIssues[0].recommendation.solution).toContain('bulk');
    });
  });

  describe('Memory Leak Detection', () => {
    it('should detect unclosed database connections', async () => {
      const code = `
        const connection = await pool.getConnection();
        const result = await connection.query('SELECT * FROM users');
        return result;
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const memoryLeaks = result.issues.filter(issue => issue.type === 'memory_leak');
      expect(memoryLeaks.length).toBeGreaterThan(0);

      const connectionLeak = memoryLeaks.find(issue => 
        issue.title.includes('Connection')
      );
      expect(connectionLeak).toBeDefined();
      expect(connectionLeak!.severity).toBe('high');
      expect(connectionLeak!.recommendation.solution).toContain('finally');
    });

    it('should detect event listener leaks', async () => {
      const code = `
        element.addEventListener('click', handler);
        button.on('press', callback);
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const eventLeaks = result.issues.filter(issue => 
        issue.type === 'memory_leak' && issue.title.includes('Event')
      );
      
      expect(eventLeaks.length).toBeGreaterThan(0);
      expect(eventLeaks[0].recommendation.solution).toContain('cleanup');
    });

    it('should detect global variable growth', async () => {
      const code = `
        global.cache = global.cache || [];
        global.cache.push(newData);
        var globalArray = [];
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const globalLeaks = result.issues.filter(issue => 
        issue.type === 'memory_leak' && issue.title.includes('Global')
      );
      
      expect(globalLeaks.length).toBeGreaterThan(0);
      expect(globalLeaks[0].recommendation.solution).toContain('size limits');
    });
  });

  describe('Inefficient Algorithm Detection', () => {
    it('should detect nested loops (O(n²) complexity)', async () => {
      const code = `
        for (const user of users) {
          for (const order of orders) {
            if (order.userId === user.id) {
              user.orders.push(order);
            }
          }
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const algorithmIssues = result.issues.filter(issue => issue.type === 'inefficient_algorithm');
      expect(algorithmIssues.length).toBeGreaterThan(0);

      const nestedLoopIssue = algorithmIssues.find(issue => 
        issue.title.includes('Nested Loops')
      );
      expect(nestedLoopIssue).toBeDefined();
      expect(nestedLoopIssue!.severity).toBe('high');
      expect(nestedLoopIssue!.impact.loadIncrease).toBeGreaterThan(5000);
    });

    it('should detect linear search in loops', async () => {
      const code = `
        for (const item of items) {
          const match = lookup.find(l => l.id === item.id);
          results.push(match);
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const linearSearchIssues = result.issues.filter(issue => 
        issue.type === 'inefficient_algorithm' && issue.title.includes('Linear Search')
      );
      
      expect(linearSearchIssues.length).toBeGreaterThan(0);
      expect(linearSearchIssues[0].recommendation.solution).toContain('lookup map');
    });

    it('should detect repeated expensive calculations', async () => {
      const code = `
        for (const item of items) {
          const hash = crypto.createHash('sha256').update(item.data).digest('hex');
          const complex = Math.pow(item.value, 10);
          results.push({ hash, complex });
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const calculationIssues = result.issues.filter(issue => 
        issue.type === 'inefficient_algorithm' && issue.title.includes('Calculations')
      );
      
      expect(calculationIssues.length).toBeGreaterThan(0);
      expect(calculationIssues[0].recommendation.solution).toContain('Cache');
    });
  });

  describe('Blocking Operations Detection', () => {
    it('should detect synchronous file operations', async () => {
      const code = `
        const data = fs.readFileSync('large-file.json');
        const exists = fs.existsSync('./config.json');
        fs.writeFileSync('./output.txt', data);
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const blockingIssues = result.issues.filter(issue => issue.type === 'blocking_operation');
      expect(blockingIssues.length).toBeGreaterThan(0);

      const fileOpIssue = blockingIssues.find(issue => 
        issue.title.includes('File Operation')
      );
      expect(fileOpIssue).toBeDefined();
      expect(fileOpIssue!.severity).toBe('high');
      expect(fileOpIssue!.recommendation.solution).toContain('async');
    });

    it('should detect synchronous network calls', async () => {
      const code = `
        const xhr = new XMLHttpRequest();
        xhr.open('GET', url, false);
        xhr.send();
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough'
      });

      const networkIssues = result.issues.filter(issue => 
        issue.type === 'blocking_operation' && issue.title.includes('Network')
      );
      
      expect(networkIssues.length).toBeGreaterThan(0);
      expect(networkIssues[0].severity).toBe('critical');
      expect(networkIssues[0].impact.estimatedBreakingPoint).toBe('1 concurrent user');
    });
  });

  describe('Risk Assessment', () => {
    it('should calculate overall risk correctly', async () => {
      const criticalCode = `
        for (const user of users) {
          const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
          user.orders = orders;
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: criticalCode,
        analysisDepth: 'thorough'
      });

      expect(result.overallRisk).toBe('critical');
      expect(result.estimatedUserCapacity).toBeLessThan(100);
    });

    it('should estimate user capacity based on issues', async () => {
      const lowRiskCode = `
        const users = await User.findAll();
        return users.map(user => ({ id: user.id, name: user.name }));
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: lowRiskCode,
        analysisDepth: 'thorough'
      });

      expect(result.overallRisk).toBe('low');
      expect(result.estimatedUserCapacity).toBeGreaterThan(1000);
    });

    it('should provide appropriate recommendations', async () => {
      const problematicCode = `
        for (const user of users) {
          const profile = await getProfile(user.id);
          for (const order of orders) {
            if (order.userId === user.id) {
              // process order
            }
          }
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: problematicCode,
        analysisDepth: 'thorough'
      });

      expect(result.recommendedActions.length).toBeGreaterThan(0);
      expect(result.recommendedActions.some(action => 
        action.includes('immediate') || action.includes('optimization')
      )).toBe(true);
    });
  });

  describe('Analysis Configuration', () => {
    it('should handle different analysis depths', async () => {
      const code = `
        for (const user of users) {
          const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
        }
      `;

      const quickResult = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'quick'
      });

      const comprehensiveResult = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive'
      });

      expect(quickResult.analysisTime).toBeLessThanOrEqual(comprehensiveResult.analysisTime);
      expect(quickResult.issues.length).toBeGreaterThan(0);
      expect(comprehensiveResult.issues.length).toBeGreaterThanOrEqual(quickResult.issues.length);
    });

    it('should include examples when requested', async () => {
      const code = `
        for (const user of users) {
          const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'thorough',
        includeExamples: true
      });

      const issueWithExamples = result.issues.find((issue: ScalingIssue) => 
        issue.examples && issue.examples.badCode && issue.examples.goodCode
      );

      expect(issueWithExamples).toBeDefined();
      expect(issueWithExamples!.examples.badCode).toContain('❌');
      expect(issueWithExamples!.examples.goodCode).toContain('✅');
      expect(issueWithExamples!.examples.explanation).toBeDefined();
    });
  });

  describe('Demo Scenarios Validation', () => {
    it('should detect issues in N+1 demo scenario', async () => {
      const code = DEMO_SCENARIOS.n_plus_one_examples.bad_user_orders;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive'
      });

      expect(result.issues.length).toBeGreaterThan(0);
      expect(result.overallRisk).toBe('critical');
      
      const nPlusOneIssues = result.issues.filter(issue => issue.type === 'n_plus_one');
      expect(nPlusOneIssues.length).toBeGreaterThan(0);
    });

    it('should detect issues in memory leak demo scenario', async () => {
      const code = DEMO_SCENARIOS.memory_leak_examples.bad_unclosed_connections;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive'
      });

      expect(result.issues.length).toBeGreaterThan(0);
      
      const memoryLeaks = result.issues.filter(issue => issue.type === 'memory_leak');
      expect(memoryLeaks.length).toBeGreaterThan(0);
    });

    it('should detect issues in algorithm demo scenario', async () => {
      const code = DEMO_SCENARIOS.inefficient_algorithm_examples.bad_nested_loops;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive'
      });

      expect(result.issues.length).toBeGreaterThan(0);
      
      const algorithmIssues = result.issues.filter(issue => issue.type === 'inefficient_algorithm');
      expect(algorithmIssues.length).toBeGreaterThan(0);
    });

    it('should detect issues in blocking operations demo scenario', async () => {
      const code = DEMO_SCENARIOS.blocking_operations_examples.bad_sync_file_operations;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive'
      });

      expect(result.issues.length).toBeGreaterThan(0);
      
      const blockingIssues = result.issues.filter(issue => issue.type === 'blocking_operation');
      expect(blockingIssues.length).toBeGreaterThan(0);
    });

    it('should detect multiple issue types in real-world disaster scenario', async () => {
      const code = DEMO_SCENARIOS.real_world_disasters.social_media_feed;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive'
      });

      expect(result.issues.length).toBeGreaterThan(3); // Should find multiple issues
      expect(result.overallRisk).toBe('critical');
      
      // Should detect multiple types of issues
      const issueTypes = new Set(result.issues.map((issue: ScalingIssue) => issue.type));
      expect(issueTypes.size).toBeGreaterThan(1);
      
      // Should include N+1 queries
      expect(result.issues.some((issue: ScalingIssue) => issue.type === 'n_plus_one')).toBe(true);
    });
  });

  describe('Performance and Accuracy', () => {
    it('should complete analysis within reasonable time', async () => {
      const largeCode = `
        ${'const users = await User.findAll();\n'.repeat(100)}
        for (const user of users) {
          const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
        }
      `;

      const startTime = Date.now();
      const result = await detector.analyzeForScalingIssues({
        codeSnippet: largeCode,
        analysisDepth: 'thorough'
      });
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
      expect(result.analysisTime).toBeLessThanOrEqual(duration + 1); // Allow for small timing differences
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    it('should maintain analysis history', async () => {
      const code1 = 'for (const user of users) { await getOrders(user.id); }';
      const code2 = 'const data = fs.readFileSync("file.json");';

      await detector.analyzeForScalingIssues({ codeSnippet: code1, analysisDepth: 'quick' });
      await detector.analyzeForScalingIssues({ codeSnippet: code2, analysisDepth: 'quick' });

      const history = detector.getAnalysisHistory();
      expect(history.length).toBe(2);
      expect(history[0].analysisId).toBeDefined();
      expect(history[1].analysisId).toBeDefined();
      expect(history[0].analysisId).not.toBe(history[1].analysisId);
    });

    it('should provide detection rule information', async () => {
      const rules = detector.getDetectionRules();
      
      expect(rules.length).toBeGreaterThan(5);
      expect(rules).toContain('n_plus_one_loops');
      expect(rules).toContain('unclosed_connections');
      expect(rules).toContain('nested_loops');
      expect(rules).toContain('sync_file_operations');
    });
  });

  describe('Error Handling', () => {
    it('should handle empty code gracefully', async () => {
      const result = await detector.analyzeForScalingIssues({
        codeSnippet: '',
        analysisDepth: 'quick'
      });

      expect(result.issues).toEqual([]);
      expect(result.overallRisk).toBe('low');
      expect(result.confidence).toBeGreaterThan(0);
    });

    it('should handle invalid file paths gracefully', async () => {
      const result = await detector.analyzeForScalingIssues({
        filePath: '/nonexistent/file.ts',
        analysisDepth: 'quick'
      });

      expect(result.issues).toEqual([]);
      expect(result.overallRisk).toBe('low');
    });

    it('should handle malformed code gracefully', async () => {
      const malformedCode = `
        for const user of users {
          await getOrders(user.id
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: malformedCode,
        analysisDepth: 'thorough'
      });

      // Should still try to detect patterns even in malformed code
      expect(result).toBeDefined();
      expect(result.confidence).toBeLessThan(1.0);
    });
  });

  describe('Integration with Examples', () => {
    it('should provide valid fix examples', async () => {
      const code = `
        for (const user of users) {
          const orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
        }
      `;

      const result = await detector.analyzeForScalingIssues({
        codeSnippet: code,
        analysisDepth: 'comprehensive',
        includeExamples: true
      });

      const issueWithExamples = result.issues.find((issue: ScalingIssue) => issue.examples);
      expect(issueWithExamples).toBeDefined();

      const { badCode, goodCode, explanation } = issueWithExamples!.examples;
      
      // Examples should be well-formed
      expect(badCode).toContain('❌');
      expect(goodCode).toContain('✅');
      expect(explanation).toBeTruthy();
      expect(explanation.length).toBeGreaterThan(20); // Meaningful explanation
      
      // Bad code should demonstrate the problem
      expect(badCode.toLowerCase()).toContain('for');
      
      // Good code should show the solution
      expect(goodCode.toLowerCase()).toContain('batch');
    });
  });
});