import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

interface Epic {
    title: string;
    status: 'not-started' | 'in-progress' | 'completed';
    stories: Story[];
    file: string;
    completionPercentage: number;
}

interface Story {
    title: string;
    status: 'todo' | 'in-progress' | 'done';
    file: string;
    epic?: string;
}

export class EpicsStoriesProvider implements vscode.TreeDataProvider<ProjectItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ProjectItem | undefined | null | void> = new vscode.EventEmitter<ProjectItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ProjectItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private epics: Epic[] = [];
    private stories: Story[] = [];

    constructor() {
        this.loadEpicsAndStories();
    }

    refresh(): void {
        this.loadEpicsAndStories();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ProjectItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ProjectItem): Thenable<ProjectItem[]> {
        if (!vscode.workspace.workspaceFolders) {
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - show epics
            return Promise.resolve(this.getEpics());
        } else if (element.contextValue === 'epic') {
            // Show stories for this epic
            return Promise.resolve(this.getStoriesForEpic(element.label as string));
        }

        return Promise.resolve([]);
    }

    private loadEpicsAndStories(): void {
        if (!vscode.workspace.workspaceFolders) {
            return;
        }

        const workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const tasksPath = path.join(workspaceRoot, 'docs', 'tasks');

        if (!fs.existsSync(tasksPath)) {
            return;
        }

        this.epics = [];
        this.stories = [];

        const files = fs.readdirSync(tasksPath);
        
        // Load epics
        files.filter(f => f.startsWith('epic-') && f.endsWith('.md')).forEach(file => {
            const filePath = path.join(tasksPath, file);
            const content = fs.readFileSync(filePath, 'utf8');
            const epic = this.parseEpic(content, file);
            this.epics.push(epic);
        });

        // Load stories
        files.filter(f => f.startsWith('story-') && f.endsWith('.md')).forEach(file => {
            const filePath = path.join(tasksPath, file);
            const content = fs.readFileSync(filePath, 'utf8');
            const story = this.parseStory(content, file);
            this.stories.push(story);
        });

        // Link stories to epics
        this.linkStoriesToEpics();
    }

    private parseEpic(content: string, filename: string): Epic {
        const titleMatch = content.match(/^#\s+(.+)/m);
        const title = titleMatch ? titleMatch[1] : filename;
        
        // Check for completion percentage
        const percentageMatch = content.match(/Completion:\s*\*\*(\d+)%\*\*/);
        const completionPercentage = percentageMatch ? parseInt(percentageMatch[1]) : 0;
        
        // Determine status based on content
        let status: 'not-started' | 'in-progress' | 'completed' = 'not-started';
        if (content.includes('[COMPLETED]') || completionPercentage === 100) {
            status = 'completed';
        } else if (content.includes('[IN PROGRESS]') || completionPercentage > 0) {
            status = 'in-progress';
        }

        return {
            title,
            status,
            stories: [],
            file: filename,
            completionPercentage
        };
    }

    private parseStory(content: string, filename: string): Story {
        const titleMatch = content.match(/^#\s+(.+)/m);
        const title = titleMatch ? titleMatch[1] : filename;
        
        // Check story status
        let status: 'todo' | 'in-progress' | 'done' = 'todo';
        if (content.includes('Status:** Done') || 
            content.includes('*Story Status*: **Completed**') ||
            content.includes('✅')) {
            status = 'done';
        } else if (content.includes('Status:** In Progress') || 
                   content.includes('*Story Status*: **In Progress**')) {
            status = 'in-progress';
        }

        // Find associated epic
        const epicMatch = content.match(/Epic:\s*(.+)/);
        const epic = epicMatch ? epicMatch[1] : undefined;

        return {
            title,
            status,
            file: filename,
            epic
        };
    }

    private linkStoriesToEpics(): void {
        this.stories.forEach(story => {
            const epic = this.epics.find(e => 
                story.epic && (e.title.includes(story.epic) || e.file.includes(story.epic))
            );
            if (epic) {
                epic.stories.push(story);
            }
        });

        // Update epic completion percentages based on stories
        this.epics.forEach(epic => {
            if (epic.stories.length > 0) {
                const completedStories = epic.stories.filter(s => s.status === 'done').length;
                epic.completionPercentage = Math.round((completedStories / epic.stories.length) * 100);
            }
        });
    }

    private getEpics(): ProjectItem[] {
        return this.epics.map(epic => {
            const icon = this.getEpicIcon(epic.status);
            const label = `${icon} ${epic.title}`;
            const description = `${epic.completionPercentage}% (${epic.stories.length} stories)`;
            
            return new ProjectItem(
                label,
                epic.stories.length > 0 ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None,
                'epic',
                epic.file,
                description,
                epic
            );
        });
    }

    private getStoriesForEpic(epicLabel: string): ProjectItem[] {
        // Extract epic title from label
        const epicTitle = epicLabel.substring(2); // Remove icon and space
        const epic = this.epics.find(e => e.title === epicTitle);
        
        if (!epic) {
            return [];
        }

        return epic.stories.map(story => {
            const icon = this.getStoryIcon(story.status);
            const label = `${icon} ${story.title}`;
            
            return new ProjectItem(
                label,
                vscode.TreeItemCollapsibleState.None,
                story.status === 'done' ? 'story-complete' : 'story-incomplete',
                story.file,
                story.status,
                undefined,
                story
            );
        });
    }

    private getEpicIcon(status: 'not-started' | 'in-progress' | 'completed'): string {
        switch (status) {
            case 'completed': return '✅';
            case 'in-progress': return '🔄';
            default: return '📋';
        }
    }

    private getStoryIcon(status: 'todo' | 'in-progress' | 'done'): string {
        switch (status) {
            case 'done': return '✅';
            case 'in-progress': return '🔄';
            default: return '⭕';
        }
    }
}

export class ProjectItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly file: string,
        public readonly description?: string,
        public readonly epic?: Epic,
        public readonly story?: Story
    ) {
        super(label, collapsibleState);
        
        this.tooltip = this.getTooltip();
        
        if (contextValue === 'epic' || contextValue.startsWith('story')) {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
            if (workspaceRoot) {
                const filePath = path.join(workspaceRoot, 'docs', 'tasks', this.file);
                this.command = {
                    command: 'vscode.open',
                    title: 'Open',
                    arguments: [vscode.Uri.file(filePath)]
                };
            }
        }
    }

    private getTooltip(): string {
        if (this.epic) {
            return `Epic: ${this.epic.title}\nStatus: ${this.epic.status}\nCompletion: ${this.epic.completionPercentage}%\nStories: ${this.epic.stories.length}`;
        } else if (this.story) {
            return `Story: ${this.story.title}\nStatus: ${this.story.status}\nFile: ${this.story.file}`;
        }
        return this.label;
    }
}