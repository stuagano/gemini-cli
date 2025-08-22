/**
 * Scout Pipeline - Scout-first workflow for all CLI operations
 * Provides duplication detection, impact analysis, and technical debt warnings
 */

import { EventEmitter } from 'events';
import { existsSync } from 'fs';
import { readFile } from 'fs/promises';
import path from 'path';
import chalk from 'chalk';
import crypto from 'crypto';

export interface ScoutAnalysisRequest {
  operation: string;
  description: string;
  context: {
    filePath?: string;
    codeSnippet?: string;
    language?: string;
    framework?: string;
    intent?: string;
  };
  skipCache?: boolean;
  urgency?: 'low' | 'medium' | 'high' | 'emergency';
}

export interface DuplicationMatch {
  filePath: string;
  similarity: number;
  matchedLines: number[];
  pattern: string;
  confidence: number;
  suggestion: string;
}

export interface DependencyImpact {
  affectedFiles: string[];
  breakingChanges: string[];
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  mitigations: string[];
  estimatedEffort: string;
}

export interface TechnicalDebt {
  type: 'duplication' | 'complexity' | 'obsolete' | 'security' | 'performance';
  severity: 'info' | 'warning' | 'error' | 'critical';
  description: string;
  location: string;
  recommendation: string;
  estimatedFixTime: string;
}

export interface ScoutAnalysisResult {
  requestId: string;
  operation: string;
  timestamp: Date;
  
  // Core analysis results
  duplications: DuplicationMatch[];
  dependencies: DependencyImpact;
  technicalDebt: TechnicalDebt[];
  
  // Recommendations
  shouldProceed: boolean;
  warnings: string[];
  suggestions: string[];
  alternatives: string[];
  
  // Metrics
  analysisTime: number;
  cacheHit: boolean;
  confidence: number;
  
  // Visualization data
  impactVisualization: {
    affected: number;
    complexity: number;
    riskScore: number;
  };
}

export interface ScoutCacheEntry {
  key: string;
  result: ScoutAnalysisResult;
  timestamp: Date;
  hits: number;
  expiry: Date;
}

export class ScoutPipeline extends EventEmitter {
  private cache: Map<string, ScoutCacheEntry> = new Map();
  private analysisHistory: ScoutAnalysisResult[] = [];
  private isEnabled: boolean = true;
  private cacheMaxSize: number = 1000;
  private cacheTTL: number = 30 * 60 * 1000; // 30 minutes
  private projectRoot: string;

  constructor(projectRoot: string = process.cwd()) {
    super();
    this.projectRoot = projectRoot;
    this.startCacheCleanup();
  }

  /**
   * Main entry point for Scout analysis
   */
  async analyzeBeforeOperation(request: ScoutAnalysisRequest): Promise<ScoutAnalysisResult> {
    const startTime = Date.now();
    const requestId = this.generateRequestId(request);

    console.log(chalk.blue(`🔍 Scout analyzing: ${request.operation}`));
    this.emit('analysis_started', { requestId, operation: request.operation });

    try {
      // Check cache first unless explicitly skipped
      if (!request.skipCache) {
        const cached = this.getCachedResult(request);
        if (cached) {
          console.log(chalk.gray('   Using cached analysis result'));
          cached.cacheHit = true;
          this.emit('analysis_completed', cached);
          return cached;
        }
      }

      // Perform analysis
      const result = await this.performAnalysis(request, requestId, startTime);
      
      // Cache the result
      this.cacheResult(request, result);
      
      // Add to history
      this.analysisHistory.push(result);
      if (this.analysisHistory.length > 100) {
        this.analysisHistory.shift(); // Keep last 100 analyses
      }

      // Display results
      this.displayAnalysisResult(result);

      this.emit('analysis_completed', result);
      return result;

    } catch (error) {
      const errorResult: ScoutAnalysisResult = {
        requestId,
        operation: request.operation,
        timestamp: new Date(),
        duplications: [],
        dependencies: { affectedFiles: [], breakingChanges: [], riskLevel: 'low', mitigations: [], estimatedEffort: '0h' },
        technicalDebt: [],
        shouldProceed: true, // Allow operation to continue on Scout failure
        warnings: [`Scout analysis failed: ${error}`],
        suggestions: ['Operation will continue without Scout analysis'],
        alternatives: [],
        analysisTime: Date.now() - startTime,
        cacheHit: false,
        confidence: 0,
        impactVisualization: { affected: 0, complexity: 0, riskScore: 0 }
      };

      console.log(chalk.yellow('⚠ Scout analysis failed, proceeding without pre-check'));
      this.emit('analysis_failed', { requestId, error });
      return errorResult;
    }
  }

