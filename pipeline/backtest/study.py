"""Descriptive event studies. Unknown future points remain null."""
from datetime import date,datetime
import bisect
OFFSETS=[-20,-10,-5,-1,0,1,3,5,10,20]
def max_drawdown(values):
    peak=values[0] if values else 0;worst=0
    for x in values:peak=max(peak,x);worst=min(worst,x/peak-1)
    return worst

def event_study(prices,event,benchmark=None):
    if not prices or not event.get('event_date'):return None
    ds=[p['date'] for p in prices];t=bisect.bisect_left(ds,event['event_date'][:10])
    if t>=len(ds):return None
    # Map non-trading dates to next observed trading session; base T-1.
    if t<1:return None
    base=prices[t-1]['close'];points=[]
    for offset in OFFSETS:
        i=t+offset
        points.append({'offset':offset,'date':ds[i] if 0<=i<len(ds) else None,'return':prices[i]['close']/base-1 if 0<=i<len(ds) else None})
    benchmark_map={p['date']:p['close'] for p in (benchmark or [])};benchmark_base=benchmark_map.get(ds[t-1])
    for point in points:
        b=benchmark_map.get(point['date'])
        point['benchmark_return']=b/benchmark_base-1 if b and benchmark_base else None
        point['excess_return']=point['return']-point['benchmark_return'] if point['return'] is not None and point['benchmark_return'] is not None else None
    window=prices[max(0,t-20):min(len(prices),t+21)];vol_before=[p['volume'] for p in prices[max(0,t-20):t]];vol_after=[p['volume'] for p in prices[t:min(len(prices),t+21)]]
    return {'event_id':event['id'],'title':event['title'],'game_id':event['game_id'],'event_date':event['event_date'],'trading_date':ds[t],'baseline':'T-1 close','mapping_rule':'事件日非交易日映射到下一实际观测交易日','points':points,'max_drawdown':max_drawdown([p['close'] for p in window]),'volume_ratio':(sum(vol_after)/len(vol_after))/(sum(vol_before)/len(vol_before)) if vol_before and vol_after and sum(vol_before)>0 else None,'complete_window':t>=20 and t+20<len(prices),'excess_return':points[-1]['excess_return'],'sample_size':1,'limitations':['描述性关联，不构成因果证据','超额收益对照沪深300价格指数；缺少同日基准时留空','未复权价格，分红会影响跨期收益'],'source_urls':event['source_urls']}

def replay_signals(prices,signals,fee_bps=5,slippage_bps=5):
    """Only recorded signal cutoffs, execution at next observed open. No hindsight tuning."""
    by_date={s['signal_date']:s for s in signals};cash=1.;units=0.;equity=[];trades=[];entry=None
    for i,p in enumerate(prices):
        if i:
            s=by_date.get(prices[i-1]['date'])
            if s and s.get('data_cutoff_time') and s.get('recorded_at') and datetime.fromisoformat(s['data_cutoff_time']) < datetime.fromisoformat(p['date']+'T09:30:00+08:00') and datetime.fromisoformat(s['recorded_at']) < datetime.fromisoformat(p['date']+'T09:30:00+08:00'):
                cost=(fee_bps+slippage_bps)/10000
                if s['signal']=='分批建仓候选' and not units:
                    units=cash/(p['open']*(1+cost));cash=0.;entry=p['open'];trades.append({'date':p['date'],'side':'buy','price':p['open']})
                elif s['signal'] in ('减仓风险','止盈观察') and units:
                    cash=units*p['open']*(1-cost);units=0.;trades.append({'date':p['date'],'side':'sell','price':p['open'],'gross_return':p['open']/entry-1,'net_return':p['open']*(1-cost)/(entry*(1+cost))-1})
        equity.append(cash+units*p['close'])
    closed=[x for x in trades if x['side']=='sell']
    return {'status':'insufficient_samples' if len(closed)<20 else 'research_only','sample_size':len(closed),'win_rate':sum(t['net_return']>0 for t in closed)/len(closed) if closed else None,'cumulative_return':equity[-1]-1 if equity else None,'max_drawdown':max_drawdown(equity),'buy_hold_return':prices[-1]['close']/prices[0]['open']-1 if prices else None,'trades':trades,'transaction_cost_bps':fee_bps,'slippage_bps':slippage_bps,'limitations':['仅回放真实归档信号，不制造历史信号','样本不足，未做样本外参数校准','信号次交易日开盘执行，交易费和滑点已计入']}
