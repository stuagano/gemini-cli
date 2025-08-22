/**
 * Enhanced NLP Command Parser for Gemini Enterprise Architect
 * Provides sophisticated natural language understanding for CLI commands
 */

import { EventEmitter } from 'events';
import { NLCommand, AgentCapabilities } from './natural-language-cli.js';

// Enhanced interfaces for better NLP support
export interface EnhancedNLCommand extends NLCommand {
  alternatives: CommandAlternative[];
  contextualEntities: ContextualEntity[];
  ambiguityScore: number;
  suggestions: string[];
  preprocessedText: string;
  semanticTokens: SemanticToken[];
}

export interface CommandAlternative {
  intent: string;
  confidence: number;
  suggestedAgent: string;
  reasoning: string;
  entities: Record<string, any>;
}

export interface ContextualEntity {
  name: string;
  value: any;
  type: EntityType;
  confidence: number;
  context: string;
  position: [number, number]; // start, end positions in text
}

export interface SemanticToken {
  text: string;
  type: TokenType;
  lemma: string;
  partOfSpeech: string;
  namedEntity?: string;
  position: [number, number];
}

export enum EntityType {
  FILE_PATH = 'file_path',
  LANGUAGE = 'language',
  FRAMEWORK = 'framework',
  ACTION = 'action',
  TECHNOLOGY = 'technology',
  COMPONENT = 'component',
  PATTERN = 'pattern',
  METRIC = 'metric',
  TIMEFRAME = 'timeframe',
  PERSON = 'person',
  PROJECT = 'project'
}

export enum TokenType {
  VERB = 'verb',
  NOUN = 'noun',
  ADJECTIVE = 'adjective',
  ADVERB = 'adverb',
  PREPOSITION = 'preposition',
  ENTITY = 'entity',
  MODIFIER = 'modifier',
  CONNECTOR = 'connector'
}

export interface IntentPattern {
  name: string;
  patterns: RegExp[];
  keywords: string[];
  requiredEntities: EntityType[];
  confidence: number;
  agent: string;
  multiAgent: boolean;
  examples: string[];
}

export interface CommandSuggestion {
  command: string;
  description: string;
  confidence: number;
  reasoning: string;
  agent: string;
}

export class EnhancedNLPParser extends EventEmitter {
  private intentPatterns: IntentPattern[];
  private agentCapabilities: AgentCapabilities;
  private contextHistory: string[] = [];
  private entityExtractors: Map<EntityType, RegExp[]>;
  private synonyms: Map<string, string[]>;
  private stopWords: Set<string>;

  constructor(agentCapabilities: AgentCapabilities) {
    super();
    this.agentCapabilities = agentCapabilities;
    this.initializeIntentPatterns();
    this.initializeEntityExtractors();
    this.initializeSynonyms();
    this.initializeStopWords();
  }

  /**
   * Enhanced command parsing with sophisticated NLP
   */
  parseCommand(input: string, context?: string[]): EnhancedNLCommand {
    const startTime = Date.now();
    
    // Preprocess the input
    const preprocessedText = this.preprocessText(input);
    
    // Tokenize and extract semantic information
    const semanticTokens = this.extractSemanticTokens(preprocessedText);
    
    // Extract entities with context
    const contextualEntities = this.extractContextualEntities(preprocessedText, semanticTokens);
    
    // Classify intent with multiple possibilities
    const intentClassification = this.classifyIntent(preprocessedText, semanticTokens, contextualEntities);
    
    // Generate alternatives and handle ambiguity
    const alternatives = this.generateAlternatives(preprocessedText, semanticTokens, contextualEntities);
    
    // Calculate ambiguity score
    const ambiguityScore = this.calculateAmbiguityScore(intentClassification, alternatives);
    
    // Generate suggestions for unclear commands
    const suggestions = this.generateSuggestions(preprocessedText, intentClassification, ambiguityScore);
    
    // Update context history
    this.updateContextHistory(input, context);

    const processingTime = Date.now() - startTime;
    
    this.emit('parsing_completed', {
      input,
      processingTime,
      tokensExtracted: semanticTokens.length,
      entitiesFound: contextualEntities.length,
      alternativesGenerated: alternatives.length
    });

    const baseCommand = this.createBaseCommand(input, intentClassification);
    
    return {
      ...baseCommand,
      alternatives,
      contextualEntities,
      ambiguityScore,
      suggestions,
      preprocessedText,
      semanticTokens,
      entities: this.consolidateEntities(contextualEntities)
    };
  }