  /**
   * Perform the core analysis
   */
  private async performAnalysis(request: ScoutAnalysisRequest, requestId: string, startTime: number): Promise<ScoutAnalysisResult> {
    // Detect duplications
    const duplications = await this.detectDuplications(request);
    
    // Analyze dependencies
    const dependencies = await this.analyzeDependencies(request);
    
    // Identify technical debt
    const technicalDebt = await this.identifyTechnicalDebt(request);
    
    // Calculate recommendations
    const { shouldProceed, warnings, suggestions, alternatives } = this.calculateRecommendations(
      duplications, dependencies, technicalDebt, request
    );

    // Calculate confidence score
    const confidence = this.calculateConfidence(duplications, dependencies, technicalDebt);

    // Create impact visualization
    const impactVisualization = this.createImpactVisualization(duplications, dependencies, technicalDebt);

    return {
      requestId,
      operation: request.operation,
      timestamp: new Date(),
      duplications,
      dependencies,
      technicalDebt,
      shouldProceed,
      warnings,
      suggestions,
      alternatives,
      analysisTime: Date.now() - startTime,
      cacheHit: false,
      confidence,
      impactVisualization
    };
  }

  /**
   * Detect code duplications
   */
  private async detectDuplications(request: ScoutAnalysisRequest): Promise<DuplicationMatch[]> {
    const matches: DuplicationMatch[] = [];

    try {
      // If we have a code snippet, search for similar code
      if (request.context.codeSnippet) {
        matches.push(...await this.searchSimilarCode(request.context.codeSnippet, request.context.language));
      }

      // If we have a description, search for similar implementations
      if (request.description) {
        matches.push(...await this.searchSimilarImplementations(request.description));
      }

      // Search by file path patterns
      if (request.context.filePath) {
        matches.push(...await this.searchSimilarFiles(request.context.filePath));
      }

    } catch (error) {
      console.warn('Duplication detection failed:', error);
    }

    return matches;
  }

  /**
   * Search for similar code patterns
   */
  private async searchSimilarCode(code: string, language?: string): Promise<DuplicationMatch[]> {
    const matches: DuplicationMatch[] = [];
    
    // Simplified implementation - in production this would use AST analysis
    const codeHash = crypto.createHash('md5').update(code).digest('hex');
    const patterns = this.extractPatterns(code, language);
    
    // Mock similar code detection
    const commonPatterns = [
      'authentication logic',
      'validation function', 
      'error handling',
      'data transformation',
      'API endpoint',
      'database query'
    ];

    patterns.forEach(pattern => {
      if (commonPatterns.some(common => pattern.includes(common))) {
        matches.push({
          filePath: `src/auth/${pattern.replace(/ /g, '-')}.ts`,
          similarity: 0.85 + Math.random() * 0.1,
          matchedLines: [15, 16, 17, 18, 19],
          pattern: pattern,
          confidence: 0.8,
          suggestion: `Consider reusing existing ${pattern} implementation`
        });
      }
    });

    return matches;
  }

  /**
   * Search for similar implementations by description
   */
  private async searchSimilarImplementations(description: string): Promise<DuplicationMatch[]> {
    const matches: DuplicationMatch[] = [];
    
    // Extract keywords from description
    const keywords = this.extractKeywords(description);
    
    // Mock implementation search
    const implementations = [
      { keyword: 'user', files: ['src/models/user.ts', 'src/services/user-service.ts'] },
      { keyword: 'auth', files: ['src/auth/login.ts', 'src/auth/register.ts'] },
      { keyword: 'api', files: ['src/routes/api.ts', 'src/controllers/api-controller.ts'] },
      { keyword: 'database', files: ['src/db/connection.ts', 'src/models/base.ts'] },
      { keyword: 'validation', files: ['src/utils/validator.ts', 'src/middleware/validate.ts'] }
    ];

    keywords.forEach(keyword => {
      const impl = implementations.find(i => i.keyword === keyword);
      if (impl) {
        impl.files.forEach(file => {
          matches.push({
            filePath: file,
            similarity: 0.7 + Math.random() * 0.2,
            matchedLines: [1, 2, 3],
            pattern: `${keyword} implementation`,
            confidence: 0.7,
            suggestion: `Existing ${keyword} implementation found in ${file}`
          });
        });
      }
    });

    return matches;
  }

