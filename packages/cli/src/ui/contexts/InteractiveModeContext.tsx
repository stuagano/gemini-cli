/**
 * InteractiveMode Context - Manages interactive CLI mode with teaching capabilities
 * Provides REPL-like experience with context retention and progressive disclosure
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useState,
  useMemo,
  useEffect,
} from 'react';

// --- Interface Definitions ---

export type TeachingLevel = 'junior' | 'senior' | 'architect';

export interface InteractiveSession {
  id: string;
  startTime: Date;
  teachingLevel: TeachingLevel;
  commands: InteractiveCommand[];
  context: SessionContext;
  lastActivity: Date;
}

export interface InteractiveCommand {
  id: string;
  timestamp: Date;
  input: string;
  output: string;
  teachingMoment?: TeachingMoment;
  contextUsed: string[];
  success: boolean;
}

export interface TeachingMoment {
  concept: string;
  level: TeachingLevel;
  explanation: string;
  example?: string;
  nextSteps?: string[];
  relatedConcepts?: string[];
}

export interface SessionContext {
  variables: Record<string, any>;
  functions: Record<string, any>;
  imports: string[];
  workingDirectory: string;
  projectContext: string;
  learningPath: string[];
}

export interface InteractiveModeState {
  isActive: boolean;
  currentSession: InteractiveSession | null;
  sessions: InteractiveSession[];
  teachingLevel: TeachingLevel;
  contextRetention: boolean;
  progressiveDisclosure: boolean;
}

// --- Teaching Engine Interface ---

export interface TeachingEngineAPI {
  teach(concept: string, context: Record<string, any>): Promise<TeachingMoment>;
  suggestNextSteps(history: InteractiveCommand[]): Promise<string[]>;
  identifyLearningOpportunities(command: string): Promise<string[]>;
  validateProgress(session: InteractiveSession): Promise<number>; // 0-100 score
}

// Defines the context value including state and functions
interface InteractiveModeContextValue {
  state: InteractiveModeState;
  startInteractiveMode: (level: TeachingLevel) => void;
  stopInteractiveMode: () => void;
  executeCommand: (command: string) => Promise<InteractiveCommand>;
  replaySession: (sessionId: string) => void;
  switchTeachingLevel: (level: TeachingLevel) => void;
  saveSession: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  getSessionHistory: () => InteractiveSession[];
  clearContext: () => void;
  updateContext: (updates: Partial<SessionContext>) => void;
}

// --- Context Definition ---

const InteractiveModeContext = createContext<InteractiveModeContextValue | undefined>(
  undefined,
);

// --- Provider Component ---

export const InteractiveModeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, setState] = useState<InteractiveModeState>({
    isActive: false,
    currentSession: null,
    sessions: [],
    teachingLevel: 'junior',
    contextRetention: true,
    progressiveDisclosure: true,
  });

  // Teaching Engine API - connects to Python agent server
  const teachingEngine: TeachingEngineAPI = useMemo(() => ({
    async teach(concept: string, context: Record<string, any>): Promise<TeachingMoment> {
      try {
        // Call Python TeachingEngine via agent server
        const response = await fetch('/api/teaching/teach', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            concept,
            context,
            level: state.teachingLevel
          }),
        });
        
        if (!response.ok) {
          throw new Error('Teaching engine request failed');
        }
        
        const data = await response.json();
        return {
          concept,
          level: state.teachingLevel,
          explanation: data.explanation,
          example: data.example,
          nextSteps: data.nextSteps,
          relatedConcepts: data.relatedConcepts,
        };
      } catch (error) {
        // Fallback teaching moment
        return {
          concept,
          level: state.teachingLevel,
          explanation: `Understanding ${concept} is important for your development.`,
          example: 'Example not available in offline mode.',
          nextSteps: ['Continue practicing', 'Ask for help when needed'],
        };
      }
    },

    async suggestNextSteps(history: InteractiveCommand[]): Promise<string[]> {
      try {
        const response = await fetch('/api/teaching/suggest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            history: history.slice(-5), // Last 5 commands
            level: state.teachingLevel
          }),
        });
        
        if (!response.ok) throw new Error('Suggestion request failed');
        
        const data = await response.json();
        return data.suggestions || [];
      } catch (error) {
        return ['Try exploring related concepts', 'Practice with examples'];
      }
    },

    async identifyLearningOpportunities(command: string): Promise<string[]> {
      const opportunities: string[] = [];
      
      // Basic pattern matching for learning opportunities
      if (command.includes('function') || command.includes('def ')) {
        opportunities.push('function design patterns');
      }
      if (command.includes('class ')) {
        opportunities.push('object-oriented programming');
      }
      if (command.includes('async') || command.includes('await')) {
        opportunities.push('asynchronous programming');
      }
      if (command.includes('test') || command.includes('spec')) {
        opportunities.push('testing strategies');
      }
      
      return opportunities;
    },

    async validateProgress(session: InteractiveSession): Promise<number> {
      const commandCount = session.commands.length;
      const successRate = session.commands.filter(c => c.success).length / commandCount;
      const conceptsCovered = new Set(
        session.commands.flatMap(c => c.teachingMoment?.relatedConcepts || [])
      ).size;
      
      // Simple scoring algorithm
      return Math.min(100, (successRate * 50) + (conceptsCovered * 5) + (commandCount * 2));
    },
  }), [state.teachingLevel]);

  // Create new session
  const createNewSession = useCallback((level: TeachingLevel): InteractiveSession => {
    return {
      id: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      startTime: new Date(),
      teachingLevel: level,
      commands: [],
      context: {
        variables: {},
        functions: {},
        imports: [],
        workingDirectory: process.cwd(),
        projectContext: 'Interactive session',
        learningPath: [],
      },
      lastActivity: new Date(),
    };
  }, []);

  // Start interactive mode
  const startInteractiveMode = useCallback((level: TeachingLevel) => {
    const newSession = createNewSession(level);
    setState(prev => ({
      ...prev,
      isActive: true,
      currentSession: newSession,
      teachingLevel: level,
      sessions: [...prev.sessions, newSession],
    }));
  }, [createNewSession]);

  // Stop interactive mode
  const stopInteractiveMode = useCallback(() => {
    setState(prev => ({
      ...prev,
      isActive: false,
      currentSession: null,
    }));
  }, []);

  // Execute command in interactive mode
  const executeCommand = useCallback(async (command: string): Promise<InteractiveCommand> => {
    if (!state.currentSession) {
      throw new Error('No active interactive session');
    }

    const commandId = `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    const timestamp = new Date();

    try {
      // Identify learning opportunities
      const opportunities = await teachingEngine.identifyLearningOpportunities(command);
      
      // Generate teaching moment if opportunities found
      let teachingMoment: TeachingMoment | undefined;
      if (opportunities.length > 0 && state.progressiveDisclosure) {
        teachingMoment = await teachingEngine.teach(opportunities[0], {
          command,
          session: state.currentSession,
          level: state.teachingLevel
        });
      }

      // Simulate command execution (in real implementation, this would call the agent server)
      const output = await simulateCommandExecution(command, state.currentSession.context);
      
      const interactiveCommand: InteractiveCommand = {
        id: commandId,
        timestamp,
        input: command,
        output,
        teachingMoment,
        contextUsed: Object.keys(state.currentSession.context.variables),
        success: !output.includes('Error'),
      };

      // Update session
      setState(prev => ({
        ...prev,
        currentSession: prev.currentSession ? {
          ...prev.currentSession,
          commands: [...prev.currentSession.commands, interactiveCommand],
          lastActivity: timestamp,
        } : null,
      }));

      return interactiveCommand;

    } catch (error) {
      const errorCommand: InteractiveCommand = {
        id: commandId,
        timestamp,
        input: command,
        output: `Error: ${error}`,
        contextUsed: [],
        success: false,
      };

      setState(prev => ({
        ...prev,
        currentSession: prev.currentSession ? {
          ...prev.currentSession,
          commands: [...prev.currentSession.commands, errorCommand],
          lastActivity: timestamp,
        } : null,
      }));

      return errorCommand;
    }
  }, [state, teachingEngine]);

  // Replay session
  const replaySession = useCallback((sessionId: string) => {
    const session = state.sessions.find(s => s.id === sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }

    setState(prev => ({
      ...prev,
      currentSession: { ...session },
      isActive: true,
      teachingLevel: session.teachingLevel,
    }));
  }, [state.sessions]);

  // Switch teaching level
  const switchTeachingLevel = useCallback((level: TeachingLevel) => {
    setState(prev => ({
      ...prev,
      teachingLevel: level,
      currentSession: prev.currentSession ? {
        ...prev.currentSession,
        teachingLevel: level,
      } : null,
    }));
  }, []);

  // Save session to localStorage
  const saveSession = useCallback(async () => {
    if (!state.currentSession) return;

    try {
      const savedSessions = JSON.parse(localStorage.getItem('interactive_sessions') || '[]');
      const existingIndex = savedSessions.findIndex((s: InteractiveSession) => s.id === state.currentSession!.id);
      
      if (existingIndex >= 0) {
        savedSessions[existingIndex] = state.currentSession;
      } else {
        savedSessions.push(state.currentSession);
      }
      
      localStorage.setItem('interactive_sessions', JSON.stringify(savedSessions));
    } catch (error) {
      console.warn('Failed to save session:', error);
    }
  }, [state.currentSession]);

  // Load session from localStorage
  const loadSession = useCallback(async (sessionId: string) => {
    try {
      const savedSessions = JSON.parse(localStorage.getItem('interactive_sessions') || '[]');
      const session = savedSessions.find((s: InteractiveSession) => s.id === sessionId);
      
      if (session) {
        setState(prev => ({
          ...prev,
          sessions: savedSessions,
          currentSession: session,
          isActive: true,
          teachingLevel: session.teachingLevel,
        }));
      }
    } catch (error) {
      console.warn('Failed to load session:', error);
    }
  }, []);

  // Get session history
  const getSessionHistory = useCallback(() => {
    return state.sessions;
  }, [state.sessions]);

  // Clear context
  const clearContext = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentSession: prev.currentSession ? {
        ...prev.currentSession,
        context: {
          ...prev.currentSession.context,
          variables: {},
          functions: {},
          imports: [],
          learningPath: [],
        },
      } : null,
    }));
  }, []);

  // Update context
  const updateContext = useCallback((updates: Partial<SessionContext>) => {
    setState(prev => ({
      ...prev,
      currentSession: prev.currentSession ? {
        ...prev.currentSession,
        context: {
          ...prev.currentSession.context,
          ...updates,
        },
      } : null,
    }));
  }, []);

  // Auto-save session on changes
  useEffect(() => {
    if (state.currentSession && state.currentSession.commands.length > 0) {
      const timeoutId = setTimeout(() => {
        saveSession();
      }, 5000); // Auto-save after 5 seconds of inactivity

      return () => clearTimeout(timeoutId);
    }
  }, [state.currentSession, saveSession]);

  const value = useMemo(
    () => ({
      state,
      startInteractiveMode,
      stopInteractiveMode,
      executeCommand,
      replaySession,
      switchTeachingLevel,
      saveSession,
      loadSession,
      getSessionHistory,
      clearContext,
      updateContext,
    }),
    [
      state,
      startInteractiveMode,
      stopInteractiveMode,
      executeCommand,
      replaySession,
      switchTeachingLevel,
      saveSession,
      loadSession,
      getSessionHistory,
      clearContext,
      updateContext,
    ],
  );

  return (
    <InteractiveModeContext.Provider value={value}>
      {children}
    </InteractiveModeContext.Provider>
  );
};

// --- Consumer Hook ---

export const useInteractiveMode = () => {
  const context = useContext(InteractiveModeContext);
  if (context === undefined) {
    throw new Error(
      'useInteractiveMode must be used within an InteractiveModeProvider',
    );
  }
  return context;
};

// --- Helper Functions ---

/**
 * Simulate command execution (placeholder for actual agent integration)
 */
async function simulateCommandExecution(command: string, context: SessionContext): Promise<string> {
  // This would be replaced with actual agent server calls
  await new Promise(resolve => setTimeout(resolve, 100)); // Simulate processing time
  
  if (command.startsWith('/')) {
    return `Executed command: ${command}`;
  } else if (command.includes('=')) {
    const [variable, value] = command.split('=').map(s => s.trim());
    return `Set ${variable} = ${value}`;
  } else if (command.toLowerCase().includes('error')) {
    return 'Error: Something went wrong';
  } else {
    return `Processed: ${command}\nResult: Success`;
  }
}

export default InteractiveModeContext;