  /**
   * Preprocess text for better analysis
   */
  private preprocessText(input: string): string {
    return input
      .toLowerCase()
      .replace(/[^\w\s\/\.\-]/g, ' ') // Keep paths and extensions
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Extract semantic tokens with linguistic analysis
   */
  private extractSemanticTokens(text: string): SemanticToken[] {
    const tokens: SemanticToken[] = [];
    const words = text.split(/\s+/);
    let position = 0;

    for (const word of words) {
      if (this.stopWords.has(word)) {
        position += word.length + 1;
        continue;
      }

      const token: SemanticToken = {
        text: word,
        type: this.classifyTokenType(word),
        lemma: this.getLemma(word),
        partOfSpeech: this.getPartOfSpeech(word),
        position: [position, position + word.length]
      };

      // Check for named entities
      const namedEntity = this.extractNamedEntity(word);
      if (namedEntity) {
        token.namedEntity = namedEntity;
      }

      tokens.push(token);
      position += word.length + 1;
    }

    return tokens;
  }

  /**
   * Extract contextual entities with confidence scoring
   */
  private extractContextualEntities(text: string, tokens: SemanticToken[]): ContextualEntity[] {
    const entities: ContextualEntity[] = [];

    // Extract entities using multiple methods
    for (const [entityType, patterns] of this.entityExtractors.entries()) {
      for (const pattern of patterns) {
        const matches = text.matchAll(new RegExp(pattern.source, 'gi'));
        
        for (const match of matches) {
          if (match.index !== undefined) {
            const entity: ContextualEntity = {
              name: entityType,
              value: match[1] || match[0],
              type: entityType,
              confidence: this.calculateEntityConfidence(match[0], entityType, text),
              context: this.getEntityContext(text, match.index, match[0].length),
              position: [match.index, match.index + match[0].length]
            };
            entities.push(entity);
          }
        }
      }
    }

    // Extract entities from semantic tokens
    for (const token of tokens) {
      if (token.namedEntity) {
        const entityType = this.mapNamedEntityToType(token.namedEntity);
        if (entityType) {
          entities.push({
            name: token.namedEntity,
            value: token.text,
            type: entityType,
            confidence: 0.8,
            context: this.getTokenContext(text, token),
            position: token.position
          });
        }
      }
    }

    // Remove duplicates and sort by confidence
    return this.deduplicateEntities(entities);
  }

  /**
   * Classify intent using pattern matching and semantic analysis
   */
  private classifyIntent(text: string, tokens: SemanticToken[], entities: ContextualEntity[]): {
    intent: string;
    confidence: number;
    agent: string;
    multiAgent: boolean;
    reasoning: string;
  } {
    let bestMatch = {
      intent: 'general',
      confidence: 0.1,
      agent: 'developer',
      multiAgent: false,
      reasoning: 'Default classification'
    };

    // Check against intent patterns
    for (const pattern of this.intentPatterns) {
      const confidence = this.calculatePatternMatch(text, tokens, entities, pattern);
      
      if (confidence > bestMatch.confidence) {
        bestMatch = {
          intent: pattern.name,
          confidence,
          agent: pattern.agent,
          multiAgent: pattern.multiAgent,
          reasoning: `Matched pattern: ${pattern.name} (${Math.round(confidence * 100)}% confidence)`
        };
      }
    }

    // Boost confidence based on entity presence
    const entityBoost = this.calculateEntityBoost(entities, bestMatch.intent);
    bestMatch.confidence = Math.min(1.0, bestMatch.confidence + entityBoost);

    return bestMatch;
  }

  /**
   * Generate alternative interpretations
   */
  private generateAlternatives(text: string, tokens: SemanticToken[], entities: ContextualEntity[]): CommandAlternative[] {
    const alternatives: CommandAlternative[] = [];
    const scores: { [key: string]: number } = {};

    // Generate alternatives based on different patterns
    for (const pattern of this.intentPatterns) {
      const confidence = this.calculatePatternMatch(text, tokens, entities, pattern);
      
      if (confidence > 0.3) { // Only include decent matches
        const key = `${pattern.name}-${pattern.agent}`;
        if (!scores[key] || confidence > scores[key]) {
          scores[key] = confidence;
          
          alternatives.push({
            intent: pattern.name,
            confidence,
            suggestedAgent: pattern.agent,
            reasoning: this.generateReasoning(pattern, confidence, entities),
            entities: this.consolidateEntities(entities)
          });
        }
      }
    }

    // Sort by confidence and return top alternatives
    return alternatives
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3);
  }

