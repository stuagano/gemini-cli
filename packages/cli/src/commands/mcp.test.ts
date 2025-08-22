/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect, vi } from 'vitest';
import { mcpCommand } from './mcp.js';
import { type Argv } from 'yargs';
import yargs from 'yargs';

describe('mcp command', () => {
  it('should have correct command definition', () => {
    expect(mcpCommand.command).toBe('mcp');
    expect(mcpCommand.describe).toBe('Manage MCP servers');
    expect(typeof mcpCommand.builder).toBe('function');
    expect(typeof mcpCommand.handler).toBe('function');
  });

  it('should have exactly one option (help flag)', () => {
    // Test to ensure that the global 'gemini' flags are not added to the mcp command
    const yargsInstance = yargs();
    const builtYargs = mcpCommand.builder?.(yargsInstance);
    if (builtYargs) {
      const options = builtYargs.getOptions();
      // Should have exactly 1 option (help flag)
      expect(Object.keys(options.key).length).toBe(1);
      expect(options.key).toHaveProperty('help');
    }
  });

  it('should register add, remove, and list subcommands', () => {
    const commandSpy = vi.fn().mockReturnThis();
    const demandCommandSpy = vi.fn().mockReturnThis();
    const versionSpy = vi.fn().mockReturnThis();
    
    const mockYargs: Partial<Argv> = {
      command: commandSpy,
      demandCommand: demandCommandSpy,
      version: versionSpy,
    };

    mcpCommand.builder?.(mockYargs as Argv);

    expect(commandSpy).toHaveBeenCalledTimes(3);
    expect(demandCommandSpy).toHaveBeenCalledWith(
      1,
      'You need at least one command before continuing.',
    );
    expect(versionSpy).toHaveBeenCalledWith(false);
  });
});
