"""Fail closed if market data cannot support a current signal."""
from pipeline.signals.engine import generate_signal
from pipeline.common import config


def test_future_market_date_never_produces_action_reference():
    etf = {'code': '516770', 'as_of': '2026-11-03',
           'data_cutoff_time': '2026-11-03T15:00:00+08:00',
           'prices': [{'close': 1.0}] * 80,
           'indicators': {'ma5': 1.0, 'ma20': 1.0}}
    result = generate_signal(etf, [], [], config('strategy'), '2026-11-02T18:00:00+08:00')
    assert result['signal'] == '数据不足，暂停判断'
    assert result['signal_score'] is None


def test_unknown_calendar_or_completed_session_is_not_fresh_market_evidence():
    etf = {'code': '516770', 'as_of': '2026-10-29',
           'data_cutoff_time': '2026-10-29T15:00:00+08:00',
           'prices': [{'close': 1.0}] * 80,
           'indicators': {'ma5': 1.0, 'ma20': 1.0}}
    result = generate_signal(etf, [], [], config('strategy'), '2026-11-02T18:00:00+08:00')
    assert result['signal'] == '数据不足，暂停判断'