  /**
   * Calculate ambiguity score (0 = clear, 1 = very ambiguous)
   */
  private calculateAmbiguityScore(primary: any, alternatives: CommandAlternative[]): number {
    if (alternatives.length === 0) return 0;
    
    const confidenceGap = primary.confidence - (alternatives[0]?.confidence || 0);
    const alternativeCount = alternatives.length;
    
    // Higher ambiguity if:
    // - Small confidence gap between top choices
    // - Many viable alternatives
    const gapFactor = Math.max(0, 1 - confidenceGap * 2);
    const countFactor = Math.min(1, alternativeCount / 3);
    
    return (gapFactor + countFactor) / 2;
  }

  /**
   * Generate helpful suggestions for unclear commands
   */
  private generateSuggestions(text: string, intent: any, ambiguityScore: number): string[] {
    const suggestions: string[] = [];

    if (ambiguityScore > 0.6) {
      suggestions.push("Your command is ambiguous. Try being more specific about what you want to do.");
      
      // Suggest based on missing entities
      const missingEntities = this.detectMissingEntities(text, intent.intent);
      for (const entity of missingEntities) {
        suggestions.push(`Consider specifying ${entity} for better accuracy.`);
      }
    }

    if (intent.confidence < 0.5) {
      suggestions.push("I'm not sure what you want to do. Try using these patterns:");
      suggestions.push(...this.getSimilarCommands(text));
    }

    return suggestions.slice(0, 5); // Limit suggestions
  }

