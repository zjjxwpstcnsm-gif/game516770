import hashlib,json,os,re,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from zoneinfo import ZoneInfo
import yaml
ROOT=Path(__file__).resolve().parents[1]
TZ=ZoneInfo('Asia/Shanghai')
def now(): return datetime.now(TZ).isoformat(timespec='seconds')
def stable_id(*parts): return hashlib.sha256('|'.join(str(x) for x in parts).encode()).hexdigest()[:20]
def canonical_url(url):
    p=urlsplit(url.strip()); q=[(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith(('utm_','fbclid','gclid'))]
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/'),urlencode(sorted(q)),''))
def load_json(path,default):
    try: return json.loads(Path(path).read_text())
    except FileNotFoundError: return default

def atomic_json(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if path.exists() and path.read_text()==content:return False
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w') as f: f.write(content); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return True

def config(name):return yaml.safe_load((ROOT/'config'/f'{name}.yaml').read_text())
def clean_text(x):return re.sub(r'\s+',' ',re.sub('<[^>]+>','',x or '')).strip()
def parse_date(value):
    if not value:return None
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        if d.tzinfo is None:return None
        return d.isoformat()
    except ValueError:return None
