/**
 * InteractiveModeContext Tests
 * Tests for interactive mode functionality and teaching engine integration
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { InteractiveModeProvider, useInteractiveMode, TeachingLevel } from './InteractiveModeContext.js';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock fetch for teaching engine API
global.fetch = vi.fn();

describe('InteractiveModeContext', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <InteractiveModeProvider>{children}</InteractiveModeProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue('[]');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      expect(result.current.state.isActive).toBe(false);
      expect(result.current.state.currentSession).toBe(null);
      expect(result.current.state.sessions).toEqual([]);
      expect(result.current.state.teachingLevel).toBe('junior');
      expect(result.current.state.contextRetention).toBe(true);
      expect(result.current.state.progressiveDisclosure).toBe(true);
    });
  });

  describe('Interactive Mode Management', () => {
    it('should start interactive mode with specified level', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('senior');
      });

      expect(result.current.state.isActive).toBe(true);
      expect(result.current.state.teachingLevel).toBe('senior');
      expect(result.current.state.currentSession).not.toBe(null);
      expect(result.current.state.currentSession?.teachingLevel).toBe('senior');
      expect(result.current.state.sessions).toHaveLength(1);
    });

    it('should stop interactive mode', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      // Start mode first
      act(() => {
        result.current.startInteractiveMode('junior');
      });

      expect(result.current.state.isActive).toBe(true);

      // Stop mode
      act(() => {
        result.current.stopInteractiveMode();
      });

      expect(result.current.state.isActive).toBe(false);
      expect(result.current.state.currentSession).toBe(null);
    });

    it('should switch teaching levels', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      expect(result.current.state.teachingLevel).toBe('junior');

      act(() => {
        result.current.switchTeachingLevel('architect');
      });

      expect(result.current.state.teachingLevel).toBe('architect');
      expect(result.current.state.currentSession?.teachingLevel).toBe('architect');
    });
  });

  describe('Command Execution', () => {
    it('should execute commands successfully', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      // Mock successful teaching engine response
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          explanation: 'Test explanation',
          example: 'Test example',
          nextSteps: ['Step 1', 'Step 2'],
        }),
      });

      let command;
      await act(async () => {
        command = await result.current.executeCommand('test command');
      });

      expect(command).toBeDefined();
      expect(command.input).toBe('test command');
      expect(command.success).toBe(true);
      expect(result.current.state.currentSession?.commands).toHaveLength(1);
    });

    it('should handle command execution errors gracefully', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      // Mock teaching engine failure
      (fetch as any).mockRejectedValueOnce(new Error('Network error'));

      let command;
      await act(async () => {
        command = await result.current.executeCommand('error command');
      });

      expect(command).toBeDefined();
      expect(command.input).toBe('error command');
      expect(command.success).toBe(false);
      expect(command.output).toContain('Error');
    });

    it('should throw error when no active session', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      await expect(async () => {
        await act(async () => {
          await result.current.executeCommand('test');
        });
      }).rejects.toThrow('No active interactive session');
    });
  });

  describe('Session Management', () => {
    it('should save session to localStorage', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      await act(async () => {
        await result.current.saveSession();
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'interactive_sessions',
        expect.stringContaining(result.current.state.currentSession!.id)
      );
    });

    it('should load session from localStorage', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      const mockSession = {
        id: 'test-session-123',
        startTime: new Date().toISOString(),
        teachingLevel: 'senior',
        commands: [],
        context: {
          variables: {},
          functions: {},
          imports: [],
          workingDirectory: '/test',
          projectContext: 'Test project',
          learningPath: [],
        },
        lastActivity: new Date().toISOString(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify([mockSession]));

      await act(async () => {
        await result.current.loadSession('test-session-123');
      });

      expect(result.current.state.isActive).toBe(true);
      expect(result.current.state.teachingLevel).toBe('senior');
      expect(result.current.state.currentSession?.id).toBe('test-session-123');
    });

    it('should replay existing session', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      // Create initial session
      act(() => {
        result.current.startInteractiveMode('junior');
      });

      const sessionId = result.current.state.currentSession!.id;

      // Stop session
      act(() => {
        result.current.stopInteractiveMode();
      });

      // Replay session
      act(() => {
        result.current.replaySession(sessionId);
      });

      expect(result.current.state.isActive).toBe(true);
      expect(result.current.state.currentSession?.id).toBe(sessionId);
    });

    it('should throw error for non-existent session replay', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      expect(() => {
        act(() => {
          result.current.replaySession('non-existent-id');
        });
      }).toThrow('Session non-existent-id not found');
    });
  });

  describe('Context Management', () => {
    it('should clear context', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      // Add some context
      act(() => {
        result.current.updateContext({
          variables: { test: 'value' },
          functions: { testFunc: 'definition' },
        });
      });

      expect(result.current.state.currentSession?.context.variables).toEqual({ test: 'value' });

      // Clear context
      act(() => {
        result.current.clearContext();
      });

      expect(result.current.state.currentSession?.context.variables).toEqual({});
      expect(result.current.state.currentSession?.context.functions).toEqual({});
    });

    it('should update context', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      const updates = {
        variables: { newVar: 'newValue' },
        imports: ['newImport'],
      };

      act(() => {
        result.current.updateContext(updates);
      });

      expect(result.current.state.currentSession?.context.variables).toEqual({ newVar: 'newValue' });
      expect(result.current.state.currentSession?.context.imports).toEqual(['newImport']);
    });
  });

  describe('Teaching Engine Integration', () => {
    it('should identify learning opportunities', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      // Mock teaching engine response
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          explanation: 'Function design is important...',
          example: 'function example() { }',
          nextSteps: ['Practice functions', 'Learn about parameters'],
          relatedConcepts: ['parameters', 'return values'],
        }),
      });

      let command;
      await act(async () => {
        command = await result.current.executeCommand('function test() { return true; }');
      });

      expect(command.teachingMoment).toBeDefined();
      expect(command.teachingMoment?.concept).toBe('function design patterns');
      expect(command.teachingMoment?.level).toBe('junior');
    });

    it('should handle offline mode gracefully', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      // Mock network failure
      (fetch as any).mockRejectedValueOnce(new Error('Network error'));

      let command;
      await act(async () => {
        command = await result.current.executeCommand('function test() {}');
      });

      expect(command.teachingMoment).toBeDefined();
      expect(command.teachingMoment?.explanation).toContain('Understanding function design patterns is important');
      expect(command.teachingMoment?.example).toBe('Example not available in offline mode.');
    });
  });

  describe('Progressive Disclosure', () => {
    it('should provide different content based on teaching level', () => {
      const levels: TeachingLevel[] = ['junior', 'senior', 'architect'];
      
      levels.forEach(level => {
        const { result } = renderHook(() => useInteractiveMode(), { wrapper });

        act(() => {
          result.current.startInteractiveMode(level);
        });

        expect(result.current.state.teachingLevel).toBe(level);
        expect(result.current.state.currentSession?.teachingLevel).toBe(level);
      });
    });
  });

  describe('Session History', () => {
    it('should return session history', () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      // Create multiple sessions
      act(() => {
        result.current.startInteractiveMode('junior');
      });

      const session1Id = result.current.state.currentSession!.id;

      act(() => {
        result.current.stopInteractiveMode();
        result.current.startInteractiveMode('senior');
      });

      const history = result.current.getSessionHistory();
      expect(history).toHaveLength(2);
      expect(history[0].id).toBe(session1Id);
      expect(history[1].teachingLevel).toBe('senior');
    });
  });

  describe('Error Handling', () => {
    it('should handle localStorage errors gracefully', async () => {
      const { result } = renderHook(() => useInteractiveMode(), { wrapper });

      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      act(() => {
        result.current.startInteractiveMode('junior');
      });

      await act(async () => {
        await result.current.saveSession();
      });

      expect(consoleSpy).toHaveBeenCalledWith('Failed to save session:', expect.any(Error));

      consoleSpy.mockRestore();
    });
  });
});