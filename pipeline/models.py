"""Public data contracts. Missing evidence is represented by null, never invented."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Record(BaseModel):
    model_config = ConfigDict(extra='forbid',allow_inf_nan=False)

class News(Record):
    id: str
    title: str
    url: str
    source: str
    published_at: str | None = None
    collected_at: str
    game_ids: list[str] = Field(default_factory=list)
    category: str = 'industry'
    summary: str = ''
    verification_status: Literal['verified','reported','unverified'] = 'reported'
    credibility_score: int = Field(ge=0,le=100)
    limitations: list[str] = Field(default_factory=list)
    source_type: str = 'media'
    summary_status: str = 'source_excerpt'
    summary_language: str | None = None
    @field_validator('url')
    @classmethod
    def valid_url(cls,v):
        if not v.startswith(('https://','http://')): raise ValueError('source URL required')
        return v
    @field_validator('published_at','collected_at')
    @classmethod
    def timezone_required(cls,v):
        if v is not None and datetime.fromisoformat(v.replace('Z','+00:00')).tzinfo is None: raise ValueError('timezone required')
        return v

class Price(Record):
    date: str
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    amount: float | None = Field(default=None,ge=0)
    @field_validator('date')
    @classmethod
    def valid_date(cls,v):
        datetime.strptime(v,'%Y-%m-%d'); return v

class Event(Record):
    id: str
    game_id: str
    title: str
    type: str
    importance: str = 'B'
    event_date: str | None = None
    announced_at: str | None = None
    first_seen_at: str
    status: Literal['rumored','announced','confirmed','postponed','completed','cancelled']
    source_urls: list[str]
    source_ids: list[str] = Field(default_factory=list)
    company_links: list[dict] = Field(default_factory=list)
    history: list[dict] = Field(default_factory=list)
    verification_note: str = ''
    investment_channel: str = '行业情绪；直接收益关系未证实'
    @field_validator('source_urls')
    @classmethod
    def urls(cls,v):
        if not v or any(not u.startswith(('http://','https://')) for u in v):raise ValueError('valid source URLs required')
        return v
    @field_validator('announced_at','first_seen_at')
    @classmethod
    def timestamps(cls,v):
        if v is not None and datetime.fromisoformat(v.replace('Z','+00:00')).tzinfo is None:raise ValueError('timezone required')
        return v
    @field_validator('event_date')
    @classmethod
    def dates(cls,v):
        if v is not None:
            if len(v)==10:datetime.strptime(v,'%Y-%m-%d')
            elif datetime.fromisoformat(v.replace('Z','+00:00')).tzinfo is None:raise ValueError('timezone required')
        return v

class Signal(Record):
    signal_date: str
    etf_code: str
    data_cutoff_time: str | None
    signal: str
    signal_score: float | None
    confidence_basis: str
    reasons: list[str]
    risks: list[str]
    invalidating_conditions: list[str]
    strategy_version: str
    source_ids: list[str]
    score_breakdown: list[dict] = Field(default_factory=list)
    price_age_days: int | None = None
    recorded_at: str | None = None

class Report(Record):
    date: str
    generated_at: str
    summary: str
    reasons: list[str]
    risks: list[str]
    source_ids: list[str]
    ai_status: str
    ai_summary: str
    disclaimer: str

class SystemStatus(Record):
    status: Literal['ok','partial_failure','failed']
    generated_at: str
    last_success_at: str | None
    last_partial_success_at: str | None = None
    source_status: list[dict]
    strategy_version: str
    ai_status: str
    ai: dict
    last_ai_success_at: str | None
    latest_market_date: str | None
    market_calendar_status: str
    build_status: str
    build_commit: str | None = None
    build_run_url: str | None = None

class Payload(Record):
    schema_version: Literal['1.0']
    generated_at: str
    timezone: Literal['Asia/Shanghai']
    data_cutoff_time: str | None
    news: list[News]
    games: list[dict]
    events: list[Event]
    etfs: list[dict]
    signals: list[Signal]
    report: Report
    system: SystemStatus
    event_studies: list[dict]
    backtest: dict