  /**
   * Get similar commands based on partial matches
   */
  private getSimilarCommands(text: string): string[] {
    const similar: CommandSuggestion[] = [];
    
    for (const pattern of this.intentPatterns) {
      const similarity = this.calculateTextSimilarity(text, pattern.examples);
      if (similarity > 0.3) {
        similar.push({
          command: pattern.examples[0],
          description: `${pattern.name} (${pattern.agent} agent)`,
          confidence: similarity,
          reasoning: `Similar to: ${pattern.examples[0]}`,
          agent: pattern.agent
        });
      }
    }

    return similar
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3)
      .map(s => `"${s.command}" - ${s.description}`);
  }

  /**
   * Initialize intent patterns for classification
   */
  private initializeIntentPatterns(): void {
    this.intentPatterns = [
      // Scout patterns
      {
        name: 'check_duplicates',
        patterns: [
          /\b(check|find|detect|search)\s+.*\b(duplicate|similar|existing|reuse)/i,
          /\b(duplicate|similar)\s+.*\b(code|implementation|function)/i,
          /\bis\s+there\s+.*\b(already|existing|similar)/i
        ],
        keywords: ['duplicate', 'similar', 'existing', 'reuse', 'find'],
        requiredEntities: [],
        confidence: 0.9,
        agent: 'scout',
        multiAgent: false,
        examples: [
          "check for duplicate authentication code",
          "find similar implementations",
          "is there already a payment processor?"
        ]
      },

      // Architect patterns
      {
        name: 'design_architecture',
        patterns: [
          /\b(design|architect|create|build)\s+.*\b(system|architecture|structure)/i,
          /\bhow\s+to\s+.*\b(structure|organize|design)/i,
          /\b(microservice|api|database)\s+.*\b(design|architecture)/i
        ],
        keywords: ['design', 'architecture', 'structure', 'system', 'pattern'],
        requiredEntities: [EntityType.COMPONENT],
        confidence: 0.85,
        agent: 'architect',
        multiAgent: true,
        examples: [
          "design a microservices architecture",
          "how to structure the database",
          "create API design patterns"
        ]
      },

      // Developer patterns
      {
        name: 'implement_feature',
        patterns: [
          /\b(implement|create|build|code|develop)\s+.*\b(feature|function|component)/i,
          /\bwrite\s+.*\b(code|function|class|module)/i,
          /\b(add|create)\s+.*\b(to|in|for)/i
        ],
        keywords: ['implement', 'create', 'build', 'code', 'develop', 'write'],
        requiredEntities: [EntityType.ACTION],
        confidence: 0.8,
        agent: 'developer',
        multiAgent: false,
        examples: [
          "implement user authentication",
          "create a payment processing module",
          "build a REST API for users"
        ]
      },

      // Guardian patterns
      {
        name: 'security_scan',
        patterns: [
          /\b(scan|check|audit|validate)\s+.*\b(security|vulnerability|compliance)/i,
          /\bsecurity\s+.*\b(scan|check|audit|review)/i,
          /\b(secure|protect)\s+.*\b(against|from)/i
        ],
        keywords: ['security', 'scan', 'vulnerability', 'audit', 'compliance'],
        requiredEntities: [],
        confidence: 0.9,
        agent: 'guardian',
        multiAgent: false,
        examples: [
          "scan for security vulnerabilities",
          "check authentication security",
          "audit the payment module"
        ]
      },

      // QA patterns
      {
        name: 'create_tests',
        patterns: [
          /\b(test|write tests|create tests)\s+.*\b(for|of)/i,
          /\b(unit|integration|e2e)\s+.*\btests?\b/i,
          /\btest\s+.*\b(coverage|automation)/i
        ],
        keywords: ['test', 'testing', 'coverage', 'automation', 'quality'],
        requiredEntities: [EntityType.COMPONENT],
        confidence: 0.85,
        agent: 'qa',
        multiAgent: false,
        examples: [
          "create unit tests for authentication",
          "write integration tests",
          "test the payment API"
        ]
      },

      // Multi-agent patterns
      {
        name: 'complete_analysis',
        patterns: [
          /\b(analyze|review|evaluate|assess)\s+.*\b(completely|thoroughly|full)/i,
          /\b(complete|full|comprehensive)\s+.*\b(review|analysis)/i,
          /\bwhat.*\b(think|recommend|suggest)/i
        ],
        keywords: ['analyze', 'review', 'evaluate', 'complete', 'comprehensive'],
        requiredEntities: [],
        confidence: 0.7,
        agent: 'architect',
        multiAgent: true,
        examples: [
          "completely analyze the authentication system",
          "full review of the codebase",
          "what do you think about this architecture?"
        ]
      }
    ];
  }

  /**
   * Initialize entity extractors with regex patterns
   */
  private initializeEntityExtractors(): void {
    this.entityExtractors = new Map([
      [EntityType.FILE_PATH, [
        /\b([a-zA-Z0-9_\-\/]+\.[a-zA-Z0-9]+)\b/g,
        /\b(src\/[a-zA-Z0-9_\-\/]+)\b/g,
        /\b([a-zA-Z0-9_\-\/]+\/[a-zA-Z0-9_\-\/]+)\b/g
      ]],
      
      [EntityType.LANGUAGE, [
        /\b(javascript|typescript|python|java|go|rust|c\+\+|c#|php|ruby|kotlin|swift)\b/gi,
        /\b(js|ts|py|jsx|tsx)\b/gi
      ]],
      
      [EntityType.FRAMEWORK, [
        /\b(react|angular|vue|express|fastapi|django|spring|rails|laravel)\b/gi,
        /\b(node\.?js|next\.?js|nuxt\.?js)\b/gi
      ]],
      
      [EntityType.ACTION, [
        /\b(create|build|implement|develop|design|refactor|optimize|fix|delete|update|modify)\b/gi
      ]],
      
      [EntityType.COMPONENT, [
        /\b(api|database|service|controller|model|component|module|library|framework)\b/gi,
        /\b(authentication|auth|login|payment|user|admin|dashboard)\b/gi
      ]],
      
      [EntityType.TECHNOLOGY, [
        /\b(docker|kubernetes|microservice|serverless|cloud|aws|gcp|azure)\b/gi,
        /\b(rest|graphql|grpc|websocket|oauth|jwt|ssl|tls)\b/gi
      ]],
      
      [EntityType.PATTERN, [
        /\b(mvc|mvvm|singleton|factory|observer|strategy|decorator)\b/gi,
        /\b(repository|service|controller|facade|adapter)\b/gi
      ]],
      
      [EntityType.TIMEFRAME, [
        /\b(today|tomorrow|yesterday|week|month|quarter|sprint)\b/gi,
        /\b(\d+\s*(?:days?|weeks?|months?))\b/gi
      ]]
    ]);
  }

  /**
   * Initialize synonyms for better understanding
   */
  private initializeSynonyms(): void {
    this.synonyms = new Map([
      ['create', ['build', 'make', 'develop', 'implement', 'construct']],
      ['check', ['verify', 'validate', 'inspect', 'examine', 'review']],
      ['fix', ['repair', 'resolve', 'solve', 'correct', 'debug']],
      ['improve', ['enhance', 'optimize', 'upgrade', 'refactor', 'better']],
      ['security', ['secure', 'protection', 'safety', 'vulnerability']],
      ['test', ['testing', 'verify', 'validate', 'check', 'quality']]
    ]);
  }

  /**
   * Initialize stop words to filter out
   */
  private initializeStopWords(): void {
    this.stopWords = new Set([
      'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
      'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
      'to', 'was', 'will', 'with', 'can', 'could', 'should', 'would',
      'please', 'help', 'me', 'you', 'i', 'we', 'they', 'this', 'that'
    ]);
  }

  // Helper methods (simplified implementations)
  private classifyTokenType(word: string): TokenType {
    const verbPatterns = /\b(create|build|implement|check|scan|test|design|fix)\b/i;
    const nounPatterns = /\b(api|database|service|component|module|system|code)\b/i;
    
    if (verbPatterns.test(word)) return TokenType.VERB;
    if (nounPatterns.test(word)) return TokenType.NOUN;
    return TokenType.NOUN; // Default
  }

  private getLemma(word: string): string {
    // Simplified lemmatization
    const lemmas: { [key: string]: string } = {
      'implementing': 'implement',
      'creating': 'create',
      'building': 'build',
      'testing': 'test',
      'checking': 'check'
    };
    return lemmas[word] || word;
  }

  private getPartOfSpeech(word: string): string {
    // Simplified POS tagging
    if (this.classifyTokenType(word) === TokenType.VERB) return 'VERB';
    return 'NOUN';
  }

  private extractNamedEntity(word: string): string | undefined {
    // Simplified named entity recognition
    const technologies = ['react', 'node', 'python', 'javascript', 'docker'];
    return technologies.includes(word.toLowerCase()) ? 'TECHNOLOGY' : undefined;
  }

  private calculateEntityConfidence(match: string, type: EntityType, context: string): number {
    // Base confidence from match strength
    let confidence = 0.7;
    
    // Boost confidence based on context
    const contextWords = context.split(/\s+/);
    const relevantContext = this.getRelevantContextWords(type);
    
    for (const word of contextWords) {
      if (relevantContext.includes(word.toLowerCase())) {
        confidence += 0.1;
      }
    }
    
    return Math.min(1.0, confidence);
  }

  private getRelevantContextWords(type: EntityType): string[] {
    const contextMap: { [key in EntityType]: string[] } = {
      [EntityType.FILE_PATH]: ['file', 'path', 'src', 'directory'],
      [EntityType.LANGUAGE]: ['language', 'programming', 'code', 'written'],
      [EntityType.FRAMEWORK]: ['framework', 'library', 'using', 'built'],
      [EntityType.ACTION]: ['want', 'need', 'should', 'must'],
      [EntityType.TECHNOLOGY]: ['technology', 'tool', 'platform', 'service'],
      [EntityType.COMPONENT]: ['component', 'module', 'part', 'system'],
      [EntityType.PATTERN]: ['pattern', 'design', 'architecture', 'structure'],
      [EntityType.METRIC]: ['metric', 'measurement', 'performance', 'analytics'],
      [EntityType.TIMEFRAME]: ['time', 'deadline', 'schedule', 'when'],
      [EntityType.PERSON]: ['person', 'user', 'developer', 'team'],
      [EntityType.PROJECT]: ['project', 'application', 'system', 'codebase']
    };
    
    return contextMap[type] || [];
  }

  private getEntityContext(text: string, position: number, length: number): string {
    const start = Math.max(0, position - 20);
    const end = Math.min(text.length, position + length + 20);
    return text.substring(start, end);
  }

  private getTokenContext(text: string, token: SemanticToken): string {
    const [start, end] = token.position;
    const contextStart = Math.max(0, start - 20);
    const contextEnd = Math.min(text.length, end + 20);
    return text.substring(contextStart, contextEnd);
  }

  private mapNamedEntityToType(namedEntity: string): EntityType | undefined {
    const mapping: { [key: string]: EntityType } = {
      'TECHNOLOGY': EntityType.TECHNOLOGY,
      'LANGUAGE': EntityType.LANGUAGE,
      'FRAMEWORK': EntityType.FRAMEWORK
    };
    return mapping[namedEntity];
  }

  private deduplicateEntities(entities: ContextualEntity[]): ContextualEntity[] {
    const seen = new Set<string>();
    const deduplicated: ContextualEntity[] = [];
    
    // Sort by confidence descending
    const sorted = entities.sort((a, b) => b.confidence - a.confidence);
    
    for (const entity of sorted) {
      const key = `${entity.type}-${entity.value.toLowerCase()}`;
      if (!seen.has(key)) {
        seen.add(key);
        deduplicated.push(entity);
      }
    }
    
    return deduplicated;
  }

  private calculatePatternMatch(
    text: string, 
    tokens: SemanticToken[], 
    entities: ContextualEntity[], 
    pattern: IntentPattern
  ): number {
    let score = 0;
    
    // Check regex patterns
    for (const regex of pattern.patterns) {
      if (regex.test(text)) {
        score += 0.4;
        break;
      }
    }
    
    // Check keywords presence
    const keywordMatches = pattern.keywords.filter(keyword => 
      text.includes(keyword.toLowerCase())
    ).length;
    score += (keywordMatches / pattern.keywords.length) * 0.4;
    
    // Check required entities
    if (pattern.requiredEntities.length > 0) {
      const entityMatches = pattern.requiredEntities.filter(reqType =>
        entities.some(entity => entity.type === reqType)
      ).length;
      score += (entityMatches / pattern.requiredEntities.length) * 0.2;
    } else {
      score += 0.2; // No required entities = full score
    }
    
    return Math.min(1.0, score);
  }

  private calculateEntityBoost(entities: ContextualEntity[], intent: string): number {
    // Boost confidence based on high-confidence entities
    const highConfidenceEntities = entities.filter(e => e.confidence > 0.8);
    return Math.min(0.2, highConfidenceEntities.length * 0.05);
  }

  private generateReasoning(pattern: IntentPattern, confidence: number, entities: ContextualEntity[]): string {
    const reasons: string[] = [];
    
    reasons.push(`Pattern match: ${Math.round(confidence * 100)}%`);
    
    if (entities.length > 0) {
      const entityTypes = [...new Set(entities.map(e => e.type))];
      reasons.push(`Found entities: ${entityTypes.join(', ')}`);
    }
    
    if (pattern.multiAgent) {
      reasons.push('Requires multi-agent collaboration');
    }
    
    return reasons.join('; ');
  }

  private consolidateEntities(entities: ContextualEntity[]): Record<string, any> {
    const consolidated: Record<string, any> = {};
    
    for (const entity of entities) {
      const key = entity.type.toString();
      if (!consolidated[key]) {
        consolidated[key] = entity.value;
      } else if (Array.isArray(consolidated[key])) {
        consolidated[key].push(entity.value);
      } else {
        consolidated[key] = [consolidated[key], entity.value];
      }
    }
    
    return consolidated;
  }

  private createBaseCommand(input: string, intent: any): NLCommand {
    return {
      raw: input,
      intent: intent.intent,
      entities: {},
      confidence: intent.confidence,
      suggestedAgent: intent.agent,
      requiresMultiAgent: intent.multiAgent
    };
  }

  private updateContextHistory(input: string, context?: string[]): void {
    this.contextHistory.push(input);
    if (context) {
      this.contextHistory.push(...context);
    }
    
    // Keep only last 10 entries
    if (this.contextHistory.length > 10) {
      this.contextHistory = this.contextHistory.slice(-10);
    }
  }

  private detectMissingEntities(text: string, intent: string): string[] {
    const missing: string[] = [];
    
    // Check for common missing entities based on intent
    if (intent.includes('implement') && !text.includes('.')) {
      missing.push('a file path or component name');
    }
    
    if (intent.includes('test') && !text.includes('for')) {
      missing.push('what to test');
    }
    
    return missing;
  }

  private calculateTextSimilarity(text1: string, examples: string[]): number {
    let maxSimilarity = 0;
    
    for (const example of examples) {
      const similarity = this.calculateLevenshteinSimilarity(text1, example);
      maxSimilarity = Math.max(maxSimilarity, similarity);
    }
    
    return maxSimilarity;
  }

  private calculateLevenshteinSimilarity(str1: string, str2: string): number {
    const matrix: number[][] = [];
    const len1 = str1.length;
    const len2 = str2.length;
    
    for (let i = 0; i <= len1; i++) {
      matrix[i] = [i];
    }
    
    for (let j = 0; j <= len2; j++) {
      matrix[0][j] = j;
    }
    
    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        if (str1[i - 1] === str2[j - 1]) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j - 1] + 1
          );
        }
      }
    }
    
    const distance = matrix[len1][len2];
    const maxLength = Math.max(len1, len2);
    
    return maxLength === 0 ? 1 : 1 - (distance / maxLength);
  }

  /**
   * Get command suggestions for ambiguous input
   */
  getCommandSuggestions(input: string, limit: number = 5): CommandSuggestion[] {
    const suggestions: CommandSuggestion[] = [];
    
    for (const pattern of this.intentPatterns) {
      for (const example of pattern.examples) {
        const similarity = this.calculateLevenshteinSimilarity(input.toLowerCase(), example.toLowerCase());
        
        if (similarity > 0.3) {
          suggestions.push({
            command: example,
            description: `${pattern.name} using ${pattern.agent} agent`,
            confidence: similarity,
            reasoning: `Similar to your input (${Math.round(similarity * 100)}% match)`,
            agent: pattern.agent
          });
        }
      }
    }
    
    return suggestions
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, limit);
  }

  /**
   * Analyze command clarity and provide feedback
   */
  analyzeCommandClarity(command: EnhancedNLCommand): {
    clarity: 'clear' | 'unclear' | 'ambiguous';
    score: number;
    feedback: string[];
  } {
    const feedback: string[] = [];
    let score = command.confidence;
    
    if (command.ambiguityScore > 0.7) {
      feedback.push('Your command has multiple interpretations');
      score -= 0.2;
    }
    
    if (command.contextualEntities.length === 0) {
      feedback.push('Try to be more specific about what you want to work with');
      score -= 0.1;
    }
    
    if (command.semanticTokens.length < 3) {
      feedback.push('Your command is quite short - more detail would help');
      score -= 0.1;
    }
    
    const clarity = score > 0.7 ? 'clear' : score > 0.4 ? 'unclear' : 'ambiguous';
    
    return { clarity, score: Math.max(0, score), feedback };
  }
}

export default EnhancedNLPParser;