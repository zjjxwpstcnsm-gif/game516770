from datetime import datetime,date,timedelta
from pipeline.models import Signal
from pipeline.etf.relationships import event_exposure

def score_event(event,game,relation,days,trend,weights):
    # Transparent heuristic, not a calibrated probability. Unknown direct relation
    # receives no positive credit, which differs from claiming it is proven zero.
    parts={'event_importance':{'SSS':100,'SS':85,'S':65,'A':40,'B':20}.get(event.get('importance'),0),'credibility':100 if event['status'] in ('confirmed','completed') else 20,'heat':game.get('heat_score') or 0,'timing':max(0,100-abs(days)*100/30),'etf_relation':{'direct':100,'indirect':50,'sentiment':15}.get(relation,0),'trend':100 if trend else 0}
    return round(sum(parts[k]*weights[k] for k in parts),2),parts

def generate_signal(etf,events,games,settings,at):
    dt=datetime.fromisoformat(at);today=dt.date();asof=etf.get('as_of');p=etf.get('prices',[]);ind=etf.get('indicators',{})
    base={'signal_date':str(today),'etf_code':etf['code'],'data_cutoff_time':etf.get('data_cutoff_time'),'strategy_version':settings['version'],'source_ids':[f"prices:{etf['code']}:{asof}"] if asof else [],'confidence_basis':'启发式规则，尚未经足够样本的独立验证；评分不是上涨概率','invalidating_conditions':['新增延期、政策风险或证据纠错后重新计算','行情过期或缺失时停止判断'],'risks':['事件热度不等于 ETF 成分股盈利','未核验当前持仓权重及直接收益权利','未复权价格不含分红再投资，不能视为总回报']}
    age=(today-date.fromisoformat(asof)).days if asof else 999
    if age<0 or not p or age>settings['price_max_age_days'] or len(p)<settings['minimum_history']:
        return Signal(**base,signal='数据不足，暂停判断',signal_score=None,reasons=['行情缺失、过期或历史长度不足；不沿用旧建议冒充今日信号']).model_dump()
    eligible=[e for e in events if e.get('event_date') and e['status']=='confirmed' and 0<=(date.fromisoformat(e['event_date'][:10])-today).days<=settings['catalyst_window_days']]
    trend=bool(ind.get('ma5') and ind.get('ma20') and p[-1]['close']>ind['ma20'] and ind['ma5']>ind['ma20'])
    score=0;basis=[];direct_relation_verified=False;gm={g['id']:g for g in games}
    for e in eligible:
        exposure=event_exposure(e,etf,at);direct_relation_verified=direct_relation_verified or exposure['relation']=='direct'
        s,parts=score_event(e,gm.get(e['game_id'],{}),exposure['relation'],(date.fromisoformat(e['event_date'][:10])-today).days,trend,settings['weights']);score=max(score,s);base['source_ids'].extend(e.get('source_ids',[]) or e.get('source_urls',[]));basis.append({'event_id':e['id'],'components':parts,'score':s,'exposure':exposure})
    if not etf.get('calendar_verified'):
        return Signal(**base,signal='数据不足，暂停判断',signal_score=None,reasons=['未核验最近应完成的交易日，无法确认行情是否已补齐；暂停操作判断']).model_dump()
    if (ind.get('return5') or 0)<settings['risk_return5']:state='减仓风险';reasons=['近 5 个交易日跌幅超过配置风险阈值；仅作条件化风险研究']
    elif eligible and trend and score>=settings['entry_score'] and etf.get('holdings_as_of') and etf.get('holdings_status')=='ok' and etf.get('benchmark_verified') and direct_relation_verified:state='分批建仓候选';reasons=['存在已确认的未来催化事件','价格与均线满足趋势确认；尚需核验持仓收益关联']
    else:state='观察等待';reasons=['未同时满足已确认催化剂、趋势及受益关联条件','无个人持仓信息，不假设持有状态']
    out=Signal(**base,signal=state,signal_score=score,reasons=reasons).model_dump();out['score_breakdown']=basis;out['price_age_days']=age
    return out
