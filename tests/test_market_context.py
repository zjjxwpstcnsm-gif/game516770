import pytest
from pipeline.collectors.market_context import calendar_context,parse_benchmark,parse_holdings

def test_national_day_calendar():
    assert calendar_context('2026-10-07T17:25:00+08:00')['expected_last_session']=='2026-09-30'
    assert calendar_context('2026-10-08T08:20:00+08:00')['expected_last_session']=='2026-09-30'
    assert calendar_context('2026-10-08T17:25:00+08:00')['expected_last_session']=='2026-10-08'

def test_calendar_utc_and_unknown_year():
    assert calendar_context('2026-11-02T06:59:00+00:00')['expected_last_session']=='2026-10-30'
    assert calendar_context('2026-11-02T07:00:00+00:00')['expected_last_session']=='2026-11-02'
    assert not calendar_context('2027-01-04T17:00:00+08:00')['verified']
    with pytest.raises(ValueError):calendar_context('2026-11-02T17:00:00')

def test_benchmark_rejects_inflight_and_invalid():
    rows=parse_benchmark('f([{"day":"2026-10-30","close":"2"},{"day":"2026-11-02","close":"3"}])','2026-11-02T08:20:00+08:00')
    assert len(rows)==1
    with pytest.raises(ValueError):parse_benchmark('[{"day":"2026-10-30","close":"NaN"}]','2026-11-02T17:00:00+08:00')

def table(weight='9.50%',quarter='2026年3季度'):
    return f'<h4>{quarter}股票投资明细</h4><table><tr><th>股票代码</th><th>股票名称</th><th>占净值比例</th></tr><tr><td>002555</td><td>三七互娱</td><td>{weight}</td></tr></table>'

def test_holdings_report_date_and_fraction():
    d,rows=parse_holdings(table(),'516770','2026-11-02T17:00:00+08:00')
    assert d=='2026-09-30' and rows[0]['weight']==.095 and rows[0]['published_at'] is None

def test_holdings_missing_future_bad():
    for text in ('nothing',table('150%'),table(quarter='2026年4季度')):
        with pytest.raises(ValueError):parse_holdings(text,'516770','2026-11-02T17:00:00+08:00')

def test_holdings_fetch_uses_site_referer_and_safe_wrapper():
    from pipeline.collectors.market_context import collect_holdings
    import json
    class HTTP:
        def get(self,url,**kwargs):
            assert kwargs['headers']['Referer']=='https://fundf10.eastmoney.com/ccmx_516770.html'
            assert 'rt' in kwargs['params']
            return type('R',(),{'text':'var apidata={ content:'+json.dumps(table())+' };'})()
    result=collect_holdings(HTTP(),'516770','2026-11-02T17:00:00+08:00')
    assert result['status']=='ok' and result['published_at'] is None

def test_source_failure_is_missing_not_fake_zero():
    from pipeline.collectors.market_context import collect_holdings,collect_benchmark
    class HTTP:
        def get(self,*a,**kw):raise RuntimeError('failure')
    assert collect_holdings(HTTP(),'516770','2026-11-02T17:00:00+08:00')['holdings']==[]
    assert collect_benchmark(HTTP(),'2026-11-02T17:00:00+08:00')['as_of'] is None