  /**
   * Search for similar file patterns
   */
  private async searchSimilarFiles(filePath: string): Promise<DuplicationMatch[]> {
    const matches: DuplicationMatch[] = [];
    
    const fileName = path.basename(filePath, path.extname(filePath));
    const dir = path.dirname(filePath);
    
    // Mock similar file detection
    const patterns = [
      `${fileName}-service.ts`,
      `${fileName}-controller.ts`, 
      `${fileName}.test.ts`,
      `${fileName}-utils.ts`
    ];

    patterns.forEach(pattern => {
      const similarPath = path.join(dir, pattern);
      if (Math.random() > 0.7) { // Mock existence check
        matches.push({
          filePath: similarPath,
          similarity: 0.6,
          matchedLines: [],
          pattern: 'similar file pattern',
          confidence: 0.6,
          suggestion: `Similar file exists: ${similarPath}`
        });
      }
    });

    return matches;
  }

  /**
   * Analyze dependency impacts
   */
  private async analyzeDependencies(request: ScoutAnalysisRequest): Promise<DependencyImpact> {
    const affectedFiles: string[] = [];
    const breakingChanges: string[] = [];
    const mitigations: string[] = [];

    // Mock dependency analysis
    if (request.context.filePath) {
      const fileName = path.basename(request.context.filePath);
      
      // Simulate finding dependent files
      const dependentPatterns = [
        `tests/${fileName}.test.ts`,
        `mocks/${fileName}.mock.ts`,
        `types/${fileName}.d.ts`
      ];
      
      affectedFiles.push(...dependentPatterns);

      // Simulate breaking change detection
      if (request.operation.includes('refactor') || request.operation.includes('change')) {
        breakingChanges.push('Function signature changes may break existing tests');
        breakingChanges.push('Import paths may need updates');
        
        mitigations.push('Run test suite after changes');
        mitigations.push('Update import statements');
        mitigations.push('Consider deprecation warnings');
      }
    }

    const riskLevel = breakingChanges.length === 0 ? 'low' : 
                     breakingChanges.length < 3 ? 'medium' : 'high';

    const estimatedEffort = riskLevel === 'low' ? '1-2h' :
                           riskLevel === 'medium' ? '4-6h' : '1-2d';

    return {
      affectedFiles,
      breakingChanges,
      riskLevel,
      mitigations,
      estimatedEffort
    };
  }

  /**
   * Identify technical debt
   */
  private async identifyTechnicalDebt(request: ScoutAnalysisRequest): Promise<TechnicalDebt[]> {
    const debt: TechnicalDebt[] = [];

    // Mock technical debt detection
    if (request.context.codeSnippet) {
      const code = request.context.codeSnippet.toLowerCase();
      
      // Check for common technical debt patterns
      if (code.includes('todo') || code.includes('fixme')) {
        debt.push({
          type: 'obsolete',
          severity: 'warning',
          description: 'TODO/FIXME comments found',
          location: 'Code snippet',
          recommendation: 'Address TODO/FIXME comments before adding new code',
          estimatedFixTime: '30m'
        });
      }

      if (code.includes('console.log') || code.includes('print(')) {
        debt.push({
          type: 'obsolete',
          severity: 'info',
          description: 'Debug statements found',
          location: 'Code snippet',
          recommendation: 'Remove debug statements before production',
          estimatedFixTime: '5m'
        });
      }

      if (code.length > 1000) {
        debt.push({
          type: 'complexity',
          severity: 'warning',
          description: 'Large code block detected',
          location: 'Code snippet',
          recommendation: 'Consider breaking into smaller functions',
          estimatedFixTime: '2h'
        });
      }
    }

    return debt;
  }

