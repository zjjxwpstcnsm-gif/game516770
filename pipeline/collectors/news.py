import feedparser
from datetime import datetime,timezone,date
from pipeline.common import now
from pipeline.normalizers.news import make_news,rss_date

def collect_news(http,sources,games):
    records=[];statuses=[]
    for s in sources:
        if not s.get('enabled',True):continue
        try:
            added=[]
            if s['id']=='steam_news':
                candidates=[g for g in games if g.get('steam_app_id')]
                limit=max(1,min(20,s.get('max_apps',8)))
                rest=candidates[1:];offset=date.today().toordinal()%len(rest) if rest else 0
                selected=candidates[:1]+(rest[offset:]+rest[:offset])[:limit-1]
                for g in selected:
                    if not g.get('steam_app_id'):continue
                    j=http.get(s['url'],params={'appid':g['steam_app_id'],'count':15,'maxlength':600,'feeds':'steam_community_announcements'},timeout=s.get('timeout',20),interval_seconds=s.get('interval_seconds',2)).json()
                    for n in j.get('appnews',{}).get('newsitems',[]):
                        published_at=datetime.fromtimestamp(n['date'],timezone.utc).isoformat() if n.get('date') else None
                        added.append(make_news(n['title'],n['url'],s['name'],published_at,now(),games,n.get('contents',''),True,s['credibility']))
            else:
                r=http.get(s['url'],check_robots=True,timeout=s.get('timeout',20),interval_seconds=s.get('interval_seconds',2));feed=feedparser.parse(r.content)
                if not feed.entries:raise ValueError('RSS has no parseable entries')
                for n in feed.entries[:40]:
                    if not n.get('link') or not n.get('title'):continue
                    added.append(make_news(n.title,n.link,s['name'],rss_date(n),now(),games,n.get('summary',''),s['category']=='official',s['credibility']))
            records.extend(added);statuses.append({'id':s['id'],'name':s['name'],'status':'ok','checked_at':now(),'records':len(added),'url':s['url'],'error':None})
        except Exception as e:
            records.extend(added)
            statuses.append({'id':s['id'],'name':s['name'],'status':'error','checked_at':now(),'records':len(added),'url':s['url'],'error':type(e).__name__+': '+str(e)[:180]})
    return records,statuses
