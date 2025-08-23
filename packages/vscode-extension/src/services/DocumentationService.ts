import * as fs from 'fs';
import * as path from 'path';

export interface DocumentStatus {
    complete: boolean;
    inProgress: boolean;
    hasContent: boolean;
    wordCount: number;
    sections: string[];
    missingRequirements?: string[];
}

export class DocumentationService {
    private requiredSections: { [key: string]: string[] } = {
        'business-case.md': ['Executive Summary', 'Problem Statement', 'Solution', 'ROI Analysis', 'Risk Assessment'],
        'prd.md': ['Overview', 'Goals', 'User Stories', 'Requirements', 'Success Metrics'],
        'architecture.md': ['System Overview', 'Components', 'Data Flow', 'Security', 'Scalability'],
        'api-specification.md': ['Endpoints', 'Authentication', 'Request/Response', 'Error Handling'],
        'testing-strategy.md': ['Test Types', 'Coverage Goals', 'Test Environment', 'CI/CD Integration']
    };

    getDocumentStatus(filePath: string): DocumentStatus {
        if (!fs.existsSync(filePath)) {
            return {
                complete: false,
                inProgress: false,
                hasContent: false,
                wordCount: 0,
                sections: []
            };
        }

        const content = fs.readFileSync(filePath, 'utf8');
        const sections = this.extractSections(content);
        const wordCount = this.countWords(content);
        const fileName = path.basename(filePath);
        
        // Check required sections
        const required = this.requiredSections[fileName] || [];
        const missingSections = required.filter(req => 
            !sections.some(sec => sec.toLowerCase().includes(req.toLowerCase()))
        );

        return {
            complete: missingSections.length === 0 && wordCount > 100,
            inProgress: wordCount > 50 && wordCount < 500,
            hasContent: wordCount > 0,
            wordCount,
            sections,
            missingRequirements: missingSections
        };
    }

    getCategoryStatus(categoryPath: string): DocumentStatus {
        if (!fs.existsSync(categoryPath)) {
            return {
                complete: false,
                inProgress: false,
                hasContent: false,
                wordCount: 0,
                sections: []
            };
        }

        const files = fs.readdirSync(categoryPath).filter(f => f.endsWith('.md'));
        let totalComplete = 0;
        let totalWords = 0;
        let allSections: string[] = [];

        files.forEach(file => {
            const status = this.getDocumentStatus(path.join(categoryPath, file));
            if (status.complete) totalComplete++;
            totalWords += status.wordCount;
            allSections = allSections.concat(status.sections);
        });

        return {
            complete: files.length > 0 && totalComplete === files.length,
            inProgress: totalComplete > 0 && totalComplete < files.length,
            hasContent: totalWords > 0,
            wordCount: totalWords,
            sections: allSections
        };
    }

    private extractSections(content: string): string[] {
        const sections: string[] = [];
        const lines = content.split('\n');
        
        for (const line of lines) {
            const match = line.match(/^#{1,3}\s+(.+)/);
            if (match) {
                sections.push(match[1]);
            }
        }
        
        return sections;
    }

    private countWords(content: string): number {
        // Remove markdown syntax
        const cleanContent = content
            .replace(/```[\s\S]*?```/g, '') // Remove code blocks
            .replace(/`[^`]*`/g, '') // Remove inline code
            .replace(/#+\s/g, '') // Remove headers
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Convert links to text
            .replace(/[*_~]/g, ''); // Remove emphasis markers
        
        const words = cleanContent.match(/\b\w+\b/g);
        return words ? words.length : 0;
    }

    async validateDocument(filePath: string): Promise<{valid: boolean; errors: string[]}> {
        const errors: string[] = [];
        const status = this.getDocumentStatus(filePath);
        
        if (status.wordCount < 100) {
            errors.push('Document should contain at least 100 words');
        }
        
        if (status.missingRequirements && status.missingRequirements.length > 0) {
            errors.push(`Missing required sections: ${status.missingRequirements.join(', ')}`);
        }
        
        // Check for TODO items
        const content = fs.readFileSync(filePath, 'utf8');
        if (content.includes('TODO') || content.includes('TBD')) {
            errors.push('Document contains TODO or TBD items');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    }

    async generateTemplate(documentType: string): Promise<string> {
        const templates: { [key: string]: string } = {
            'business-case': `# Business Case

## Executive Summary
[Provide a brief overview of the business case]

## Problem Statement
### Current State
- 

### Challenges
- 

### Opportunity Cost
- 

## Solution
### Proposed Approach
- 

### Key Benefits
- 

## ROI Analysis
### Investment Required
- Development: $
- Infrastructure: $
- Training: $

### Expected Returns
- Year 1: $
- Year 2: $
- Year 3: $

### Payback Period
[Expected time to recover investment]

## Risk Assessment
### Technical Risks
- 

### Business Risks
- 

### Mitigation Strategies
- 

## Success Metrics
- 
`,
            'architecture': `# Architecture Document

## System Overview
[High-level description of the system]

## Components
### Frontend
- 

### Backend
- 

### Database
- 

### External Services
- 

## Data Flow
\`\`\`mermaid
graph LR
    A[User] --> B[Frontend]
    B --> C[API Gateway]
    C --> D[Backend Services]
    D --> E[Database]
\`\`\`

## Security
### Authentication
- 

### Authorization
- 

### Data Protection
- 

## Scalability
### Horizontal Scaling
- 

### Vertical Scaling
- 

### Performance Targets
- 
`,
            'api': `# API Specification

## Overview
[API description and purpose]

## Base URL
\`\`\`
https://api.example.com/v1
\`\`\`

## Authentication
### Method
- Bearer Token

### Headers
\`\`\`
Authorization: Bearer <token>
\`\`\`

## Endpoints

### GET /endpoint
#### Description
[What this endpoint does]

#### Request
\`\`\`json
{
  // Request body
}
\`\`\`

#### Response
\`\`\`json
{
  // Response body
}
\`\`\`

#### Error Codes
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Error Handling
### Error Response Format
\`\`\`json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
\`\`\`
`
        };

        return templates[documentType] || '# Document\n\n## Overview\n\n## Details\n';
    }
}