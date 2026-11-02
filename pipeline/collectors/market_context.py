"""Dated market evidence. Missing or unsupported coverage always stays unknown."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import json
import math
import re
import random
from bs4 import BeautifulSoup

SH = ZoneInfo('Asia/Shanghai')
CALENDAR_SOURCE = 'https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml'
# Manually verified official 2026 notice, not a weekday-only calendar approximation.
HOLIDAY_RANGES_2026 = [('01-01','01-03'),('02-15','02-23'),('04-04','04-06'),('05-01','05-05'),('06-19','06-21'),('09-25','09-27'),('10-01','10-07')]

def calendar_context(as_of):
    dt = datetime.fromisoformat(as_of.replace('Z','+00:00')) if isinstance(as_of,str) else as_of
    if dt.tzinfo is None: raise ValueError('aware as_of required')
    dt=dt.astimezone(SH)
    if dt.year != 2026:
        return {'status':'unavailable','verified':False,'expected_last_session':None,'source_url':CALENDAR_SOURCE,'reason':'仅核验 2026 年官方休市表，其他年份暂停判断'}
    holidays=set()
    for a,b in HOLIDAY_RANGES_2026:
        d=date.fromisoformat('2026-'+a);end=date.fromisoformat('2026-'+b)
        while d<=end: holidays.add(d);d+=timedelta(days=1)
    candidate=dt.date()
    if dt.time()<time(15,0):candidate-=timedelta(days=1)
    while candidate.weekday()>=5 or candidate in holidays:candidate-=timedelta(days=1)
    if candidate.year!=2026:
        return {'status':'unavailable','verified':False,'expected_last_session':None,'source_url':CALENDAR_SOURCE,'reason':'上一个交易日超出已核验年份'}
    return {'status':'verified','verified':True,'expected_last_session':candidate.isoformat(),'source_url':CALENDAR_SOURCE,'coverage_year':2026,'published_date':'2025-12-22','verified_date':'2026-11-02','timezone':'Asia/Shanghai','session_close':'15:00','limitation':'按已公布全年休市表；临时停市需另外核验，跨年自动暂停'}

def parse_benchmark(text,as_of):
    start=text.find('[');end=text.rfind(']')
    if start<0 or end<start:raise ValueError('missing benchmark array')
    arr=json.loads(text[start:end+1]);rows=[];cutoff=calendar_context(as_of).get('expected_last_session')
    if not cutoff:return []
    for p in arr:
        d=p['day'][:10];date.fromisoformat(d)
        close=float(p['close'])
        if not math.isfinite(close) or close<=0:raise ValueError('invalid benchmark close')
        if '2023-01-01'<=d<=cutoff: rows.append({'date':d,'close':close})
    if not rows:raise ValueError('empty completed benchmark history')
    if len({x['date'] for x in rows})!=len(rows):raise ValueError('duplicate benchmark dates')
    return sorted(rows,key=lambda p:p['date'])

def collect_benchmark(http,as_of):
    url='https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData'
    try:
        response=http.get(url,params={'symbol':'sh000300','scale':'240','ma':'no','datalen':'1023'})
        rows=parse_benchmark(response.text,as_of)
        return {'status':'ok','code':'000300','name':'沪深300指数','price_type':'index_close','source':'Sina','source_url':url,'adjustment':'price_index_not_total_return','as_of':rows[-1]['date'],'prices':rows,'limitation':'宽基市场对照，并非 ETF 跟踪的动漫游戏指数；指数价格收益不含股息'}
    except Exception as e:
        return {'status':'unavailable','code':'000300','name':'沪深300指数','source_url':url,'prices':[],'as_of':None,'error':type(e).__name__}

def parse_holdings(html,code,as_of):
    """Read disclosed table rows only. Never execute the remote JS wrapper."""
    # Archive returns var apidata={content:"<html>...",...}; isolate JSON string.
    if 'var apidata' in html:
        m=re.search(r'content\s*:\s*("(?:[^"\\]|\\.)*")',html,re.S)
        if not m:raise ValueError('unsupported archive payload')
        html=json.loads(m.group(1))
    soup=BeautifulSoup(html,'html.parser');snapshots=[]
    for table in soup.find_all('table'):
        header=' '.join(x.get_text(' ',strip=True) for x in table.find_all('th'))
        if '股票代码' not in header or '占净值' not in header:continue
        heading=table.find_previous(['h4','h3'])
        label=heading.get_text(' ',strip=True) if heading else ''
        quarter=re.search(r'(20\d{2})\s*年\s*第?([1234一二三四])\s*季度',label)
        if not quarter:continue
        q={'一':1,'二':2,'三':3,'四':4}.get(quarter[2],int(quarter[2]) if quarter[2].isdigit() else 0)
        end=f'{quarter[1]}-'+{1:'03-31',2:'06-30',3:'09-30',4:'12-31'}[q]
        if end>as_of[:10]:raise ValueError('future holdings report period')
        cols=[re.sub(r'\s+','',x.get_text()) for x in table.find_all('th')]
        ci=next(i for i,v in enumerate(cols) if '股票代码' in v);ni=next(i for i,v in enumerate(cols) if '股票名称' in v);wi=next(i for i,v in enumerate(cols) if '占净值' in v)
        rows=[]
        for tr in table.find_all('tr'):
            cells=[x.get_text(' ',strip=True) for x in tr.find_all('td')]
            if not cells:continue
            if len(cells)<=max(ci,ni,wi):raise ValueError('malformed holdings row')
            stock=cells[ci];weight=float(cells[wi].strip('%').replace(',',''))/100
            if not re.fullmatch(r'\d{5,6}',stock) or not math.isfinite(weight) or not 0<=weight<=1:raise ValueError('invalid holdings value')
            rows.append({'code':stock,'name':cells[ni],'weight':weight,'weight_basis':'fraction_of_fund_NAV','as_of':end,'published_at':None,'source_url':f'https://fundf10.eastmoney.com/ccmx_{code}.html'})
        if rows:
            if sum(x['weight'] for x in rows)>1.01:raise ValueError('invalid holdings total')
            snapshots.append((end,rows))
    if not snapshots:raise ValueError('no dated holdings table')
    return max(snapshots,key=lambda x:x[0])

def collect_holdings(http,code,as_of):
    url='https://fundf10.eastmoney.com/FundArchivesDatas.aspx'
    try:
        text=http.get(url,params={'type':'jjcc','code':code,'topline':'100','year':as_of[:4],'month':'','rt':str(random.random())},headers={'Referer':f'https://fundf10.eastmoney.com/ccmx_{code}.html'}).text
        period,rows=parse_holdings(text,code,as_of)
        return {'status':'ok','as_of':period,'holdings':rows,'source_url':f'https://fundf10.eastmoney.com/ccmx_{code}.html','published_at':None,'limitation':'披露期持仓快照，非实时权重；公告时间缺失，不用于历史时点策略；披露可能仅前十大'}
    except Exception as e:return {'status':'unavailable','as_of':None,'holdings':[],'source_url':f'https://fundf10.eastmoney.com/ccmx_{code}.html','error':type(e).__name__,'limitation':'未取得可解析且有报告期的持仓，不猜测权重'}
