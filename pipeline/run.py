"""Idempotent collection and atomic validated publication. python -m pipeline.run"""
import argparse,json
from pathlib import Path
from datetime import datetime,date,timedelta
from pipeline.common import ROOT,config,now,load_json,atomic_json,stable_id
from pipeline.collectors.http import PublicHTTP
from pipeline.collectors.news import collect_news
from pipeline.collectors.prices import collect_prices,NAMES
from pipeline.collectors.market_context import calendar_context,collect_benchmark,collect_holdings
from pipeline.events.discovery import enrich_games_and_events
from pipeline.deduplication.merge import merge_news
from pipeline.events.lifecycle import build_events
from pipeline.etf.indicators import indicators
from pipeline.signals.engine import generate_signal
from pipeline.backtest.study import event_study,replay_signals
from pipeline.verification.validate import validate_payload
from pipeline.reports.daily import daily_report

def research_events(research,at):
    out=[]
    for e in research.get('game_evidence',[]):
        if e['status']!='confirmed':continue
        d=e.get('published_date') if e['type']=='release_date_announced' else e.get('event_at') or e.get('event_date')
        if not d:continue
        kind='release' if e['type']=='release_date_revision' else e['type']
        # Stable release identity preserves revisions. Only final release source is canonical.
        if e['type']=='release_date_revision':continue
        history=[]
        if e['game_id']=='phantom-blade-zero' and kind=='release':
            revision=next((x for x in research['game_evidence'] if x['type']=='release_date_revision'),None)
            if revision:history=[{'observed_at':at,'announced_date':revision['published_date'],'date_precision':'day','previous_event_date':revision['old_event_date'],'previous_status':'announced','new_event_date':revision['event_date'],'new_status':'confirmed','source_urls':[revision['url']]}]
        out.append({'id':stable_id(e['game_id'],kind),'game_id':e['game_id'],'title':('黑神话：悟空' if e['game_id']=='black-myth-wukong' else '影之刃零')+' · '+{'release':'正式发售','preorder':'开放预购','gameplay_showcase':'实机演示','release_date_announced':'发售日期公布'}.get(kind,kind),'type':kind,'importance':'S','event_date':d,'announced_at':e.get('published_at'),'first_seen_at':at,'status':'confirmed','source_urls':[e['url'],*e.get('corroborating_urls',[])],'history':history,'verification_note':e.get('note','官方来源核验；日级公布日期不伪造精确发布时间')+('；公布日期 '+e['published_date'] if e.get('published_date') else '')})
    return out

def discover_games(http,games,statuses):
    """Steam featured categories publicly expose rotating real app entities."""
    try:
        j=http.get('https://store.steampowered.com/api/featuredcategories',params={'cc':'cn','l':'schinese'}).json();known={g.get('steam_app_id') for g in games};added=0
        for kind in ('coming_soon','top_sellers','new_releases'):
            for x in j.get(kind,{}).get('items',[])[:8]:
                if x.get('id') in known or not x.get('name'):continue
                known.add(x['id']);games.append({'id':'steam-'+str(x['id']),'name':x['name'],'aliases':[x['name']],'developer':None,'publisher':None,'official_url':f"https://store.steampowered.com/app/{x['id']}/",'steam_app_id':x['id'],'heat_grade':'B','heat_score':None,'heat_basis':'Steam 公开推荐列表发现；缺少多指标证据，不自动升格','investment_relation':'无明确关联','discovery_source':'https://store.steampowered.com/api/featuredcategories','discovered_at':now()});added+=1
        statuses.append({'id':'steam_discovery','name':'Steam 动态游戏发现','status':'ok','records':added,'checked_at':now(),'url':'https://store.steampowered.com/api/featuredcategories','error':None})
    except Exception as e:statuses.append({'id':'steam_discovery','name':'Steam 动态游戏发现','status':'error','records':0,'checked_at':now(),'error':type(e).__name__})
    return games

