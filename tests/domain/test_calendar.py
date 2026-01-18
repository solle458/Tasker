"""
domain/models/calendar.py のテスト
"""

from datetime import datetime

from src.domain.models.calendar import Event, Calendar


class TestEvent:
    """Event dataclass のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        event = Event()
        assert event.name == ""
        assert isinstance(event.start, datetime)
        assert isinstance(event.end, datetime)
        assert event.description == ""

    def test_with_arguments(self):
        """引数を指定してインスタンス化できることを確認"""
        start_time = datetime(2026, 1, 18, 10, 0, 0)
        end_time = datetime(2026, 1, 18, 11, 0, 0)
        event = Event(
            name="会議",
            start=start_time,
            end=end_time,
            description="週次ミーティング",
        )
        assert event.name == "会議"
        assert event.start == start_time
        assert event.end == end_time
        assert event.description == "週次ミーティング"

    def test_with_partial_arguments(self):
        """一部の引数のみ指定してインスタンス化できることを確認"""
        event = Event(name="イベント名のみ")
        assert event.name == "イベント名のみ"
        assert event.description == ""

    def test_datetime_default_factory(self):
        """datetime.nowがdefault_factoryとして機能することを確認"""
        event1 = Event()
        event2 = Event()
        # 各インスタンスが独立したdatetimeを持つ（共有されない）
        # 注意: ミリ秒単位で異なる可能性があるため、同じ秒内であることを確認
        assert event1.start is not event2.start  # オブジェクト参照が異なる

    def test_event_with_sample_fixture(self, sample_event):
        """フィクスチャを使用したテスト"""
        assert sample_event.name == "サンプルイベント"
        assert sample_event.description == "サンプルイベントの説明"

    def test_event_equality(self):
        """同じ値を持つイベントが等しいことを確認（dataclassの比較）"""
        start_time = datetime(2026, 1, 18, 10, 0, 0)
        end_time = datetime(2026, 1, 18, 11, 0, 0)
        event1 = Event(name="会議", start=start_time, end=end_time, description="説明")
        event2 = Event(name="会議", start=start_time, end=end_time, description="説明")
        assert event1 == event2

    def test_event_inequality(self):
        """異なる値を持つイベントが等しくないことを確認"""
        start_time = datetime(2026, 1, 18, 10, 0, 0)
        end_time = datetime(2026, 1, 18, 11, 0, 0)
        event1 = Event(name="会議1", start=start_time, end=end_time)
        event2 = Event(name="会議2", start=start_time, end=end_time)
        assert event1 != event2


class TestCalendar:
    """Calendar dataclass のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        calendar = Calendar()
        assert calendar.name == ""
        assert calendar.events == []

    def test_with_arguments(self):
        """引数を指定してインスタンス化できることを確認"""
        event1 = Event(name="イベント1")
        event2 = Event(name="イベント2")
        calendar = Calendar(
            name="マイカレンダー",
            events=[event1, event2],
        )
        assert calendar.name == "マイカレンダー"
        assert len(calendar.events) == 2
        assert calendar.events[0].name == "イベント1"
        assert calendar.events[1].name == "イベント2"

    def test_with_partial_arguments(self):
        """一部の引数のみ指定してインスタンス化できることを確認"""
        calendar = Calendar(name="カレンダー名のみ")
        assert calendar.name == "カレンダー名のみ"
        assert calendar.events == []

    def test_events_mutable_default_not_shared(self):
        """eventsのミュータブルなデフォルト値が共有されないことを確認"""
        calendar1 = Calendar()
        calendar2 = Calendar()

        calendar1.events.append(Event(name="新イベント"))

        # calendar2のeventsには影響しないことを確認
        assert len(calendar1.events) == 1
        assert len(calendar2.events) == 0
        assert calendar1.events != calendar2.events

    def test_calendar_with_sample_fixture(self, sample_calendar):
        """フィクスチャを使用したテスト"""
        assert sample_calendar.name == "サンプルカレンダー"
        assert len(sample_calendar.events) == 1
        assert sample_calendar.events[0].name == "サンプルイベント"

    def test_calendar_equality(self):
        """同じ値を持つカレンダーが等しいことを確認（dataclassの比較）"""
        calendar1 = Calendar(name="カレンダー", events=[])
        calendar2 = Calendar(name="カレンダー", events=[])
        assert calendar1 == calendar2

    def test_calendar_inequality(self):
        """異なる値を持つカレンダーが等しくないことを確認"""
        calendar1 = Calendar(name="カレンダー1", events=[])
        calendar2 = Calendar(name="カレンダー2", events=[])
        assert calendar1 != calendar2

    def test_add_event_to_calendar(self):
        """カレンダーにイベントを追加できることを確認"""
        calendar = Calendar(name="テストカレンダー")
        event = Event(name="新しいイベント")
        calendar.events.append(event)

        assert len(calendar.events) == 1
        assert calendar.events[0].name == "新しいイベント"
