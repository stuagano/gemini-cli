-- Initialize Gemini Enterprise database schema

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS tasks;
CREATE SCHEMA IF NOT EXISTS sessions;

-- Agents table
CREATE TABLE IF NOT EXISTS agents.agent_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive',
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks.task_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents.agent_instances(id),
    task_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    payload JSONB,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    agent_id UUID REFERENCES agents.agent_instances(id),
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge base metadata
CREATE TABLE IF NOT EXISTS knowledge.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    content_hash VARCHAR(64),
    metadata JSONB,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge chunks for RAG
CREATE TABLE IF NOT EXISTS knowledge.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES knowledge.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_vector VECTOR(384), -- Assuming 384-dimensional embeddings
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents.agent_instances(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents.agent_instances(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks.task_queue(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks.task_queue(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks.task_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions.user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON knowledge.documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON knowledge.document_chunks(document_id);

-- Grant permissions to gemini user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agents TO gemini;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA knowledge TO gemini;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tasks TO gemini;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sessions TO gemini;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agents TO gemini;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA knowledge TO gemini;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tasks TO gemini;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sessions TO gemini;