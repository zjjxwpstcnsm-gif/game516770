"""Evidence-dated economic-rights mapping; popularity alone creates no ownership."""
from datetime import datetime

def event_exposure(event, etf, as_of):
    today=as_of[:10]
    holdings={h['code']:h for h in etf.get('holdings',[]) if h.get('as_of','9999')<=today}
    matches=[]
    for link in event.get('company_links',[]):
        if link.get('relation') not in ('direct','indirect'):continue
        if link.get('verification_status')!='verified':continue
        if not link.get('source_url','').startswith('https://'):continue
        if not link.get('valid_from') or link['valid_from']>today:continue
        if link.get('valid_to') and link['valid_to']<today:continue
        code=link.get('stock_code');h=holdings.get(code)
        if not h:continue
        matches.append({**link,'holding_weight':h['weight'],'holdings_as_of':h['as_of'],'holdings_source':h.get('source_url')})
    # Deduplicate a company cited through multiple rights; never double-count weight.
    by_code={}
    for m in matches:
        old=by_code.get(m['stock_code'])
        if not old or m['relation']=='direct':by_code[m['stock_code']]=m
    matches=list(by_code.values())
    relation='direct' if any(m['relation']=='direct' for m in matches) else 'indirect' if matches else 'sentiment'
    return {'relation':relation,'evidence':matches,'verified_holding_weight':sum(m['holding_weight'] for m in matches) if matches else None,'holdings_as_of':etf.get('holdings_as_of'),'limitation':'披露期权重不等于利润敏感度；缺少明确权益证据只讨论行业情绪。'}
