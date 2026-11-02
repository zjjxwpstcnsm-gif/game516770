from pipeline.common import stable_id
from pipeline.models import Event

def merge_event(old,new):
    if not old:return new
    tracked=('event_date','status')
    history=list(old.get('history',[]))
    if any(old.get(k)!=new.get(k) for k in tracked):
        history.append({'observed_at':new['first_seen_at'],'previous_event_date':old.get('event_date'),'previous_status':old.get('status'),'new_event_date':new.get('event_date'),'new_status':new.get('status'),'source_urls':new['source_urls']})
    return {**new,'first_seen_at':old['first_seen_at'],'history':history,'source_urls':sorted(set(old['source_urls']+new['source_urls'])),'source_ids':sorted(set(old.get('source_ids',[])+new.get('source_ids',[])))}

def build_events(news,games,verified,previous,observed):
    out={x['id']:x for x in previous};game_map={g['id']:g for g in games}
    for n in news:
        if n['category']=='industry':continue
        for gid in n['game_ids']:
            # No date inference from title: source publication is NOT event date.
            eid=stable_id(gid,n['category'],n['url'])
            event=Event(id=eid,game_id=gid,title=n['title'],type=n['category'],importance=game_map[gid].get('heat_grade','B'),announced_at=n['published_at'],first_seen_at=observed,status='announced' if n['source_type']=='official' else 'rumored',source_urls=[n['url']],source_ids=[n['id']],verification_note='来源已发布；具体发生时间未核实，不进入未来日历').model_dump()
            out[eid]=merge_event(out.get(eid),event)
    for v in verified:
        event=Event(**{**v,'first_seen_at':v.get('first_seen_at',observed)}).model_dump()
        out[event['id']]=merge_event(out.get(event['id']),event)
    # Merge same game/type/date only where a date has actually been verified.
    canonical={}
    for e in out.values():
        key=(e['game_id'],e['type'],e['event_date']) if e['event_date'] and e['status'] in ('confirmed','completed') else (e['id'],)
        if key in canonical:
            prev=canonical[key];prev['source_urls']=sorted(set(prev['source_urls']+e['source_urls']));prev['source_ids']=sorted(set(prev.get('source_ids',[])+e.get('source_ids',[])))
        else:canonical[key]=e
    return list(canonical.values())

def known_as_of(event,cutoff):
    from datetime import datetime
    if not event.get('announced_at'):return False
    try:
        a=datetime.fromisoformat(event['announced_at'].replace('Z','+00:00')); c=datetime.fromisoformat(cutoff.replace('Z','+00:00'))
        if a.tzinfo is None or c.tzinfo is None:return False
        if a>c:return False
        # Revision history without precise point-in-time availability fails closed.
        for h in event.get('history',[]):
            t=h.get('observed_at')
            if not t or datetime.fromisoformat(t.replace('Z','+00:00'))>c:return False
        return True
    except (ValueError,TypeError):return False
