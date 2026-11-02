import json
from pipeline.models import Price
from pipeline.common import now
NAMES={'516770':'游戏ETF华泰柏瑞','159869':'游戏ETF华夏','516010':'游戏ETF国泰'}

def collect_prices(http,code):
    errors=[]
    url='https://push2his.eastmoney.com/api/qt/stock/kline/get'
    try:
        j=http.get(url,params={'secid':('0.' if code.startswith('1') else '1.')+code,'fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','klt':'101','fqt':'0','beg':'20230101','end':'20500101'}).json()
        rows=[]
        for s in (j.get('data') or {}).get('klines',[]):
            p=s.split(',');rows.append(Price(date=p[0],open=float(p[1]),close=float(p[2]),high=float(p[3]),low=float(p[4]),volume=float(p[5])*100,amount=float(p[6])).model_dump())
        if not rows:raise ValueError('empty price series')
        return rows,{'source':'Eastmoney','source_url':url+'?secid='+('0.' if code.startswith('1') else '1.')+code+'&klt=101&fqt=0&beg=20230101&end=20500101','adjustment':'unadjusted','volume_unit':'shares','errors':errors}
    except Exception as e:errors.append('Eastmoney: '+type(e).__name__)
    url='https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_data=/CN_MarketDataService.getKLineData'
    try:
        text=http.get(url,params={'symbol':('sz' if code.startswith('1') else 'sh')+code,'scale':'240','ma':'no','datalen':'1023'}).text
        start=text.find('[');end=text.rfind(']');arr=json.loads(text[start:end+1]);rows=[]
        for p in arr:
            if p['day'][:10]<'2023-01-01':continue
            rows.append(Price(date=p['day'][:10],open=float(p['open']),close=float(p['close']),high=float(p['high']),low=float(p['low']),volume=float(p['volume']),amount=None).model_dump())
        if not rows:raise ValueError('empty price series')
        return rows,{'source':'Sina','source_url':url+'?symbol='+('sz' if code.startswith('1') else 'sh')+code+'&scale=240&ma=no&datalen=1023','adjustment':'unadjusted','volume_unit':'source_native_unverified','errors':errors,'limitation':'成交量单位未独立核验，不与其他来源拼接；成交额缺失'}
    except Exception as e:errors.append('Sina: '+type(e).__name__)
    return [],{'source':None,'source_url':None,'adjustment':'unadjusted','volume_unit':None,'errors':errors}
