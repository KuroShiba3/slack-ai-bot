from uuid import UUID

from ...domain.model.feedback import Feedback, FeedbackType
from ..database import DatabasePool


class FeedbackRepository:
    async def find_by_message_and_user(
        self, message_id: UUID, user_id: str
    ) -> Feedback | None:
        """メッセージIDとユーザーIDでフィードバックを取得"""
        async with DatabasePool.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, message_id, user_id, feedback, created_at, updated_at
                    FROM feedbacks
                    WHERE message_id = %s AND user_id = %s
                    """,
                    (message_id, user_id),
                )
                row = await cur.fetchone()

                if not row:
                    return None

                return Feedback.reconstruct(
                    id=row["id"],
                    user_id=row["user_id"],
                    message_id=row["message_id"],
                    feedback=FeedbackType(row["feedback"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

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