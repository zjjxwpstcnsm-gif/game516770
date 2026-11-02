from pipeline.etf.relationships import event_exposure

def test_no_equity_rights_from_popularity():
    assert event_exposure({'importance':'SSS'}, {'holdings':[]},'2026-11-02')['verified_holding_weight'] is None

def test_weight_deduplicated_and_expired_right_ignored():
    link={'stock_code':'000001','relation':'direct','verification_status':'verified','source_url':'https://example.com/ir','valid_from':'2026-01-01'}
    etf={'holdings':[{'code':'000001','weight':0.1,'as_of':'2026-09-30'}],'holdings_as_of':'2026-09-30'}
    assert event_exposure({'company_links':[link,link]},etf,'2026-11-02')['verified_holding_weight']==0.1
    assert event_exposure({'company_links':[{**link,'valid_to':'2026-10-01'}]},etf,'2026-11-02')['relation']=='sentiment'
