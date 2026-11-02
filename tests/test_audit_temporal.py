"""Independent regressions for temporal truth and malformed production inputs."""
from pipeline.events.lifecycle import known_as_of, merge_event
from pipeline.normalizers.news import rss_date


def test_knowledge_cutoff_compares_instants_not_iso_text():
    event = {'announced_at': '2026-06-01T10:00:00+08:00', 'history': []}
    assert known_as_of(event, '2026-06-01T03:00:00+00:00')


def test_knowledge_not_available_before_real_instant():
    event = {'announced_at': '2026-06-01T03:00:00+00:00', 'history': []}
    assert not known_as_of(event, '2026-06-01T10:00:00+08:00')


def test_unknown_announcement_is_not_backtest_evidence():
    assert not known_as_of({'announced_at': None}, '2026-11-02T10:00:00+08:00')


def test_rss_missing_or_naive_dates_are_not_fabricated():
    assert rss_date({}) is None
    assert rss_date({'published': '2026-01-01T10:00:00'}) is None


def test_event_revision_retains_original_discovery_and_previous_date():
    old = {'event_date': '2026-09-09', 'status': 'confirmed', 'first_seen_at': '2026-01-01T00:00:00+08:00', 'source_urls': ['https://example.com/first'], 'history': []}
    new = {**old, 'event_date': '2026-10-29', 'first_seen_at': '2026-06-02T00:00:00+08:00', 'source_urls': ['https://example.com/delay']}
    result = merge_event(old, new)
    assert result['first_seen_at'] == old['first_seen_at']
    assert result['history'][-1]['previous_event_date'] == '2026-09-09'
    assert set(result['source_urls']) == {'https://example.com/first', 'https://example.com/delay'}
