from pipeline.common import canonical_url

def merge_news(old,new,limit=1200):
    merged={canonical_url(n['url']):n for n in old}
    for n in new:
        key=canonical_url(n['url'])
        if key in merged:n={**n,'collected_at':merged[key]['collected_at']}
        merged[key]=n
    return sorted(merged.values(),key=lambda n:n.get('published_at') or n['collected_at'],reverse=True)[:limit]
