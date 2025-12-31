from uuid import uuid4

import pytest

from src.application.dto.feedback_usecase import FeedbackInput
from src.application.usecase.feedback_usecase import FeedbackUseCase
from src.domain.model.feedback import FeedbackType
from tests.infrastructure.repository.in_memory_feedback_repository import (
    InMemoryFeedbackRepository,
)


@pytest.fixture
def repository():
    """インメモリリポジトリ"""
    repo = InMemoryFeedbackRepository()
    yield repo
    repo.clear()


@pytest.fixture
def usecase(repository):
    """FeedbackUseCaseのインスタンス"""
    return FeedbackUseCase(feedback_repository=repository)


@pytest.mark.asyncio
async def test_first_feedback_is_saved(usecase, repository):
    """初回フィードバックが保存されるテスト"""
    message_id = uuid4()
    input_dto = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )

    await usecase.execute(input_dto)

    # フィードバックが保存されていることを確認
    saved_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    assert saved_feedback is not None
    assert saved_feedback.message_id == message_id
    assert saved_feedback.user_id == "U12345"
    assert saved_feedback.feedback == FeedbackType.GOOD
    assert saved_feedback.is_positive()


@pytest.mark.asyncio
async def test_feedback_can_be_updated_from_good_to_bad(usecase, repository):
    """GoodからBadへフィードバックを変更できるテスト"""
    message_id = uuid4()

    # 最初にGoodフィードバックを保存
    input_dto1 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto1)

    # Badに変更
    input_dto2 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="bad",
        user_id="U12345",
    )
    await usecase.execute(input_dto2)

    # フィードバックが更新されていることを確認
    saved_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    assert saved_feedback is not None
    assert saved_feedback.feedback == FeedbackType.BAD
    assert saved_feedback.is_negative()


@pytest.mark.asyncio
async def test_feedback_can_be_updated_from_bad_to_good(usecase, repository):
    """BadからGoodへフィードバックを変更できるテスト"""
    message_id = uuid4()

    # 最初にBadフィードバックを保存
    input_dto1 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="bad",
        user_id="U12345",
    )
    await usecase.execute(input_dto1)

    # Goodに変更
    input_dto2 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto2)

    # フィードバックが更新されていることを確認
    saved_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    assert saved_feedback is not None
    assert saved_feedback.feedback == FeedbackType.GOOD
    assert saved_feedback.is_positive()


@pytest.mark.asyncio
async def test_multiple_users_can_give_feedback_to_same_message(usecase, repository):
    """同じメッセージに複数のユーザーがフィードバックできるテスト"""
    message_id = uuid4()

    # ユーザー1のフィードバック
    input_dto1 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U11111",
    )
    await usecase.execute(input_dto1)

    # ユーザー2のフィードバック
    input_dto2 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="bad",
        user_id="U22222",
    )
    await usecase.execute(input_dto2)

    # 両方のフィードバックが保存されていることを確認
    feedback1 = await repository.find_by_message_and_user(message_id, "U11111")
    feedback2 = await repository.find_by_message_and_user(message_id, "U22222")

    assert feedback1 is not None
    assert feedback2 is not None

    assert feedback1.feedback == FeedbackType.GOOD
    assert feedback2.feedback == FeedbackType.BAD


@pytest.mark.asyncio
async def test_user_can_give_feedback_to_multiple_messages(usecase, repository):
    """1人のユーザーが複数のメッセージにフィードバックできるテスト"""
    message_id1 = uuid4()
    message_id2 = uuid4()

    # メッセージ1へのフィードバック
    input_dto1 = FeedbackInput(
        message_id=str(message_id1),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto1)

    # メッセージ2へのフィードバック
    input_dto2 = FeedbackInput(
        message_id=str(message_id2),
        feedback_type="bad",
        user_id="U12345",
    )
    await usecase.execute(input_dto2)

    # 両方のフィードバックが保存されていることを確認
    feedback1 = await repository.find_by_message_and_user(message_id1, "U12345")
    feedback2 = await repository.find_by_message_and_user(message_id2, "U12345")

    assert feedback1 is not None
    assert feedback2 is not None

    assert feedback1.message_id == message_id1
    assert feedback2.message_id == message_id2


@pytest.mark.asyncio
async def test_updating_feedback_preserves_id(usecase, repository):
    """フィードバック更新時にIDが保持されることをテスト"""
    message_id = uuid4()

    # 最初のフィードバック
    input_dto1 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto1)

    # IDを記録
    first_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    original_id = first_feedback.id

    # フィードバックを更新
    input_dto2 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="bad",
        user_id="U12345",
    )
    await usecase.execute(input_dto2)

    # IDが保持されていることを確認
    updated_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    assert updated_feedback.id == original_id


@pytest.mark.asyncio
async def test_same_feedback_type_does_not_update_timestamp(usecase, repository):
    """同じフィードバックタイプの場合にタイムスタンプが更新されないテスト"""
    message_id = uuid4()

    # 最初のフィードバック
    input_dto1 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto1)

    # 最初の更新日時を記録
    first_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    original_updated_at = first_feedback.updated_at

    # 同じフィードバックを再度送信
    input_dto2 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto2)

    # 更新日時が変わっていないことを確認
    second_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    assert second_feedback.updated_at == original_updated_at


@pytest.mark.asyncio
async def test_different_feedback_type_updates_timestamp(usecase, repository):
    """異なるフィードバックタイプの場合にタイムスタンプが更新されるテスト"""
    message_id = uuid4()

    # 最初のフィードバック
    input_dto1 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="good",
        user_id="U12345",
    )
    await usecase.execute(input_dto1)

    # 最初の更新日時を記録
    first_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    original_updated_at = first_feedback.updated_at

    # 異なるフィードバックを送信
    input_dto2 = FeedbackInput(
        message_id=str(message_id),
        feedback_type="bad",
        user_id="U12345",
    )
    await usecase.execute(input_dto2)

    # 更新日時が変わっていることを確認
    second_feedback = await repository.find_by_message_and_user(message_id, "U12345")
    assert second_feedback.updated_at > original_updated_at


@pytest.mark.asyncio
async def test_nonexistent_feedback_returns_none(usecase, repository):
    """存在しないフィードバックを取得するとNoneが返るテスト"""
    message_id = uuid4()

    feedback = await repository.find_by_message_and_user(message_id, "U12345")

    assert feedback is None
