def daily_report(signals,news,events,generated_at,ai):
    main=next((s for s in signals if s['etf_code']=='516770'),signals[0] if signals else {})
    return {'date':generated_at[:10],'generated_at':generated_at,'summary':main.get('signal','数据不足，暂停判断'),'reasons':main.get('reasons',[]),'risks':main.get('risks',[]),'source_ids':main.get('source_ids',[]),'ai_status':ai.get('status','unavailable'),'ai_summary':ai.get('summary') or 'AI分析暂不可用','disclaimer':'仅用于投资研究，不保证收益，不执行真实证券交易。'}
