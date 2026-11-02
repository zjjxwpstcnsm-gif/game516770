from pipeline.backtest.study import replay_signals, event_study

PRICES = [
    {'date':'2026-10-29','open':1.0,'close':1.0,'volume':100},
    {'date':'2026-10-30','open':1.0,'close':1.0,'volume':100},
    {'date':'2026-11-02','open':1.001,'close':1.001,'volume':100},
]


def signal(day, label, recorded):
    return {'signal_date':day, 'signal':label, 'data_cutoff_time':day+'T15:00:00+08:00', 'recorded_at':recorded}


def test_late_recorded_signal_cannot_execute_before_it_existed():
    s=signal('2026-10-29','分批建仓候选','2026-10-30T10:00:00+08:00')
    assert replay_signals(PRICES,[s])['trades'] == []


def test_unknown_recorded_timestamp_excluded_from_replay():
    s=signal('2026-10-29','分批建仓候选',None)
    assert replay_signals(PRICES,[s])['trades'] == []


def test_win_rate_accounts_for_roundtrip_cost():
    signals=[signal('2026-10-29','分批建仓候选','2026-10-29T18:00:00+08:00'),
             signal('2026-10-30','减仓风险','2026-10-30T18:00:00+08:00')]
    result=replay_signals(PRICES, signals, fee_bps=5, slippage_bps=5)
    assert result['sample_size']==1
    assert result['win_rate']==0.0
    assert result['cumulative_return']<0


def test_future_event_windows_are_not_filled_or_extrapolated():
    event={'id':'e','title':'event','game_id':'g','event_date':'2026-10-30','source_urls':['https://example.com']}
    result=event_study(PRICES,event)
    assert not result['complete_window']
    assert all(p['return'] is None for p in result['points'] if p['offset']>=3)