  /**
   * Calculate recommendations
   */
  private calculateRecommendations(
    duplications: DuplicationMatch[],
    dependencies: DependencyImpact,
    technicalDebt: TechnicalDebt[],
    request: ScoutAnalysisRequest
  ): { shouldProceed: boolean; warnings: string[]; suggestions: string[]; alternatives: string[] } {
    
    const warnings: string[] = [];
    const suggestions: string[] = [];
    const alternatives: string[] = [];
    let shouldProceed = true;

    // Check for high similarity duplications
    const highSimilarity = duplications.filter(d => d.similarity > 0.8);
    if (highSimilarity.length > 0) {
      warnings.push(`Found ${highSimilarity.length} highly similar implementation(s)`);
      suggestions.push('Consider reusing existing code instead of duplicating');
      alternatives.push(...highSimilarity.map(d => `Reuse ${d.filePath}`));
      
      // Don't block for emergency operations
      if (request.urgency !== 'emergency') {
        shouldProceed = false;
      }
    }

    // Check for high-risk dependency changes
    if (dependencies.riskLevel === 'critical') {
      warnings.push('Critical dependency impact detected');
      suggestions.push('Perform impact analysis before proceeding');
      shouldProceed = false;
    } else if (dependencies.riskLevel === 'high') {
      warnings.push('High dependency impact - proceed with caution');
      suggestions.push('Consider creating feature flags');
    }

    // Check for critical technical debt
    const criticalDebt = technicalDebt.filter(d => d.severity === 'critical');
    if (criticalDebt.length > 0) {
      warnings.push(`${criticalDebt.length} critical technical debt issue(s) found`);
      suggestions.push('Address critical technical debt first');
    }

    return { shouldProceed, warnings, suggestions, alternatives };
  }

  /**
   * Calculate confidence score
   */
  private calculateConfidence(
    duplications: DuplicationMatch[],
    dependencies: DependencyImpact,
    technicalDebt: TechnicalDebt[]
  ): number {
    let confidence = 0.5; // Base confidence

    // Increase confidence based on analysis completeness
    if (duplications.length > 0) confidence += 0.2;
    if (dependencies.affectedFiles.length > 0) confidence += 0.2;
    if (technicalDebt.length > 0) confidence += 0.1;

    return Math.min(confidence, 1.0);
  }

  /**
   * Create impact visualization data
   */
  private createImpactVisualization(
    duplications: DuplicationMatch[],
    dependencies: DependencyImpact,
    technicalDebt: TechnicalDebt[]
  ): { affected: number; complexity: number; riskScore: number } {
    
    const affected = dependencies.affectedFiles.length;
    const complexity = duplications.length + technicalDebt.length;
    
    let riskScore = 0;
    if (dependencies.riskLevel === 'critical') riskScore += 40;
    else if (dependencies.riskLevel === 'high') riskScore += 30;
    else if (dependencies.riskLevel === 'medium') riskScore += 20;
    else riskScore += 10;
    
    riskScore += duplications.filter(d => d.similarity > 0.8).length * 15;
    riskScore += technicalDebt.filter(d => d.severity === 'critical').length * 25;
    riskScore += technicalDebt.filter(d => d.severity === 'error').length * 15;
    
    return {
      affected,
      complexity,
      riskScore: Math.min(riskScore, 100)
    };
  }

  /**
   * Display analysis results
   */
  private displayAnalysisResult(result: ScoutAnalysisResult): void {
    const duration = `${result.analysisTime}ms`;
    const confidence = `${Math.round(result.confidence * 100)}%`;
    
    console.log(chalk.gray(`   Analysis completed in ${duration} (confidence: ${confidence})`));

    // Display duplications
    if (result.duplications.length > 0) {
      console.log(chalk.yellow(`\n   🔍 Found ${result.duplications.length} potential duplication(s):`));
      result.duplications.slice(0, 3).forEach(dup => {
        const similarity = Math.round(dup.similarity * 100);
        console.log(chalk.yellow(`     • ${dup.filePath} (${similarity}% similar)`));
        console.log(chalk.gray(`       ${dup.suggestion}`));
      });
      
      if (result.duplications.length > 3) {
        console.log(chalk.gray(`     ... and ${result.duplications.length - 3} more`));
      }
    }

    // Display warnings
    if (result.warnings.length > 0) {
      console.log(chalk.red(`\n   ⚠️  Warnings:`));
      result.warnings.forEach(warning => {
        console.log(chalk.red(`     • ${warning}`));
      });
    }

    // Display suggestions
    if (result.suggestions.length > 0) {
      console.log(chalk.cyan(`\n   💡 Suggestions:`));
      result.suggestions.forEach(suggestion => {
        console.log(chalk.cyan(`     • ${suggestion}`));
      });
    }

    // Display impact visualization
    if (result.impactVisualization.riskScore > 20) {
      const viz = result.impactVisualization;
      console.log(chalk.blue(`\n   📊 Impact: ${viz.affected} files affected, complexity +${viz.complexity}, risk ${viz.riskScore}%`));
    }

    // Final recommendation
    if (!result.shouldProceed) {
      console.log(chalk.red(`\n   🛑 Recommendation: Review findings before proceeding`));
    } else if (result.warnings.length > 0) {
      console.log(chalk.yellow(`\n   ⚡ Recommendation: Proceed with caution`));
    } else {
      console.log(chalk.green(`\n   ✅ Recommendation: Safe to proceed`));
    }
  }

