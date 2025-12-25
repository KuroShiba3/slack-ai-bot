-- depends: create_task_plans

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY,
    task_plan_id UUID NOT NULL REFERENCES task_plans(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    agent_name VARCHAR(50) NOT NULL CHECK (agent_name IN ('general_answer', 'web_search')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed')),
    result TEXT,
    task_log_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_tasks_task_plan_id ON tasks(task_plan_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_name ON tasks(agent_name);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);