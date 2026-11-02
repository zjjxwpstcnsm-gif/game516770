"""Bounded, rate-limited public requests with robots checks for pages/feeds."""
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import httpx
UA='GameAlphaResearch/1.0 (+https://github.com/zjjxwpstcnsm-gif/game516770)'
class PublicHTTP:
    def __init__(self):
        self.client=httpx.Client(timeout=20,follow_redirects=True,headers={'User-Agent':UA})
        self.robots={};self.last={}
    def get(self,url,*,check_robots=False,params=None,timeout=20,interval_seconds=1,headers=None):
        host=urlsplit(url).netloc
        if check_robots and host not in self.robots:
            r=self.client.get(f'https://{host}/robots.txt')
            if r.status_code==200:
                rp=RobotFileParser();rp.parse(r.text.splitlines());self.robots[host]=rp
            elif r.status_code in (404,410):self.robots[host]=None
            else:raise RuntimeError('robots.txt unavailable; source skipped conservatively')
        if check_robots and self.robots[host] and not self.robots[host].can_fetch(UA,url):raise RuntimeError('robots.txt disallows fetch')
        wait=interval_seconds-(time.monotonic()-self.last.get(host,0))
        if wait>0:time.sleep(wait)
        self.last[host]=time.monotonic()
        r=self.client.get(url,params=params,timeout=timeout,headers=headers);r.raise_for_status();return r