def run(out=ROOT/'public/data',offline=False):
    out=Path(out);at=now();old=load_json(out/'latest.json',{});settings=config('strategy');watch=config('watchlist');research=load_json(ROOT/'research.json',{})
    games=watch['games'];statuses=[];http=PublicHTTP()
    if not offline:games=discover_games(http,games,statuses)
    # Persist previously discovered entities, never lose their history.
    gm={g['id']:g for g in old.get('games',[])}
    for g in games:
        prior=gm.get(g['id'],{});merged={**prior,**g}
        if prior.get('heat_evidence'):
            for key in ('heat_grade','heat_score','heat_basis'):merged[key]=prior.get(key,g.get(key))
        gm[g['id']]=merged
    games=list(gm.values())
    news_new,ns=collect_news(http,config('sources')['sources'],games) if not offline else ([],[]);statuses+=ns
    news=merge_news(old.get('news',[]),news_new)
    games,discovered_events,discovery_status=enrich_games_and_events(http,games,news,at) if not offline else (games,[],[])
    statuses.extend(discovery_status)
    previous_events=old.get('events',[])
    for e in previous_events:
        if e.get('verification_note','').startswith('Steam 中国区中文商店日级计划日期'):
            e['history']=e.get('history',[])+[{'observed_at':at,'previous_event_date':e.get('event_date'),'previous_status':e['status'],'new_event_date':None,'new_status':'announced','reason':'纠正商店本地化日期的时区歧义；不作为已核实北京时间'}]
            e.update(event_date=None,status='announced',verification_note='商店本地化日期存在时区歧义，已撤销精确日期并保留修订记录')
    events=build_events(news,games,watch.get('verified_events',[])+research_events(research,at)+discovered_events,previous_events,at)
    calendar=calendar_context(at)
    benchmark=collect_benchmark(http,at) if not offline else {'status':'unavailable','prices':[],'as_of':None}
    if benchmark['status']!='ok':
        prior_benchmark=next((e.get('benchmark') for e in old.get('etfs',[]) if e.get('benchmark',{}).get('prices')),None)
        if prior_benchmark:benchmark={**prior_benchmark,'status':'historical_snapshot','error':benchmark.get('error','current_collection_unavailable')}
    statuses.append({'id':'benchmark','name':'沪深300市场对照','status':'ok' if benchmark['status']=='ok' else 'error','checked_at':now(),'records':len(benchmark['prices']),'url':benchmark.get('source_url'),'error':benchmark.get('error')})
    etfs=[]
    for code in settings['etfs']:
        previous=next((x for x in old.get('etfs',[]) if x['code']==code),{})
        prices,meta=collect_prices(http,code) if not offline else ([],{'errors':['offline run']})
        fetched=bool(prices)
        if not prices:prices=previous.get('prices',[]);meta={**previous,'errors':meta['errors']}
        elif previous.get('source')==meta.get('source') and previous.get('adjustment')==meta.get('adjustment') and previous.get('volume_unit')==meta.get('volume_unit'):
            prices=[*previous.get('prices',[]),*prices]
        # Never join price providers with incompatible volume units or adjustment conventions.
        prices=sorted({p['date']:p for p in prices if p['date']<=(calendar.get('expected_last_session') or at[:10])}.values(),key=lambda p:p['date'])
        asof=prices[-1]['date'] if prices else None;last=prices[-1] if prices else {};prev=prices[-2] if len(prices)>1 else {}
        etf={'code':code,'name':NAMES[code],'index_name':'中证动漫游戏指数','index_code':'930901','price_type':'exchange_close','as_of':asof,'data_cutoff_time':asof+'T15:00:00+08:00' if asof else None,'source':meta.get('source'),'source_url':meta.get('source_url'),'adjustment':'unadjusted','volume_unit':meta.get('volume_unit'),'latest':{'close':last.get('close'),'change_pct':last['close']/prev['close']-1 if prev else None,'volume':last.get('volume'),'amount':last.get('amount')},'indicators':indicators(prices),'prices':prices,'holdings':[],'holdings_as_of':None,'holdings_status':'缺少已核验日期的当前持仓权重','collection_status':'ok' if fetched else 'historical_snapshot' if prices else 'missing','limitations':['价格为场内未复权收盘价，非净值、非实时行情','历史持仓未核验，不计算直接收益权重',*([meta['limitation']] if meta.get('limitation') else [])]}
        holdings=collect_holdings(http,code,at) if not offline else {'status':'unavailable','holdings':[],'as_of':None}
        if holdings['status']!='ok' and previous.get('holdings'):
            holdings={**previous.get('holdings_evidence',{}),'holdings':previous['holdings'],'as_of':previous.get('holdings_as_of'),'status':'historical_snapshot','error':holdings.get('error','current_collection_unavailable')}
        etf.update(holdings=holdings['holdings'],holdings_as_of=holdings['as_of'],holdings_status=holdings['status'],holdings_evidence=holdings,calendar_verified=bool(calendar['verified'] and asof==calendar['expected_last_session']),calendar=calendar,benchmark_verified=bool(benchmark['status']=='ok' and benchmark['as_of']==asof),benchmark=benchmark,direct_relation_verified=False)
        statuses.append({'id':'holdings_'+code,'name':NAMES[code]+'持仓','status':'ok' if holdings['status']=='ok' else 'error','checked_at':now(),'records':len(holdings['holdings']),'url':holdings.get('source_url'),'error':holdings.get('error')})
        etfs.append(etf);statuses.append({'id':'prices_'+code,'name':NAMES[code]+'行情','status':'ok' if fetched else 'error','checked_at':at,'records':len(prices),'url':meta.get('source_url'),'error':'; '.join(meta.get('errors',[])) or None})
    signals=[{**generate_signal(e,events,games,settings,at),'recorded_at':at} for e in etfs]
    try:
        from pipeline.ai import AgnesClient
        evidence_records=list(news_new[:8])
        for e in etfs:
            if e['latest']['close'] is not None:
                evidence_records.append({'id':f"prices:{e['code']}:{e['as_of']}",'title':e['name']+' 已核验场内收盘价','url':e['source_url'],'source':e['source'],'date':e['as_of'],'value':e['latest']['close'],'metric':'exchange_close_unadjusted','evidence':{'indicators':e['indicators'],'holdings_as_of':e['holdings_as_of'],'price_type':e['price_type']}})
        for s in signals:
            evidence_records.append({'id':f"signal:{s['etf_code']}:{s['signal_date']}",'title':'规则引擎结论（AI 不得更改）：'+s['signal'],'source':'Game Alpha '+settings['version'],'date':s['signal_date'],'summary':'；'.join(s['reasons']+s['risks']),'evidence':{'signal':s['signal'],'score':s['signal_score'],'source_ids':s['source_ids'],'data_cutoff_time':s['data_cutoff_time']}})
        ai=AgnesClient(state_dir=out/'system/ai_cache').analyze(evidence_records,kind='daily_research').model_dump()
    except Exception as e:ai={'status':'failed','summary':None,'error':type(e).__name__}
    at=now()
    if ai['status']=='ok':
        summaries={sid:item['summary'] for item in ai.get('items',[]) for sid in item.get('source_ids',[])}
        for n in news:
            if n['id'] in summaries:n.update(summary=summaries[n['id']],summary_status='ai_validated',summary_language='zh-CN')
    studies=[]
    for etf in etfs:
        for event in events:
            if event['type']=='release' and event.get('event_date') and event['status'] in ('confirmed','completed'):
                s=event_study(etf['prices'],event,benchmark.get('prices',[]))
                if s:studies.append({**s,'etf_code':etf['code']})
    signal_history=load_json(out/'signals.json',[]);by_key={(s['signal_date'],s['etf_code']):s for s in signal_history}
    for s in signals:by_key[(s['signal_date'],s['etf_code'])]=s
    signal_history=list(by_key.values());report=daily_report(signals,news,events,at,ai)
    system={'status':'partial_failure' if any(s['status']=='error' for s in statuses) or ai['status']!='ok' else 'ok','generated_at':at,'last_success_at':at if statuses and all(s['status']=='ok' for s in statuses) and ai['status']=='ok' else (old.get('system',{}).get('last_success_at') if old.get('system',{}).get('status')=='ok' else None),'last_partial_success_at':at if any(s['status']=='ok' for s in statuses) else old.get('system',{}).get('last_partial_success_at'),'source_status':statuses,'strategy_version':settings['version'],'ai_status':ai['status'],'ai':ai,'last_ai_success_at':at if ai['status']=='ok' else old.get('system',{}).get('last_ai_success_at'),'latest_market_date':max((e['as_of'] for e in etfs if e['as_of']),default=None),'market_calendar_status':'已核验 2026 年上交所休市表；跨年及缺失应完成交易日时暂停判断','build_status':'pipeline_completed_pending_build'}
    latest={'schema_version':'1.0','generated_at':at,'timezone':'Asia/Shanghai','data_cutoff_time':max((e['data_cutoff_time'] for e in etfs if e['data_cutoff_time']),default=None),'news':news,'games':games,'events':events,'etfs':etfs,'signals':signals,'report':report,'system':system,'event_studies':studies,'backtest':replay_signals(etfs[0]['prices'],[s for s in signal_history if s['etf_code']=='516770'],settings['transaction_cost_bps'],settings['slippage_bps'])}
    validate_payload(latest)
    atomic_json(out/'system/signal_runs'/(at.replace(':','-')+'.json'),signals) # Validate whole generation BEFORE replacing any public dataset.
    for name,data in [('news',news),('games',games),('events',events),('signals',signal_history),('latest',latest)]:atomic_json(out/(name+'.json'),data)
    for e in etfs:atomic_json(out/'prices'/(e['code']+'.json'),e)
    atomic_json(out/'reports'/(at[:10]+'.json'),report);atomic_json(out/'system/status.json',system)
    print(json.dumps({'status':system['status'],'news':len(news),'events':len(events),'prices':{e['code']:len(e['prices']) for e in etfs},'ai':ai['status']},ensure_ascii=False))
    return latest

def main():
    p=argparse.ArgumentParser();p.add_argument('--validate-only',action='store_true');p.add_argument('--offline',action='store_true');p.add_argument('--output',type=Path,default=ROOT/'public/data');args=p.parse_args()
    if args.validate_only:validate_payload(load_json(args.output/'latest.json',{}));print('Data validation passed')
    else:run(args.output,args.offline)
if __name__=='__main__':main()
