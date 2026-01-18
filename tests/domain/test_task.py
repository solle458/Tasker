"""
domain/models/task.py のテスト
"""

from src.domain.models.task import Task, TaskType


class TestTaskType:
    """TaskType Enum のテスト"""

    def test_all_task_types_exist(self):
        """全てのTaskType値が存在することを確認"""
        expected_types = ["Daily", "Must", "Should", "Could"]
        actual_types = [t.name for t in TaskType]
        assert set(actual_types) == set(expected_types)

    def test_task_type_values_are_unique(self):
        """TaskTypeの値が重複していないことを確認"""
        values = [t.value for t in TaskType]
        assert len(values) == len(set(values))

    def test_task_type_count(self):
        """TaskTypeの数が正しいことを確認"""
        assert len(TaskType) == 4

    def test_task_type_daily(self):
        """Daily タイプの存在確認"""
        assert TaskType.Daily is not None
        assert TaskType.Daily.name == "Daily"

    def test_task_type_must(self):
        """Must タイプの存在確認"""
        assert TaskType.Must is not None
        assert TaskType.Must.name == "Must"

    def test_task_type_should(self):
        """Should タイプの存在確認"""
        assert TaskType.Should is not None
        assert TaskType.Should.name == "Should"

    def test_task_type_could(self):
        """Could タイプの存在確認"""
        assert TaskType.Could is not None
        assert TaskType.Could.name == "Could"


class TestTask:
    """Task dataclass のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        task = Task()
        assert task.name == ""
        assert task.task_type == TaskType.Daily
        assert task.is_completed is False

    def test_with_arguments(self):
        """引数を指定してインスタンス化できることを確認"""
        task = Task(
            name="テストタスク",
            task_type=TaskType.Must,
            is_completed=True,
        )
        assert task.name == "テストタスク"
        assert task.task_type == TaskType.Must
        assert task.is_completed is True

    def test_with_partial_arguments(self):
        """一部の引数のみ指定してインスタンス化できることを確認"""
        task = Task(name="部分的なタスク")
        assert task.name == "部分的なタスク"
        assert task.task_type == TaskType.Daily
        assert task.is_completed is False

    def test_task_type_assignment(self):
        """各TaskTypeを正しく設定できることを確認"""
        for task_type in TaskType:
            task = Task(task_type=task_type)
            assert task.task_type == task_type

    def test_is_completed_true(self):
        """is_completedをTrueに設定できることを確認"""
        task = Task(is_completed=True)
        assert task.is_completed is True

    def test_is_completed_false(self):
        """is_completedをFalseに設定できることを確認"""
        task = Task(is_completed=False)
        assert task.is_completed is False

    def test_task_with_sample_fixture(self, sample_task):
        """フィクスチャを使用したテスト"""
        assert sample_task.name == "サンプルタスク"
        assert sample_task.task_type == TaskType.Must
        assert sample_task.is_completed is False

    def test_task_equality(self):
        """同じ値を持つタスクが等しいことを確認（dataclassの比較）"""
        task1 = Task(name="タスク", task_type=TaskType.Must, is_completed=False)
        task2 = Task(name="タスク", task_type=TaskType.Must, is_completed=False)
        assert task1 == task2

    def test_task_inequality(self):
        """異なる値を持つタスクが等しくないことを確認"""
        task1 = Task(name="タスク1", task_type=TaskType.Must, is_completed=False)
        task2 = Task(name="タスク2", task_type=TaskType.Must, is_completed=False)
        assert task1 != task2
