/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SlashCommand, CommandKind } from './types.js';
import { CommandContext } from '../contexts/commandContext.js';
import {
  LoadedSettings,
  loadSettings,
  SettingScope,
  USER_SETTINGS_PATH,
} from '../../config/settings.js';
import { SETTINGS_SCHEMA } from '../../config/settingsSchema.js';
import * as path from 'path';
import * as fs from 'fs';

async function getConfig(
  context: CommandContext,
  key: string,
): Promise<void> {
  const settings = loadSettings(process.cwd());
  const value = settings.merged[key as keyof typeof settings.merged];

  if (value !== undefined) {
    context.print(`Value for "${key}": ${JSON.stringify(value, null, 2)}`);
  } else {
    context.print(`Configuration key "${key}" not found.`);
  }
}

async function setConfig(
  context: CommandContext,
  key: string,
  value: string,
): Promise<void> {
  const settings = loadSettings(process.cwd());
  const settingDefinition = SETTINGS_SCHEMA[key];

  if (!settingDefinition) {
    context.printError(`Unknown configuration key: "${key}".`);
    return;
  }

  let parsedValue: unknown;
  try {
    switch (settingDefinition.type) {
      case 'boolean':
        parsedValue = value.toLowerCase() === 'true';
        break;
      case 'number':
        parsedValue = parseFloat(value);
        if (isNaN(parsedValue)) {
          throw new Error(`Invalid number value for "${key}": "${value}"`);
        }
        break;
      case 'array':
        parsedValue = JSON.parse(value);
        if (!Array.isArray(parsedValue)) {
          throw new Error(`Invalid array value for "${key}": "${value}"`);
        }
        break;
      case 'object':
        parsedValue = JSON.parse(value);
        if (typeof parsedValue !== 'object' || parsedValue === null) {
          throw new Error(`Invalid object value for "${key}": "${value}"`);
        }
        break;
      case 'string':
      default:
        parsedValue = value;
        break;
    }
  } catch (e) {
    context.printError(`Error parsing value for "${key}": ${e instanceof Error ? e.message : String(e)}`);
    return;
  }

  settings.setValue(SettingScope.User, key as keyof Settings, parsedValue);
  context.print(`Configuration key "${key}" set to "${value}" in user settings.`);
}

async function resetConfig(
  context: CommandContext,
  key: string,
): Promise<void> {
  const settings = loadSettings(process.cwd());
  const userSettingsFile = settings.forScope(SettingScope.User);

  if (Object.prototype.hasOwnProperty.call(userSettingsFile.settings, key)) {
    delete userSettingsFile.settings[key as keyof typeof userSettingsFile.settings];
    settings.setValue(SettingScope.User, key as keyof Settings, undefined); // This will trigger save
    context.print(`Configuration key "${key}" reset to default in user settings.`);
  } else {
    context.print(`Configuration key "${key}" is not set in user settings.`);
  }
}

async function listConfig(context: CommandContext): Promise<void> {
  const settings = loadSettings(process.cwd());
  context.print('Current Configuration (merged from system, user, and workspace):');
  context.print(JSON.stringify(settings.merged, null, 2));

  context.print('\nAvailable Configuration Keys:');
  for (const key in SETTINGS_SCHEMA) {
    if (Object.prototype.hasOwnProperty.call(SETTINGS_SCHEMA, key)) {
      const definition = SETTINGS_SCHEMA[key];
      context.print(`- ${key}: ${definition.description || 'No description available.'} (Type: ${definition.type})`);
    }
  }
}

export const configCommand: SlashCommand = {
  name: 'config',
  description: 'Manage user configurations',
  kind: CommandKind.BUILT_IN,
  subCommands: [
    {
      name: 'get',
      description: 'Get a configuration value',
      kind: CommandKind.BUILT_IN,
      action: async (context, args) => {
        const key = args.trim();
        if (!key) {
          context.ui.addItem({ type: 'error', content: 'Usage: /config get <key>' });
          return;
        }
        await getConfig(context, key);
      },
    },
    {
      name: 'set',
      description: 'Set a configuration value',
      kind: CommandKind.BUILT_IN,
      action: async (context, args) => {
        const parts = args.trim().split(' ');
        const key = parts[0];
        const value = parts.slice(1).join(' ').trim();
        if (!key || !value) {
          context.ui.addItem({ type: 'error', content: 'Usage: /config set <key> <value>' });
          return;
        }
        await setConfig(context, key, value);
      },
    },
    {
      name: 'reset',
      description: 'Reset a configuration value to its default',
      kind: CommandKind.BUILT_IN,
      action: async (context, args) => {
        const key = args.trim();
        if (!key) {
          context.ui.addItem({ type: 'error', content: 'Usage: /config reset <key>' });
          return;
        }
        await resetConfig(context, key);
      },
    },
    {
      name: 'list',
      description: 'List all configuration keys and their values',
      kind: CommandKind.BUILT_IN,
      action: async (context) => {
        await listConfig(context);
      },
    },
  ],
};