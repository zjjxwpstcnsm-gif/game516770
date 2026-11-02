import re
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from pipeline.common import clean_text,canonical_url,stable_id
from pipeline.models import News

def match_games(title,games):
    t=title.casefold();return [g['id'] for g in games if any(a.casefold() in t for a in [g['name'],*g.get('aliases',[])])]
def category(title):
    t=title.casefold()
    for k,words in {'delay':['delay','postpon','延期'],'sales':['million copies','sales','销量'],'demo':['demo','试玩'],'preorder':['pre-order','preorder','预购'],'release':['release','launch','发售'],'announcement':['announce','revealed','官宣']}.items():
        if any(w in t for w in words):return k
    return 'industry'
def rss_date(entry):
    for key in ('published','updated'):
        if entry.get(key):
            try:
                d=parsedate_to_datetime(entry[key]);return d.isoformat() if d.tzinfo else None
            except (ValueError,TypeError):
                try:
                    d=datetime.fromisoformat(entry[key].replace('Z','+00:00'));return d.isoformat() if d.tzinfo else None
                except ValueError:pass
    return None

def make_news(title,url,source,published,collected,games,summary='',official=False,score=75):
    url=canonical_url(url);limits=['仅使用公开订阅摘要，未存储网页全文']
    if published is None:limits.append('来源未提供可靠发布时间')
    # A publisher RSS confirms that the article exists, not every underlying claim.
    return News(id=stable_id(url),title=clean_text(title),url=url,source=source,published_at=published,collected_at=collected,game_ids=match_games(title,games),category=category(title),summary=clean_text(summary)[:500],verification_status='verified' if official else 'reported',credibility_score=score,limitations=limits,source_type='official' if official else 'media').model_dump()
