/**
 * Interactive Command - Start interactive mode with teaching capabilities
 * Provides REPL-like experience with progressive learning
 */

import { CommandKind, SlashCommand } from './types.js';
import { MessageType } from '../types.js';
import { SettingScope } from '../../config/settings.js';

export const interactiveCommand: SlashCommand = {
  name: 'interactive',
  altNames: ['i', 'repl', 'teach'],
  kind: CommandKind.BUILT_IN,
  description: 'Start interactive mode with teaching capabilities',
  
  action: async (context) => {
    // Add interactive mode item to history
    const interactiveItem = {
      type: MessageType.INTERACTIVE_MODE,
      timestamp: new Date(),
      teachingLevel: 'junior', // Default level
    };

    context.ui.addItem(interactiveItem, Date.now());
  },
};

// Teaching level command for switching levels in interactive mode
export const levelCommand: SlashCommand = {
  name: 'level',
  kind: CommandKind.BUILT_IN,
  description: 'Set teaching level for interactive mode',
  
  action: async (context, args) => {
    const levels = ['junior', 'senior', 'architect'];
    const level = args?.trim().toLowerCase();
    
    if (!level) {
      return {
        type: 'message',
        messageType: 'info',
        content: `Available teaching levels: ${levels.join(', ')}`,
      };
    }
    
    if (!levels.includes(level)) {
      return {
        type: 'message',
        messageType: 'error',
        content: `Invalid level. Available levels: ${levels.join(', ')}`,
      };
    }
    
    // Store level preference
    context.services.settings.updateSetting('interactive.teachingLevel', level, SettingScope.USER);
    
    return {
      type: 'message',
      messageType: 'info',
      content: `Teaching level set to: ${level}`,
    };
  },
};

export const interactiveCommands = [interactiveCommand, levelCommand];