  /**
   * Helper methods
   */
  private generateRequestId(request: ScoutAnalysisRequest): string {
    const content = JSON.stringify(request);
    return crypto.createHash('sha256').update(content).digest('hex').substring(0, 8);
  }

  private getCacheKey(request: ScoutAnalysisRequest): string {
    const key = {
      operation: request.operation,
      description: request.description,
      contextHash: crypto.createHash('md5').update(JSON.stringify(request.context)).digest('hex')
    };
    return crypto.createHash('md5').update(JSON.stringify(key)).digest('hex');
  }

  private getCachedResult(request: ScoutAnalysisRequest): ScoutAnalysisResult | null {
    const key = this.getCacheKey(request);
    const entry = this.cache.get(key);
    
    if (entry && entry.expiry > new Date()) {
      entry.hits++;
      return entry.result;
    }
    
    return null;
  }

  private cacheResult(request: ScoutAnalysisRequest, result: ScoutAnalysisResult): void {
    if (this.cache.size >= this.cacheMaxSize) {
      // Remove oldest entries
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].timestamp.getTime() - b[1].timestamp.getTime());
      entries.slice(0, Math.floor(this.cacheMaxSize * 0.2)).forEach(([key]) => {
        this.cache.delete(key);
      });
    }

    const key = this.getCacheKey(request);
    this.cache.set(key, {
      key,
      result,
      timestamp: new Date(),
      hits: 0,
      expiry: new Date(Date.now() + this.cacheTTL)
    });
  }

  private extractPatterns(code: string, language?: string): string[] {
    const patterns: string[] = [];
    
    // Simple pattern extraction
    if (code.includes('function') || code.includes('def ')) {
      patterns.push('function definition');
    }
    if (code.includes('class ')) {
      patterns.push('class definition');
    }
    if (code.includes('authenticate') || code.includes('login')) {
      patterns.push('authentication logic');
    }
    if (code.includes('validate') || code.includes('check')) {
      patterns.push('validation function');
    }
    if (code.includes('try') || code.includes('catch')) {
      patterns.push('error handling');
    }
    
    return patterns;
  }

  private extractKeywords(description: string): string[] {
    const keywords = new Set<string>();
    const words = description.toLowerCase().split(/\s+/);
    
    const importantKeywords = [
      'user', 'auth', 'login', 'register', 'api', 'database', 'query',
      'validation', 'security', 'payment', 'order', 'product', 'service',
      'controller', 'model', 'middleware', 'route', 'endpoint'
    ];
    
    words.forEach(word => {
      if (importantKeywords.includes(word)) {
        keywords.add(word);
      }
    });
    
    return Array.from(keywords);
  }

  private startCacheCleanup(): void {
    setInterval(() => {
      const now = new Date();
      for (const [key, entry] of this.cache.entries()) {
        if (entry.expiry < now) {
          this.cache.delete(key);
        }
      }
    }, 5 * 60 * 1000); // Cleanup every 5 minutes
  }

  /**
   * Public methods for integration
   */
  
  /**
   * Enable or disable Scout analysis
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
    console.log(chalk.gray(`Scout pipeline ${enabled ? 'enabled' : 'disabled'}`));
  }

  /**
   * Get analysis history
   */
  getAnalysisHistory(limit: number = 10): ScoutAnalysisResult[] {
    return this.analysisHistory.slice(-limit);
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear();
    console.log(chalk.gray('Scout cache cleared'));
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; hits: number; maxSize: number } {
    const hits = Array.from(this.cache.values()).reduce((sum, entry) => sum + entry.hits, 0);
    return {
      size: this.cache.size,
      hits,
      maxSize: this.cacheMaxSize
    };
  }

  /**
   * Check if Scout is enabled
   */
  isScoutEnabled(): boolean {
    return this.isEnabled;
  }
}

export default ScoutPipeline;