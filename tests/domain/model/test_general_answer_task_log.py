from src.domain.model.general_answer_task_log import GeneralAnswerTaskLog


def test_create_empty_log():
    """空のタスクログを生成するテスト"""
    log = GeneralAnswerTaskLog.create()

    assert log.attempts == []


def test_add_single_attempt():
    """単一の生成試行を追加するテスト"""
    log = GeneralAnswerTaskLog.create()
    response = "これはテスト回答です。"

    log.add_attempt(response=response)

    assert len(log.attempts) == 1
    assert log.attempts[0].response == response


def test_to_dict_single_attempt():
    """単一試行のログを辞書に変換するテスト"""
    log = GeneralAnswerTaskLog.create()
    response = "テスト回答です"
    log.add_attempt(response=response)

    result = log.to_dict()

    assert result == {"attempts": [{"response": "テスト回答です"}]}


def test_from_dict_single_attempt():
    """単一試行の辞書からログを復元するテスト"""
    data = {"attempts": [{"response": "復元された回答"}]}

    log = GeneralAnswerTaskLog.from_dict(data)

    assert len(log.attempts) == 1
    assert log.attempts[0].response == "復元された回答"
