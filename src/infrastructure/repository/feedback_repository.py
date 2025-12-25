from ...domain.model.feedback import Feedback
from ..database import DatabasePool


class FeedbackRepository:
    async def save(self, feedback: Feedback) -> None:
        """フィードバックを保存"""
        async with DatabasePool.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO feedbacks (id, message_id, user_id, feedback, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id, user_id) DO UPDATE SET
                    feedback = EXCLUDED.feedback,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    feedback.id,
                    feedback.message_id,
                    feedback.user_id,
                    feedback.feedback.value,
                    feedback.created_at,
                    feedback.updated_at,
                ),
            )