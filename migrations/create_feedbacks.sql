CREATE TABLE IF NOT EXISTS feedbacks (
    id UUID PRIMARY KEY,
    message_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    feedback VARCHAR(10) NOT NULL CHECK (feedback IN ('good', 'bad')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_feedbacks_message_id ON feedbacks(message_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_user_id ON feedbacks(user_id);
CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at ON feedbacks(created_at DESC);