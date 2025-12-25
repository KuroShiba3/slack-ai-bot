-- depends: create_chat_sessions

CREATE TABLE IF NOT EXISTS task_plans (
    id UUID PRIMARY KEY,
    chat_session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_plans_chat_session_id ON task_plans(chat_session_id);
CREATE INDEX IF NOT EXISTS idx_task_plans_message_id ON task_plans(message_id);
CREATE INDEX IF NOT EXISTS idx_task_plans_created_at ON task_plans(created_at DESC);