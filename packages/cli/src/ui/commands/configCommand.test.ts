/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { configCommand } from './configCommand.js';
import { createMockCommandContext } from '../../test-utils/mockCommandContext.js';
import * as settingsModule from '../../config/settings.js';
import { SETTINGS_SCHEMA } from '../../config/settingsSchema.js';
import { CustomTheme } from '../ui/themes/theme.js';

// Mock the settings module
vi.mock('../../config/settings.js', async (importOriginal) => {
  const actual = await importOriginal<typeof settingsModule>();
  return {
    ...actual,
    loadSettings: vi.fn(),
    saveSettings: vi.fn(),
  };
});

describe('configCommand', () => {
  let mockContext: ReturnType<typeof createMockCommandContext>;
  let mockLoadedSettings: settingsModule.LoadedSettings;
  let mockUserSettings: settingsModule.Settings;

  beforeEach(() => {
    vi.clearAllMocks();

    mockUserSettings = {
      theme: 'dark',
      showMemoryUsage: true,
    };

    mockLoadedSettings = new settingsModule.LoadedSettings(
      { path: '/system/settings.json', settings: {} },
      { path: settingsModule.USER_SETTINGS_PATH, settings: mockUserSettings },
      { path: '/workspace/.gemini/settings.json', settings: {} },
      [],
    );

    // Mock loadSettings to return our mockLoadedSettings
    vi.mocked(settingsModule.loadSettings).mockReturnValue(mockLoadedSettings);

    mockContext = createMockCommandContext();
  });

  // Helper to get a subcommand handler
  const getSubCommandHandler = (commandName: string) => {
    const subCommand = configCommand.subCommands?.find(
      (cmd) => cmd.name === commandName,
    );
    if (!subCommand) {
      throw new Error(`Subcommand "${commandName}" not found.`);
    }
    return subCommand.action;
  };

  describe('get subcommand', () => {
    it('should return the value of an existing configuration key', async () => {
      const handler = getSubCommandHandler('get');
      await handler!(mockContext, 'theme');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Value for "theme": "dark"',
      });
    });

    it('should return a JSON string for object/array values', async () => {
      mockUserSettings.customThemes = {
        myTheme: {
          name: 'myTheme',
          text: {
            primary: '#FF0000',
          },
        } as CustomTheme,
      };
      const handler = getSubCommandHandler('get');
      await handler!(mockContext, 'customThemes');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Value for "customThemes": {\n  "myTheme": {\n    "name": "myTheme",\n    "text": {\n      "primary": "#FF0000"\n    }\n  }\n}',
      });
    });

    it('should indicate if a configuration key is not found', async () => {
      const handler = getSubCommandHandler('get');
      await handler!(mockContext, 'nonExistentKey');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "nonExistentKey" not found.',
      });
    });

    it('should show usage if no key is provided', async () => {
      const handler = getSubCommandHandler('get');
      await handler!(mockContext, '');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: 'Usage: /config get <key>',
      });
    });
  });

  describe('set subcommand', () => {
    it('should set a string configuration value', async () => {
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'theme light');
      expect(mockLoadedSettings.setValue).toHaveBeenCalledWith(
        settingsModule.SettingScope.User,
        'theme',
        'light',
      );
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "theme" set to "light" in user settings.',
      });
    });

    it('should set a boolean configuration value', async () => {
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'showMemoryUsage false');
      expect(mockLoadedSettings.setValue).toHaveBeenCalledWith(
        settingsModule.SettingScope.User,
        'showMemoryUsage',
        false,
      );
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "showMemoryUsage" set to "false" in user settings.',
      });
    });

    it('should set a number configuration value', async () => {
      mockUserSettings.maxSessionTurns = 10; // Add to schema for testing
      (SETTINGS_SCHEMA as any).maxSessionTurns = { type: 'number', label: 'Max Session Turns', category: 'General', requiresRestart: false, default: 10 };
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'maxSessionTurns 20');
      expect(mockLoadedSettings.setValue).toHaveBeenCalledWith(
        settingsModule.SettingScope.User,
        'maxSessionTurns',
        20,
      );
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "maxSessionTurns" set to "20" in user settings.',
      });
    });

    it('should set an array configuration value', async () => {
      mockUserSettings.includeDirectories = [];
      (SETTINGS_SCHEMA as any).includeDirectories = { type: 'array', label: 'Include Directories', category: 'General', requiresRestart: false, default: [] };
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'includeDirectories ["src", "dist"]');
      expect(mockLoadedSettings.setValue).toHaveBeenCalledWith(
        settingsModule.SettingScope.User,
        'includeDirectories',
        ['src', 'dist'],
      );
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "includeDirectories" set to "[\"src\",\"dist\"]" in user settings.',
      });
    });

    it('should set an object configuration value', async () => {
      mockUserSettings.telemetry = {};
      (SETTINGS_SCHEMA as any).telemetry = { type: 'object', label: 'Telemetry', category: 'Advanced', requiresRestart: true, default: {} };
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'telemetry {"enabled":true}');
      expect(mockLoadedSettings.setValue).toHaveBeenCalledWith(
        settingsModule.SettingScope.User,
        'telemetry',
        { enabled: true },
      );
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "telemetry" set to "{\"enabled\":true}" in user settings.',
      });
    });

    it('should handle unknown configuration keys', async () => {
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'unknownKey value');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: 'Unknown configuration key: "unknownKey".',
      });
      expect(mockLoadedSettings.setValue).not.toHaveBeenCalled();
    });

    it('should show usage if key or value is missing', async () => {
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'keyOnly');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: 'Usage: /config set <key> <value>',
      });
    });

    it('should handle invalid value for boolean type', async () => {
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'showMemoryUsage notABoolean');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: 'Error parsing value for "showMemoryUsage": Invalid boolean value for "showMemoryUsage": "notABoolean"',
      });
      expect(mockLoadedSettings.setValue).not.toHaveBeenCalled();
    });

    it('should handle invalid value for number type', async () => {
      (SETTINGS_SCHEMA as any).maxSessionTurns = { type: 'number', label: 'Max Session Turns', category: 'General', requiresRestart: false, default: 10 };
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'maxSessionTurns notANumber');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: 'Error parsing value for "maxSessionTurns": Invalid number value for "maxSessionTurns": "notANumber"',
      });
      expect(mockLoadedSettings.setValue).not.toHaveBeenCalled();
    });

    it('should handle invalid JSON for array type', async () => {
      (SETTINGS_SCHEMA as any).includeDirectories = { type: 'array', label: 'Include Directories', category: 'General', requiresRestart: false, default: [] };
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'includeDirectories notAnArray');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: expect.stringContaining('Error parsing value for "includeDirectories": Unexpected token \'o\', "notAnArray" is not valid JSON.'),
      });
      expect(mockLoadedSettings.setValue).not.toHaveBeenCalled();
    });

    it('should handle invalid JSON for object type', async () => {
      (SETTINGS_SCHEMA as any).telemetry = { type: 'object', label: 'Telemetry', category: 'Advanced', requiresRestart: true, default: {} };
      const handler = getSubCommandHandler('set');
      await handler!(mockContext, 'telemetry notAnObject');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: expect.stringContaining('Error parsing value for "telemetry": Unexpected token \'o\', "notAnObject" is not valid JSON.'),
      });
      expect(mockLoadedSettings.setValue).not.toHaveBeenCalled();
    });
  });

  describe('reset subcommand', () => {
    it('should reset an existing configuration key in user settings', async () => {
      mockUserSettings.theme = 'dark';
      const handler = getSubCommandHandler('reset');
      await handler!(mockContext, 'theme');
      expect(mockLoadedSettings.setValue).toHaveBeenCalledWith(
        settingsModule.SettingScope.User,
        'theme',
        undefined,
      );
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "theme" reset to default in user settings.',
      });
      expect(mockUserSettings.theme).toBeUndefined(); // Verify it's deleted from the mock
    });

    it('should indicate if a configuration key is not set in user settings', async () => {
      mockUserSettings.theme = undefined; // Ensure it's not in user settings
      const handler = getSubCommandHandler('reset');
      await handler!(mockContext, 'theme');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: 'Configuration key "theme" is not set in user settings.',
      });
      expect(mockLoadedSettings.setValue).not.toHaveBeenCalled(); // setValue should not be called if not present
    });

    it('should show usage if no key is provided', async () => {
      const handler = getSubCommandHandler('reset');
      await handler!(mockContext, '');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'error',
        text: 'Usage: /config reset <key>',
      });
    });
  });

  describe('list subcommand', () => {
    it('should list all configuration keys and their values', async () => {
      const handler = getSubCommandHandler('list');
      await handler!(mockContext, '');
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('Current Configuration (merged from system, user, and workspace):'),
      });
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining(JSON.stringify(mockLoadedSettings.merged, null, 2)),
      });
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('Available Configuration Keys:'),
      });
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('- theme: The color theme for the UI. (Type: string)'),
      });
      expect(mockContext.ui.addItem).toHaveBeenCalledWith({
        type: 'info',
        text: expect.stringContaining('- showMemoryUsage: Display memory usage information in the UI (Type: boolean)'),
      });
    });
  });
});