#!/usr/bin/env node
/**
 * Gemini CLI Swarm Agent
 * Individual agent instance that can be spawned by the SwarmOrchestrator
 */

import { program } from 'commander';
import express from 'express';
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import { readFileSync } from 'fs';
import { join } from 'path';

interface AgentConfig {
    personaId: string;
    sessionId: string;
    agentId: string;
    port: number;
    workingDir: string;
    role: string;
    expertise: string[];
}

interface SwarmMessage {
    type: 'TASK' | 'COLLABORATION' | 'STATUS' | 'RESULT';
    from: string;
    to?: string;
    taskId?: string;
    content: any;
    timestamp: Date;
}

interface AgentCapability {
    name: string;
    description: string;
    handler: (input: any) => Promise<any>;
}

class SwarmAgent {
    private config: AgentConfig;
    private app: express.Application;
    private server: any;
    private wss: WebSocketServer;
    private peers: Map<string, any> = new Map();
    private capabilities: Map<string, AgentCapability> = new Map();
    private taskHistory: any[] = [];
    private isReady = false;

    constructor(config: AgentConfig) {
        this.config = config;
        this.app = express();
        this.setupExpress();
        this.registerCapabilities();
        
        console.log(`🤖 Swarm Agent ${config.agentId} initializing...`);
        console.log(`   Persona: ${config.personaId}`);
        console.log(`   Role: ${config.role}`);
        console.log(`   Port: ${config.port}`);
    }

