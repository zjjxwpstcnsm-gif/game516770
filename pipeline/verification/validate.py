from datetime import date,datetime
from pipeline.models import News,Price,Event,Signal,Payload

def validate_payload(data):
    Payload.model_validate(data)
    if data.get('schema_version')!='1.0':raise ValueError('unknown schema')
    seen=set()
    for n in data['news']:
        News.model_validate(n)
        if n['id'] in seen:raise ValueError('duplicate news ID')
        seen.add(n['id'])
    event_ids=set(); game_ids={g['id'] for g in data['games']}
    for e in data['events']:
        Event.model_validate(e)
        if e['id'] in event_ids or e['game_id'] not in game_ids:raise ValueError('invalid event identity')
        event_ids.add(e['id'])
    for etf in data['etfs']:
        ds=[]
        for p in etf['prices']:
            Price.model_validate(p);ds.append(p['date'])
            if p['high']<max(p['open'],p['close']) or p['low']>min(p['open'],p['close']):raise ValueError('invalid OHLC')
        if ds!=sorted(set(ds)):raise ValueError('price dates not sorted unique')
        if ds and ds[-1]>data['generated_at'][:10]:raise ValueError('future price')
    for s in data['signals']:Signal.model_validate(s)
    return True
