# Interactive Mode Documentation

## Overview

The Interactive Mode provides a REPL-like experience with built-in teaching capabilities for progressive learning. It's designed to help developers at different skill levels learn through practice with context retention and intelligent guidance.

## Features

### 🎯 Progressive Learning
- **Teaching Levels**: Junior, Senior, Architect
- **Context-Aware**: Learns from your command history
- **Progressive Disclosure**: Information adapted to your level

### 📚 Teaching Engine Integration
- **Real-time Explanations**: Immediate feedback on commands
- **Learning Opportunities**: Identifies teaching moments automatically
- **Concept Suggestions**: Provides related concepts to explore

### 💾 Session Management
- **Context Retention**: Variables, functions, and state persist
- **Session History**: Review and replay previous sessions
- **Auto-save**: Sessions automatically saved to localStorage

### 🔄 REPL Features
- **Command History**: Navigate with ↑/↓ arrows
- **Special Commands**: Built-in commands for mode management
- **Error Recovery**: Graceful handling of failed operations

## Getting Started

### Starting Interactive Mode

```bash
# Start with default (junior) level
/interactive

# Alternative commands
/i
/repl
/teach

# Set specific level first
/level senior
/interactive
```

### Teaching Levels

#### 📚 Junior Level
- **Detailed explanations** with context and examples
- **Step-by-step guidance** through concepts
- **Related concepts** to explore next
- **Common pitfalls** and how to avoid them

Example output:
```
📚 Teaching Moment: function design patterns

What: Functions are reusable blocks of code that perform specific tasks
Why: This promotes code reusability and maintainability
How: Define with clear names, parameters, and return values
Example: function calculateTotal(items) { return items.reduce((sum, item) => sum + item.price, 0); }
```

#### ✓ Senior Level
- **Quick validations** and confirmations
- **Best practice** reminders
- **Code quality** insights
- **Performance considerations**

Example output:
```
✓ function design patterns: Best practice applied - clear function naming and single responsibility
```

#### 🏗️ Architect Level
- **Strategic discussions** about design choices
- **Trade-off analysis** between approaches
- **System-level implications**
- **Scalability considerations**

Example output:
```
🏗️ Architecture Decision: function design patterns
Trade-offs: Modular functions vs. inline code - Consider maintenance overhead vs. performance
```

## Special Commands

Interactive mode includes built-in commands for session management:

### `:help`
Display comprehensive help information
```
:help
```

### `:level [junior|senior|architect]`
Set or display current teaching level
```
:level                    # Show current level
:level senior            # Switch to senior level
:level architect         # Switch to architect level
```

### `:clear`
Clear screen and reset session context
```
:clear
```

### `:save`
Manually save current session
```
:save
```

### `:teaching [on|off]`
Toggle teaching moments display
```
:teaching                # Show current status
:teaching on            # Enable teaching moments
:teaching off           # Disable teaching moments
```

### `:exit` or `:quit`
Exit interactive mode
```
:exit
:quit
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Execute command |
| `↑` / `↓` | Navigate command history |
| `Ctrl+C` | Exit interactive mode |
| `Ctrl+D` | Exit interactive mode |
| `Backspace` | Delete character |
| `Delete` | Clear input line |

## Session Management

### Automatic Features
- **Auto-save**: Sessions saved every 5 seconds after activity
- **Context Retention**: Variables and state persist between commands
- **Command History**: All commands remembered with timestamps

### Manual Management
```bash
# Save current session
:save

# Sessions are automatically loaded on restart
# Use /interactive to resume last session
```

### Session Data Structure
```typescript
interface InteractiveSession {
  id: string;                    // Unique session identifier
  startTime: Date;              // Session start timestamp
  teachingLevel: TeachingLevel; // Current teaching level
  commands: InteractiveCommand[]; // Command history
  context: SessionContext;      // Variables, functions, state
  lastActivity: Date;           // Last command timestamp
}
```

## Context Management

The interactive mode maintains context across commands:

### Variables
```bash
$ name = "John"
Set name = John

$ greeting = `Hello ${name}`
Set greeting = Hello John
```

### Functions
```bash
$ function add(a, b) { return a + b; }
Processed: function add(a, b) { return a + b; }
Result: Success

$ add(2, 3)
Result: 5
```

### Imports and Dependencies
```bash
$ import { useState } from 'react'
Added import: useState from react

$ const [count, setCount] = useState(0)
Created state variable: count
```

## Teaching Moments

Teaching moments are automatically triggered based on:

### Code Patterns
- Function definitions
- Class declarations
- Async/await usage
- Testing patterns
- Error handling

### Learning Opportunities
- Common mistakes
- Performance optimizations
- Best practices
- Security considerations

### Example Teaching Moment
```bash
$ async function fetchUser(id) { return fetch(`/api/users/${id}`); }

📚 Teaching Moment: asynchronous programming

What: Async functions enable non-blocking operations
Why: Prevents UI freezing and improves user experience
How: Use async/await for cleaner promise handling
Example: 
  async function fetchData() {
    try {
      const response = await fetch('/api/data');
      return await response.json();
    } catch (error) {
      console.error('Fetch failed:', error);
    }
  }

Next steps:
  • Practice error handling with try/catch
  • Learn about Promise.all for concurrent requests
  • Explore async iteration with for-await-of
```

## Integration with Agent Server

The interactive mode integrates with the Python agent server's TeachingEngine:

### API Endpoints
- `POST /api/teaching/teach` - Generate teaching moments
- `POST /api/teaching/suggest` - Get next step suggestions
- `POST /api/teaching/validate` - Validate learning progress

### Offline Fallback
When the agent server is unavailable:
- Basic teaching moments still provided
- Fallback explanations used
- Local pattern matching for learning opportunities

## Troubleshooting

### Common Issues

#### Teaching moments not appearing
```bash
# Check if teaching is enabled
:teaching

# Enable if disabled
:teaching on

# Verify teaching level
:level
```

#### Session not saving
- Check browser localStorage permissions
- Verify adequate storage space
- Check console for error messages

#### Commands not executing
- Ensure agent server is running (`./start_server.sh`)
- Check network connectivity
- Try simpler commands first

#### Context not persisting
```bash
# Clear and restart session
:clear

# Check current context
:help  # Shows current session info
```

### Debug Information

The interactive mode header shows:
- Current teaching level
- Session ID (last 8 characters)
- Command count
- Teaching moment status

## Best Practices

### For Learning
1. **Start at appropriate level** - Don't skip to architect level immediately
2. **Read teaching moments** - They provide valuable context
3. **Practice regularly** - Use interactive mode for experimentation
4. **Save important sessions** - Manual save before exploring risky commands

### For Development
1. **Use context wisely** - Build up variables and functions incrementally
2. **Clear context when needed** - Start fresh for new topics
3. **Review session history** - Learn from previous explorations
4. **Experiment safely** - Interactive mode is perfect for trying new ideas

## Advanced Usage

### Custom Teaching Scenarios
The teaching engine can be extended to support custom learning paths and domain-specific knowledge.

### Integration with Projects
Interactive mode can be started within specific project contexts to provide relevant suggestions and examples.

### Team Learning
Sessions can be shared and replayed to facilitate team learning and knowledge transfer.

## Future Enhancements

- **Collaborative Sessions**: Multi-user interactive environments
- **Learning Paths**: Structured curriculum integration
- **Code Execution**: Direct code execution within the REPL
- **Visual Learning**: Diagrams and visual aids for complex concepts
- **Assessment Integration**: Progress tracking and skill evaluation