    private setupExpress(): void {
        this.app.use(express.json());
        
        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                agent_id: this.config.agentId,
                persona: this.config.personaId,
                ready: this.isReady,
                tasks_completed: this.taskHistory.length
            });
        });

        // Task execution endpoint
        this.app.post('/execute', async (req, res) => {
            try {
                const { task_type, task_id, description, input } = req.body;
                
                console.log(`📋 Received task: ${task_type} (${task_id})`);
                
                const result = await this.executeTask(task_type, description, input);
                
                res.json({
                    success: true,
                    task_id,
                    result,
                    completed_at: new Date()
                });

                // Log completion for orchestrator
                console.log(`TASK_COMPLETED:${task_id}:${JSON.stringify(result)}`);
                
            } catch (error) {
                console.error(`❌ Task execution failed:`, error);
                console.log(`TASK_FAILED:${task_id}:${error}`);
                
                res.status(500).json({
                    success: false,
                    error: error instanceof Error ? error.message : String(error)
                });
            }
        });

        // Collaboration endpoint
        this.app.post('/collaborate', async (req, res) => {
            const { target_agent, message_type, content } = req.body;
            
            try {
                const result = await this.sendToPeer(target_agent, message_type, content);
                res.json({ success: true, result });
            } catch (error) {
                res.status(500).json({ success: false, error: error instanceof Error ? error.message : String(error) });
            }
        });

        // Status endpoint
        this.app.get('/status', (req, res) => {
            res.json({
                agent_id: this.config.agentId,
                persona: this.config.personaId,
                status: this.isReady ? 'ready' : 'initializing',
                capabilities: Array.from(this.capabilities.keys()),
                peers_connected: this.peers.size,
                tasks_completed: this.taskHistory.length,
                uptime: process.uptime()
            });
        });
    }

    private registerCapabilities(): void {
        // Register capabilities based on persona
        switch (this.config.personaId) {
            case 'architect':
                this.registerArchitectCapabilities();
                break;
            case 'scout':
                this.registerScoutCapabilities();
                break;
            case 'guardian':
                this.registerGuardianCapabilities();
                break;
            case 'optimizer':
                this.registerOptimizerCapabilities();
                break;
            case 'teacher':
                this.registerTeacherCapabilities();
                break;
            case 'project-manager':
                this.registerProjectManagerCapabilities();
                break;
            case 'security-expert':
                this.registerSecurityCapabilities();
                break;
            case 'devops-engineer':
                this.registerDevOpsCapabilities();
                break;
            default:
                this.registerGeneralCapabilities();
        }

        console.log(`📚 Registered ${this.capabilities.size} capabilities`);
    }

    private registerArchitectCapabilities(): void {
        this.capabilities.set('design-architecture', {
            name: 'Design Architecture',
            description: 'Design system architecture and patterns',
            handler: async (input) => {
                const { description, requirements } = input;
                
                // Simulate architecture design process
                return {
                    architecture: {
                        pattern: 'Microservices',
                        components: [
                            'API Gateway',
                            'Authentication Service',
                            'Business Logic Services',
                            'Data Layer'
                        ],
                        technologies: ['Node.js', 'Docker', 'Kubernetes', 'PostgreSQL'],
                        scalability: 'High',
                        maintainability: 'High'
                    },
                    recommendations: [
                        'Implement CQRS pattern for complex business logic',
                        'Use event sourcing for audit trail',
                        'Consider GraphQL for flexible API queries'
                    ],
                    estimated_complexity: 'Medium-High'
                };
            }
        });

        this.capabilities.set('review-architecture', {
            name: 'Review Architecture',
            description: 'Review existing architecture for improvements',
            handler: async (input) => {
                const { code, file_path } = input;
                
                return {
                    patterns_detected: ['MVC', 'Repository Pattern'],
                    issues: [
                        'Tight coupling between controller and data layer',
                        'Missing error handling middleware'
                    ],
                    improvements: [
                        'Introduce service layer',
                        'Add proper dependency injection',
                        'Implement circuit breaker pattern'
                    ],
                    score: 7.5
                };
            }
        });
    }

    private registerScoutCapabilities(): void {
        this.capabilities.set('detect-duplicates', {
            name: 'Detect Duplicates',
            description: 'Find duplicate code patterns and similarities',
            handler: async (input) => {
                const { workspace_path, threshold = 0.8 } = input;
                
                // Simulate duplicate detection
                return {
                    duplicates: [
                        {
                            similarity: 0.92,
                            files: ['src/utils/validation.js', 'src/helpers/validate.js'],
                            pattern: 'Email validation logic',
                            lines: [15, 23]
                        },
                        {
                            similarity: 0.85,
                            files: ['src/auth/login.js', 'src/auth/register.js'],
                            pattern: 'Password hashing',
                            lines: [45, 67]
                        }
                    ],
                    total_files_scanned: 156,
                    analysis_time_ms: 2340
                };
            }
        });

        this.capabilities.set('quality-check', {
            name: 'Quality Check',
            description: 'Analyze code quality and technical debt',
            handler: async (input) => {
                const { code, file_path } = input;
                
                return {
                    quality_score: 8.2,
                    issues: [
                        {
                            type: 'complexity',
                            message: 'Function too complex',
                            line: 45,
                            severity: 'warning'
                        },
                        {
                            type: 'naming',
                            message: 'Variable name too short',
                            line: 12,
                            severity: 'info'
                        }
                    ],
                    suggestions: [
                        'Break down large functions',
                        'Use more descriptive variable names',
                        'Add JSDoc comments'
                    ]
                };
            }
        });
    }

    private registerGuardianCapabilities(): void {
        this.capabilities.set('security-scan', {
            name: 'Security Scan',
            description: 'Scan for security vulnerabilities',
            handler: async (input) => {
                const { code, file_path } = input;
                
                return {
                    vulnerabilities: [
                        {
                            type: 'SQL Injection',
                            severity: 'high',
                            line: 78,
                            description: 'Unsanitized user input in SQL query',
                            fix: 'Use parameterized queries'
                        },
                        {
                            type: 'XSS',
                            severity: 'medium',
                            line: 123,
                            description: 'Unescaped user content in HTML',
                            fix: 'Use proper HTML escaping'
                        }
                    ],
                    security_score: 6.5,
                    compliance: {
                        'OWASP Top 10': 'Partial',
                        'CWE Standards': 'Good'
                    }
                };
            }
        });

        this.capabilities.set('validate-code', {
            name: 'Validate Code',
            description: 'Comprehensive code validation',
            handler: async (input) => {
                const { code, rules } = input;
                
                return {
                    validation_passed: false,
                    errors: 2,
                    warnings: 5,
                    issues: [
                        {
                            rule: 'no-unused-vars',
                            message: 'Variable "temp" is defined but never used',
                            line: 34,
                            severity: 'error'
                        }
                    ],
                    auto_fixable: 3
                };
            }
        });
    }

    private registerOptimizerCapabilities(): void {
        this.capabilities.set('performance-analysis', {
            name: 'Performance Analysis',
            description: 'Analyze code performance bottlenecks',
            handler: async (input) => {
                const { code, file_path } = input;
                
                return {
                    performance_score: 7.8,
                    bottlenecks: [
                        {
                            type: 'N+1 Query',
                            location: 'getUserPosts function',
                            impact: 'high',
                            solution: 'Use eager loading or batch queries'
                        },
                        {
                            type: 'Memory Leak',
                            location: 'Event listener cleanup',
                            impact: 'medium',
                            solution: 'Remove event listeners in cleanup'
                        }
                    ],
                    optimizations: [
                        'Add database indexing',
                        'Implement caching strategy',
                        'Use connection pooling'
                    ]
                };
            }
        });
    }

    private registerTeacherCapabilities(): void {
        this.capabilities.set('explain-concept', {
            name: 'Explain Concept',
            description: 'Provide educational explanations',
            handler: async (input) => {
                const { concept, skill_level, learning_style } = input;
                
                return {
                    explanation: `Understanding ${concept} at ${skill_level} level...`,
                    examples: [
                        'Basic example with simple code',
                        'Intermediate example with real-world scenario'
                    ],
                    resources: [
                        'Documentation link',
                        'Tutorial recommendations'
                    ],
                    next_steps: [
                        'Practice exercises',
                        'Advanced topics to explore'
                    ]
                };
            }
        });
    }

    private registerProjectManagerCapabilities(): void {
        this.capabilities.set('task-planning', {
            name: 'Task Planning',
            description: 'Break down and plan development tasks',
            handler: async (input) => {
                const { project_description, timeline } = input;
                
                return {
                    tasks: [
                        {
                            name: 'Requirements Analysis',
                            duration: '2 days',
                            dependencies: [],
                            assignee: 'architect'
                        },
                        {
                            name: 'Database Design',
                            duration: '3 days',
                            dependencies: ['Requirements Analysis'],
                            assignee: 'architect'
                        },
                        {
                            name: 'API Development',
                            duration: '5 days',
                            dependencies: ['Database Design'],
                            assignee: 'developer'
                        }
                    ],
                    estimated_total: '10 days',
                    critical_path: ['Requirements Analysis', 'Database Design', 'API Development']
                };
            }
        });
    }

    private registerSecurityCapabilities(): void {
        this.capabilities.set('penetration-test', {
            name: 'Penetration Test',
            description: 'Simulate security attacks',
            handler: async (input) => {
                return {
                    test_results: [
                        {
                            attack_vector: 'SQL Injection',
                            result: 'Vulnerable',
                            evidence: 'Successfully extracted database schema'
                        },
                        {
                            attack_vector: 'XSS',
                            result: 'Protected',
                            evidence: 'Input properly sanitized'
                        }
                    ],
                    overall_security: 'Moderate Risk'
                };
            }
        });
    }

    private registerDevOpsCapabilities(): void {
        this.capabilities.set('deployment-analysis', {
            name: 'Deployment Analysis',
            description: 'Analyze deployment configuration',
            handler: async (input) => {
                return {
                    deployment_health: 'Good',
                    issues: [
                        'Missing health checks in some services',
                        'Resource limits not set for containers'
                    ],
                    recommendations: [
                        'Add Kubernetes health probes',
                        'Implement proper resource quotas',
                        'Set up monitoring and alerting'
                    ]
                };
            }
        });
    }

    private registerGeneralCapabilities(): void {
        this.capabilities.set('analyze', {
            name: 'General Analysis',
            description: 'General code analysis',
            handler: async (input) => {
                return {
                    analysis: `General analysis completed for ${input.description || 'provided input'}`,
                    timestamp: new Date(),
                    agent: this.config.agentId
                };
            }
        });
    }

    private async executeTask(taskType: string, description: string, input: any): Promise<any> {
        console.log(`⚙️ Executing ${taskType}: ${description}`);
        
        const capability = this.capabilities.get(taskType) || this.capabilities.get('analyze');
        
        if (!capability) {
            throw new Error(`Capability '${taskType}' not found`);
        }

        const startTime = Date.now();
        
        try {
            const result = await capability.handler(input);
            
            const executionTime = Date.now() - startTime;
            
            // Record task in history
            this.taskHistory.push({
                task_type: taskType,
                description,
                execution_time_ms: executionTime,
                completed_at: new Date(),
                success: true
            });

            console.log(`✅ Task completed in ${executionTime}ms`);
            
            return {
                ...result,
                execution_time_ms: executionTime,
                agent_id: this.config.agentId,
                persona: this.config.personaId
            };
            
        } catch (error) {
            const executionTime = Date.now() - startTime;
            
            this.taskHistory.push({
                task_type: taskType,
                description,
                execution_time_ms: executionTime,
                completed_at: new Date(),
                success: false,
                error: error instanceof Error ? error.message : String(error)
            });
            
            throw error;
        }
    }

    private async sendToPeer(targetAgent: string, messageType: string, content: any): Promise<any> {
        const peer = this.peers.get(targetAgent);
        
        if (!peer) {
            throw new Error(`Peer agent '${targetAgent}' not found`);
        }

        const message: SwarmMessage = {
            type: messageType as any,
            from: this.config.agentId,
            to: targetAgent,
            content,
            timestamp: new Date()
        };

        // Send via WebSocket if connected
        if (peer.ws && peer.ws.readyState === 1) {
            peer.ws.send(JSON.stringify(message));
            return { sent: true, method: 'websocket' };
        }

        // Fallback to HTTP
        try {
            const response = await fetch(`http://localhost:${peer.port}/collaborate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from_agent: this.config.agentId,
                    message_type: messageType,
                    content
                })
            });

            return await response.json();
        } catch (error) {
            throw new Error(`Failed to communicate with peer: ${error}`);
        }
    }

    async start(): Promise<void> {
        return new Promise((resolve) => {
            this.server = createServer(this.app);
            this.wss = new WebSocketServer({ server: this.server });

            this.setupWebSocket();

            this.server.listen(this.config.port, () => {
                this.isReady = true;
                console.log(`AGENT_READY`);
                console.log(`🟢 Agent listening on port ${this.config.port}`);
                resolve();
            });
        });
    }

    private setupWebSocket(): void {
        this.wss.on('connection', (ws) => {
            console.log('🔌 WebSocket connection established');

            ws.on('message', (data) => {
                try {
                    const message: SwarmMessage = JSON.parse(data.toString());
                    this.handleSwarmMessage(message, ws);
                } catch (error) {
                    console.error('Error parsing swarm message:', error);
                }
            });

            ws.on('close', () => {
                console.log('🔌 WebSocket connection closed');
            });
        });
    }

    private handleSwarmMessage(message: SwarmMessage, ws: any): void {
        console.log(`📨 Received swarm message: ${message.type} from ${message.from}`);

        switch (message.type) {
            case 'TASK':
                this.handleSwarmTask(message, ws);
                break;
            case 'COLLABORATION':
                this.handleCollaboration(message, ws);
                break;
            case 'STATUS':
                this.handleStatusRequest(message, ws);
                break;
        }
    }

    private async handleSwarmTask(message: SwarmMessage, ws: any): Promise<void> {
        try {
            const { task_type, description, input } = message.content;
            const result = await this.executeTask(task_type, description, input);

            ws.send(JSON.stringify({
                type: 'RESULT',
                from: this.config.agentId,
                to: message.from,
                taskId: message.taskId,
                content: { success: true, result },
                timestamp: new Date()
            }));

        } catch (error) {
            ws.send(JSON.stringify({
                type: 'RESULT',
                from: this.config.agentId,
                to: message.from,
                taskId: message.taskId,
                content: { success: false, error: error instanceof Error ? error.message : String(error) },
                timestamp: new Date()
            }));
        }
    }

    private handleCollaboration(message: SwarmMessage, ws: any): void {
        // Handle collaboration requests from other agents
        console.log(`🤝 Collaboration request: ${JSON.stringify(message.content)}`);
        
        // Echo back for now
        ws.send(JSON.stringify({
            type: 'RESULT',
            from: this.config.agentId,
            to: message.from,
            content: { 
                message: `Collaboration acknowledged by ${this.config.personaId}`,
                original_request: message.content
            },
            timestamp: new Date()
        }));
    }

    private handleStatusRequest(message: SwarmMessage, ws: any): void {
        ws.send(JSON.stringify({
            type: 'RESULT',
            from: this.config.agentId,
            to: message.from,
            content: {
                agent_id: this.config.agentId,
                persona: this.config.personaId,
                status: this.isReady ? 'ready' : 'initializing',
                capabilities: Array.from(this.capabilities.keys()),
                tasks_completed: this.taskHistory.length
            },
            timestamp: new Date()
        }));
    }

    initializePeers(peers: any[]): void {
        peers.forEach(peer => {
            this.peers.set(peer.id, {
                id: peer.id,
                persona: peer.persona,
                port: peer.port,
                ws: null
            });
        });

        console.log(`🔗 Initialized ${peers.length} peer connections`);
    }

    stop(): void {
        if (this.server) {
            this.server.close();
        }
        if (this.wss) {
            this.wss.close();
        }
        console.log(`🔴 Agent ${this.config.agentId} stopped`);
    }
}

// CLI setup
program
    .version('1.0.0')
    .description('Gemini CLI Swarm Agent')
    .option('--persona <id>', 'Persona ID')
    .option('--session-id <id>', 'Session ID')
    .option('--agent-id <id>', 'Agent ID')
    .option('--port <number>', 'Port number', '8100')
    .option('--working-dir <path>', 'Working directory', process.cwd())
    .option('--role <role>', 'Agent role', 'General Agent')
    .option('--expertise <list>', 'Comma-separated expertise list', '');

program.parse();

const options = program.opts();

if (!options.persona || !options.sessionId || !options.agentId) {
    console.error('Missing required options: --persona, --session-id, --agent-id');
    process.exit(1);
}

const config: AgentConfig = {
    personaId: options.persona,
    sessionId: options.sessionId,
    agentId: options.agentId,
    port: parseInt(options.port),
    workingDir: options.workingDir,
    role: options.role,
    expertise: options.expertise.split(',').filter((s: string) => s.trim())
};

const agent = new SwarmAgent(config);

// Handle STDIN for orchestrator commands
process.stdin.setEncoding('utf8');
process.stdin.on('readable', () => {
    const chunk = process.stdin.read();
    if (chunk !== null) {
        try {
            const command = JSON.parse(chunk.trim());
            
            switch (command.type) {
                case 'INIT_COMMUNICATION':
                    agent.initializePeers(command.peers);
                    break;
                case 'EXECUTE_TASK':
                    // This will be handled via HTTP/WebSocket
                    break;
            }
        } catch (error) {
            // Ignore non-JSON input
        }
    }
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Received SIGTERM, shutting down gracefully...');
    agent.stop();
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('🛑 Received SIGINT, shutting down gracefully...');
    agent.stop();
    process.exit(0);
});

// Start the agent
agent.start().catch(error => {
    console.error('Failed to start agent:', error);
    process.exit(1);
});