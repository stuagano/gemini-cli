/**
 * InteractiveMode Component - REPL-like interface with teaching capabilities
 * Provides progressive learning experience with context retention
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Box, Text, useInput } from 'ink';
import chalk from 'chalk';
import { useInteractiveMode, TeachingLevel, InteractiveCommand } from '../contexts/InteractiveModeContext.js';
import { Colors } from '../colors.js';

interface InteractiveModeProps {
  onExit: () => void;
}

export const InteractiveMode: React.FC<InteractiveModeProps> = ({ onExit }) => {
  const {
    state,
    startInteractiveMode,
    stopInteractiveMode,
    executeCommand,
    switchTeachingLevel,
    clearContext,
    saveSession,
  } = useInteractiveMode();

  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [displayCommands, setDisplayCommands] = useState<InteractiveCommand[]>([]);
  const [showTeachingMoments, setShowTeachingMoments] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const inputRef = useRef<string>('');
  inputRef.current = input;

  // Initialize interactive mode if not already active
  useEffect(() => {
    if (!state.isActive) {
      startInteractiveMode('junior'); // Default to junior level
    }
  }, [state.isActive, startInteractiveMode]);

  // Update display commands when session changes
  useEffect(() => {
    if (state.currentSession) {
      setDisplayCommands(state.currentSession.commands);
    }
  }, [state.currentSession]);

  // Handle input and command execution
  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const commandText = input.trim();
    setInput('');
    
    // Add to history
    setHistory(prev => [...prev, commandText]);
    setHistoryIndex(-1);
    
    // Handle special commands
    if (commandText.startsWith(':')) {
      handleSpecialCommand(commandText);
      return;
    }

    setIsLoading(true);
    try {
      const result = await executeCommand(commandText);
      setDisplayCommands(prev => [...prev, result]);
    } catch (error) {
      console.error('Command execution failed:', error);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, executeCommand]);

  // Handle special commands (REPL commands)
  const handleSpecialCommand = useCallback((command: string) => {
    const [cmd, ...args] = command.slice(1).split(' ');
    
    switch (cmd.toLowerCase()) {
      case 'help':
        setDisplayCommands(prev => [...prev, {
          id: `help_${Date.now()}`,
          timestamp: new Date(),
          input: command,
          output: getHelpText(),
          contextUsed: [],
          success: true,
        }]);
        break;
        
      case 'level':
        if (args.length > 0) {
          const newLevel = args[0].toLowerCase() as TeachingLevel;
          if (['junior', 'senior', 'architect'].includes(newLevel)) {
            switchTeachingLevel(newLevel);
            setDisplayCommands(prev => [...prev, {
              id: `level_${Date.now()}`,
              timestamp: new Date(),
              input: command,
              output: `Teaching level switched to: ${newLevel}`,
              contextUsed: [],
              success: true,
            }]);
          } else {
            setDisplayCommands(prev => [...prev, {
              id: `level_error_${Date.now()}`,
              timestamp: new Date(),
              input: command,
              output: 'Error: Invalid level. Use: junior, senior, or architect',
              contextUsed: [],
              success: false,
            }]);
          }
        } else {
          setDisplayCommands(prev => [...prev, {
            id: `level_current_${Date.now()}`,
            timestamp: new Date(),
            input: command,
            output: `Current teaching level: ${state.teachingLevel}`,
            contextUsed: [],
            success: true,
          }]);
        }
        break;
        
      case 'clear':
        setDisplayCommands([]);
        clearContext();
        break;
        
      case 'save':
        saveSession();
        setDisplayCommands(prev => [...prev, {
          id: `save_${Date.now()}`,
          timestamp: new Date(),
          input: command,
          output: 'Session saved successfully',
          contextUsed: [],
          success: true,
        }]);
        break;
        
      case 'teaching':
        if (args[0] === 'on') {
          setShowTeachingMoments(true);
          setDisplayCommands(prev => [...prev, {
            id: `teaching_on_${Date.now()}`,
            timestamp: new Date(),
            input: command,
            output: 'Teaching moments enabled',
            contextUsed: [],
            success: true,
          }]);
        } else if (args[0] === 'off') {
          setShowTeachingMoments(false);
          setDisplayCommands(prev => [...prev, {
            id: `teaching_off_${Date.now()}`,
            timestamp: new Date(),
            input: command,
            output: 'Teaching moments disabled',
            contextUsed: [],
            success: true,
          }]);
        } else {
          setDisplayCommands(prev => [...prev, {
            id: `teaching_status_${Date.now()}`,
            timestamp: new Date(),
            input: command,
            output: `Teaching moments: ${showTeachingMoments ? 'enabled' : 'disabled'}`,
            contextUsed: [],
            success: true,
          }]);
        }
        break;
        
      case 'exit':
      case 'quit':
        stopInteractiveMode();
        onExit();
        break;
        
      default:
        setDisplayCommands(prev => [...prev, {
          id: `unknown_${Date.now()}`,
          timestamp: new Date(),
          input: command,
          output: `Unknown command: ${cmd}. Type :help for available commands.`,
          contextUsed: [],
          success: false,
        }]);
    }
  }, [state.teachingLevel, switchTeachingLevel, clearContext, saveSession, stopInteractiveMode, onExit, showTeachingMoments]);

  // Handle keyboard input
  useInput((input, key) => {
    if (key.return) {
      handleSubmit();
    } else if (key.ctrl && input === 'c') {
      stopInteractiveMode();
      onExit();
    } else if (key.ctrl && input === 'd') {
      stopInteractiveMode();
      onExit();
    } else if (key.upArrow) {
      if (history.length > 0) {
        const newIndex = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setInput(history[newIndex]);
      }
    } else if (key.downArrow) {
      if (historyIndex >= 0) {
        const newIndex = historyIndex + 1;
        if (newIndex >= history.length) {
          setHistoryIndex(-1);
          setInput('');
        } else {
          setHistoryIndex(newIndex);
          setInput(history[newIndex]);
        }
      }
    } else if (key.backspace) {
      setInput(prev => prev.slice(0, -1));
    } else if (key.delete) {
      setInput('');
    } else if (input && !key.ctrl && !key.meta) {
      setInput(prev => prev + input);
    }
  });

  // Get help text for REPL commands
  const getHelpText = () => {
    return `
${chalk.blue.bold('Interactive Mode Help')}

${chalk.yellow('Special Commands:')}
  :help              - Show this help message
  :level [junior|senior|architect] - Set or show teaching level
  :clear             - Clear screen and context
  :save              - Save current session
  :teaching [on|off] - Enable/disable teaching moments
  :exit, :quit       - Exit interactive mode

${chalk.yellow('Teaching Levels:')}
  • junior     - Detailed explanations with examples
  • senior     - Quick validations and best practices  
  • architect  - Strategic discussions and trade-offs

${chalk.yellow('Features:')}
  • Context retention across commands
  • Progressive disclosure based on your level
  • Session history and replay
  • Command history (↑/↓ arrows)
  
${chalk.yellow('Shortcuts:')}
  Ctrl+C, Ctrl+D    - Exit interactive mode
  ↑/↓ arrows        - Browse command history
  Enter             - Execute command
`;
  };

  // Render teaching moment
  const renderTeachingMoment = (moment: NonNullable<InteractiveCommand['teachingMoment']>) => {
    const levelIcon = moment.level === 'junior' ? '📚' : 
                     moment.level === 'senior' ? '✓' : '🏗️';
    
    const levelColor = moment.level === 'junior' ? Colors.primary : 
                      moment.level === 'senior' ? Colors.success : Colors.warning;

    return (
      <Box flexDirection="column" marginLeft={2} marginTop={1} paddingX={2} 
           borderStyle="round" borderColor={levelColor}>
        <Text color={levelColor} bold>
          {levelIcon} Teaching Moment: {moment.concept}
        </Text>
        <Text wrap="wrap" color="gray">
          {moment.explanation}
        </Text>
        {moment.example && (
          <Box marginTop={1}>
            <Text color="cyan">Example: </Text>
            <Text color="gray">{moment.example}</Text>
          </Box>
        )}
        {moment.nextSteps && moment.nextSteps.length > 0 && (
          <Box marginTop={1} flexDirection="column">
            <Text color="magenta">Next steps:</Text>
            {moment.nextSteps.map((step, index) => (
              <Text key={index} color="gray">  • {step}</Text>
            ))}
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Box flexDirection="column" height="100%">
      {/* Header */}
      <Box borderStyle="single" borderColor="blue" paddingX={1}>
        <Text color="blue" bold>
          🎯 Interactive Mode - Level: {state.teachingLevel.toUpperCase()}
        </Text>
        <Text color="gray"> | Session: {state.currentSession?.id.slice(-8)}</Text>
        <Text color="gray"> | Commands: {displayCommands.length}</Text>
        <Text color="gray"> | Teaching: {showTeachingMoments ? 'ON' : 'OFF'}</Text>
      </Box>

      {/* Command History Display */}
      <Box flexDirection="column" flexGrow={1} overflow="hidden">
        {displayCommands.map((cmd, index) => (
          <Box key={cmd.id} flexDirection="column" marginY={1}>
            {/* Command Input */}
            <Box>
              <Text color="green" bold>
                [{cmd.timestamp.toLocaleTimeString()}] $ 
              </Text>
              <Text color="white"> {cmd.input}</Text>
            </Box>
            
            {/* Command Output */}
            <Box marginLeft={2}>
              <Text color={cmd.success ? "gray" : "red"}>
                {cmd.output}
              </Text>
            </Box>
            
            {/* Teaching Moment */}
            {cmd.teachingMoment && showTeachingMoments && renderTeachingMoment(cmd.teachingMoment)}
          </Box>
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <Box marginY={1}>
            <Text color="yellow">⏳ Processing command...</Text>
          </Box>
        )}
      </Box>

      {/* Input Prompt */}
      <Box borderStyle="single" borderColor="green" paddingX={1}>
        <Text color="green" bold>
          [{new Date().toLocaleTimeString()}] $ 
        </Text>
        <Text color="white">{input}</Text>
        <Text color="green">▌</Text>
      </Box>

      {/* Footer */}
      <Box borderStyle="single" borderColor="gray" paddingX={1}>
        <Text color="gray">
          Ctrl+C to exit | :help for commands | ↑/↓ for history | Current level: {state.teachingLevel}
        </Text>
      </Box>
    </Box>
  );
};

export default InteractiveMode;