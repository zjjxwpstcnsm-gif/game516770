"""Conservative Steam release discovery and evidence-based (not investment) heat.

Store dates are regional day precision. Publication time is unknown, so records
cannot be replayed as historical known information. SSS requires independent
sales evidence plus review scale and multiple media publishers.
"""
from datetime import date, datetime
import re
from urllib.parse import urlsplit
from pipeline.common import stable_id


def parse_release_date(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    # Do not infer a day from a month, quarter, year or 'coming soon'.
    m = re.fullmatch(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', value)
    if m:
        try:
            return date(*map(int, m.groups())).isoformat()
        except ValueError:
            return None
    for fmt in ('%Y-%m-%d', '%d %b, %Y', '%b %d, %Y', '%d %B, %Y', '%B %d, %Y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def heat_assessment(game, news, review_metrics=None):
    reviews = review_metrics or {}
    count = reviews.get('total_reviews')
    positive = reviews.get('positive_ratio')
    media = {urlsplit(n.get('url', '')).hostname for n in news
             if game['id'] in n.get('game_ids', []) and n.get('source_type') == 'media'
             and n.get('url')}
    media.discard(None)
    # Explicit independently verified sales data only. Never infer from owners,
    # review multipliers, concurrent players or a newspaper headline.
    sales_evidence = game.get('verified_sales') or {}
    sales = sales_evidence.get('copies') if (sales_evidence.get('verification_status') == 'verified'
             and sales_evidence.get('source_url') and sales_evidence.get('as_of')) else None
    review_score = 0 if count is None else (40 if count >= 100000 else 30 if count >= 10000 else 20 if count >= 1000 else 10 if count >= 100 else 0)
    media_score = min(len(media) * 10, 30)
    sales_score = 30 if sales is not None and sales >= 10000000 else 20 if sales is not None and sales >= 1000000 else 0
    score = review_score + media_score + sales_score
    if count is None and not media and sales is None:
        grade, score = 'B', None
    elif count is not None and count >= 100000 and positive is not None and positive >= .8 and len(media) >= 3 and sales_score == 30:
        grade = 'SSS'
    elif review_score >= 30 and len(media) >= 2:
        grade = 'SS'
    elif review_score >= 20 or len(media) >= 3:
        grade = 'S'
    elif review_score >= 10 or len(media) >= 1:
        grade = 'A'
    else:
        grade = 'B'
    return {'heat_grade': grade, 'heat_score': score,
            'heat_basis': '启发式热度，非投资评级或预测概率；SSS 需销量、评价规模及多家媒体三类证据',
            'heat_evidence': {'review_count': count, 'positive_ratio': positive,
                'media_publishers': sorted(media), 'verified_sales': sales,
                'review_source': reviews.get('source_url'), 'review_as_of': reviews.get('as_of'),
                'sales_source': sales_evidence.get('source_url') if sales is not None else None,
                'components': {'review_scale': review_score, 'media_breadth': media_score, 'verified_sales': sales_score},
                'missing': [name for name, missing in [('verified_sales', sales is None), ('review_count', count is None), ('media_coverage', not media)] if missing]}}


def enrich_games_and_events(http, games, news, at, max_apps=8):
    enriched = [dict(g) for g in games]
    events, statuses = [], []
    candidates = [g for g in enriched if g.get('steam_app_id')]
    # Rotating bounded batch, while always prioritizing original watchlist game.
    limit = max(0, min(int(max_apps), 20))
    selected = candidates[:1]
    rest = candidates[1:]
    if rest and limit > 1:
        offset = date.fromisoformat(at[:10]).toordinal() % len(rest)
        selected += (rest[offset:] + rest[:offset])[:limit - 1]
    selected = selected[:limit]
    selected_ids = {g['id'] for g in selected}
    for g in enriched:
        # Preserve previous verified metrics on skipped days, with source as_of.
        metrics = g.get('steam_reviews')
        if g['id'] in selected_ids:
            app = g['steam_app_id']
            source = f'https://store.steampowered.com/app/{app}/'
            try:
                response = http.get('https://store.steampowered.com/api/appdetails', params={'appids': app, 'cc': 'cn', 'l': 'schinese'}).json()
                item = response.get(str(app), {})
                if not item.get('success') or not isinstance(item.get('data'), dict):
                    raise ValueError('Steam appdetails unavailable')
                details = item['data']
                if details.get('type') != 'game':
                    raise ValueError('Steam entity is not a game')
                rd = details.get('release_date') or {}
                exact = parse_release_date(rd.get('date'))
                g.update({'developer': ', '.join(details.get('developers', [])) or g.get('developer'),
                          'publisher': ', '.join(details.get('publishers', [])) or g.get('publisher'),
                          'release_date_raw': rd.get('date'), 'steam_display_release_date': exact,
                          'release_date_precision': 'day' if exact else 'unknown',
                          'release_source': source, 'release_checked_at': at,
                          'release_coming_soon': rd.get('coming_soon')})
                if exact and rd.get('coming_soon') is True and exact >= at[:10]:
                    events.append({'id': stable_id(g['id'], 'release', 'steam-store'), 'game_id': g['id'],
                        'title': g['name'] + ' · Steam 发售日期', 'type': 'release', 'importance': g.get('heat_grade', 'B'),
                        'event_date': exact, 'announced_at': None, 'first_seen_at': at,
                        'status': 'announced', 'source_urls': [source], 'source_ids': [],
                        'company_links': [], 'history': [],
                        'verification_note': 'Steam 商店显示的计划日期，日精度、原始时区未知（可能与北京时间相差一天）；须以官方精确时刻复核。首次公布时间未知，不用于历史已知信息回放。'})
                statuses.append({'id': f'steam_details_{app}', 'name': g['name'] + ' 官方日期', 'status': 'ok', 'checked_at': at, 'records': 1, 'url': source, 'error': None})
            except Exception as exc:
                statuses.append({'id': f'steam_details_{app}', 'name': g['name'] + ' 官方日期', 'status': 'error', 'checked_at': at, 'records': 0, 'url': source, 'error': type(exc).__name__})
            review_url = f'https://store.steampowered.com/appreviews/{app}'
            try:
                result = http.get(review_url, params={'json': 1, 'language': 'all', 'purchase_type': 'all', 'num_per_page': 0}).json()
                q = result.get('query_summary') or {}
                total, pos, neg = q.get('total_reviews'), q.get('total_positive'), q.get('total_negative')
                if result.get('success') != 1 or not all(isinstance(x, int) and x >= 0 for x in (total, pos, neg)) or pos + neg != total:
                    raise ValueError('Invalid Steam review summary')
                metrics = {'total_reviews': total, 'positive_ratio': pos / total if total else None, 'source_url': review_url, 'as_of': at}
                g['steam_reviews'] = metrics
                statuses.append({'id': f'steam_reviews_{app}', 'name': g['name'] + ' 评价数据', 'status': 'ok', 'checked_at': at, 'records': 1, 'url': review_url, 'error': None})
            except Exception as exc:
                statuses.append({'id': f'steam_reviews_{app}', 'name': g['name'] + ' 评价数据', 'status': 'error', 'checked_at': at, 'records': 0, 'url': review_url, 'error': type(exc).__name__})
        g.update(heat_assessment(g, news, metrics))
    grades = {g['id']: g['heat_grade'] for g in enriched}
    for event in events:
        event['importance'] = grades[event['game_id']]
    return enriched, events, statuses
