from pipeline.events.discovery import parse_release_date, heat_assessment, enrich_games_and_events


def test_date_precision_never_invented():
    for raw in ['Q4 2026', '2026', 'November 2026', '即将推出', 'Coming soon', None, '2026 年 2 月 30 日']:
        assert parse_release_date(raw) is None
    assert parse_release_date('2026 年 11 月 4 日') == '2026-11-04'
    assert parse_release_date('20 Aug, 2024') == '2024-08-20'


def test_sss_requires_multiple_evidence_types():
    game = {'id': 'x', 'name': 'Amazing SSS game'}
    assert heat_assessment(game, [])['heat_grade'] == 'B'
    reviews = {'total_reviews': 500000, 'positive_ratio': .98}
    assert heat_assessment(game, [], reviews)['heat_grade'] != 'SSS'
    news = [{'game_ids': ['x'], 'source_type': 'media', 'url': f'https://{n}.com/a'} for n in ['a', 'b', 'c']]
    assert heat_assessment(game, news, reviews)['heat_grade'] == 'SS'
    game['verified_sales'] = {'copies': 10000000, 'verification_status': 'verified', 'source_url': 'https://official.test/sales', 'as_of': '2026-11-02'}
    assert heat_assessment(game, news, reviews)['heat_grade'] == 'SSS'


def test_duplicate_media_urls_not_multiple_publishers():
    news = [{'game_ids': ['x'], 'source_type': 'media', 'url': f'https://one.test/{i}'} for i in range(20)]
    result = heat_assessment({'id': 'x'}, news)
    assert result['heat_evidence']['media_publishers'] == ['one.test']


class Response:
    def __init__(self, data): self.data = data
    def json(self): return self.data


class HTTP:
    def get(self, url, params=None):
        if 'appreviews' in url:
            return Response({'success': 1, 'query_summary': {'total_reviews': 100, 'total_positive': 90, 'total_negative': 10}})
        return Response({'123': {'success': True, 'data': {'type': 'game', 'developers': ['Studio'], 'publishers': ['Pub'], 'release_date': {'date': '2026 年 11 月 4 日', 'coming_soon': True}}}})


def test_discovered_future_event_has_unknown_announcement():
    games, events, statuses = enrich_games_and_events(HTTP(), [{'id': 'x', 'name': 'X', 'steam_app_id': 123}], [], '2026-11-02T18:00:00+08:00')
    assert events[0]['event_date'] == '2026-11-04'
    assert events[0]['announced_at'] is None
    assert events[0]['first_seen_at'] == '2026-11-02T18:00:00+08:00'
    assert events[0]['status'] == 'announced'
    assert games[0]['steam_reviews']['total_reviews'] == 100
    assert all(s['status'] == 'ok' for s in statuses)


def test_release_id_stable_when_date_changes():
    _, events, _ = enrich_games_and_events(HTTP(), [{'id': 'x', 'name': 'X', 'steam_app_id': 123}], [], '2026-11-02T18:00:00+08:00')
    _, again, _ = enrich_games_and_events(HTTP(), [{'id': 'x', 'name': 'X', 'steam_app_id': 123}], [], '2026-11-03T18:00:00+08:00')
    assert events[0]['id'] == again[0]['id']


def test_past_steam_local_date_cannot_replace_beijing_release():
    class PastHTTP(HTTP):
        def get(self, url, params=None):
            if 'appreviews' in url: return super().get(url, params)
            return Response({'123': {'success': True, 'data': {'type': 'game', 'release_date': {'date': '2024 年 8 月 19 日', 'coming_soon': False}}}})
    games, events, _ = enrich_games_and_events(PastHTTP(), [{'id': 'x', 'name': 'X', 'steam_app_id': 123}], [], '2026-11-02T18:00:00+08:00')
    assert events == []
    assert games[0]['steam_display_release_date'] == '2024-08-19'
    assert 'release_date' not in games[0]
