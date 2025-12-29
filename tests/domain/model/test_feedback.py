from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.domain.model.feedback import Feedback, FeedbackType


def test_create_good_feedback():
    """GOODフィードバックを生成するテスト"""
    feedback = Feedback.create(
        user_id="U12345", message_id=uuid4(), feedback=FeedbackType.GOOD
    )

    assert feedback.feedback == FeedbackType.GOOD
    assert feedback.is_positive() is True
    assert feedback.is_negative() is False


def test_create_bad_feedback():
    """BADフィードバックを生成するテスト"""
    feedback = Feedback.create(
        user_id="U12345", message_id=uuid4(), feedback=FeedbackType.BAD
    )

    assert feedback.feedback == FeedbackType.BAD
    assert feedback.is_positive() is False
    assert feedback.is_negative() is True


def test_reconstruct_feedback():
    """フィードバックを再構築するテスト"""
    feedback_id = uuid4()
    user_id = "U12345"
    message_id = uuid4()
    feedback_type = FeedbackType.GOOD
    created_at = datetime(2024, 1, 1, 12, 0, 0)
    updated_at = datetime(2024, 1, 2, 12, 0, 0)

    feedback = Feedback.reconstruct(
        id=feedback_id,
        user_id=user_id,
        message_id=message_id,
        feedback=feedback_type,
        created_at=created_at,
        updated_at=updated_at,
    )

    assert feedback.id == feedback_id
    assert feedback.user_id == user_id
    assert feedback.message_id == message_id
    assert feedback.feedback == feedback_type
    assert feedback.created_at == created_at
    assert feedback.updated_at == updated_at


def test_make_positive():
    """フィードバックをポジティブに変更するテスト"""
    feedback = Feedback.create(
        user_id="U12345", message_id=uuid4(), feedback=FeedbackType.BAD
    )
    original_updated_at = feedback.updated_at

    feedback.make_positive()

    assert feedback.feedback == FeedbackType.GOOD
    assert feedback.is_positive() is True
    assert feedback.updated_at > original_updated_at


def test_make_negative():
    """フィードバックをネガティブに変更するテスト"""
    feedback = Feedback.create(
        user_id="U12345", message_id=uuid4(), feedback=FeedbackType.GOOD
    )
    original_updated_at = feedback.updated_at

    feedback.make_negative()

    assert feedback.feedback == FeedbackType.BAD
    assert feedback.is_negative() is True
    assert feedback.updated_at > original_updated_at
