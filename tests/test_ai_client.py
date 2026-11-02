import json
from pathlib import Path

import httpx
import pytest

from pipeline.ai import AgnesClient, AISettings

RECORDS = [{'id': 'n1', 'title': '官方公布试玩计划', 'url': 'https://example.com/news', 'source': 'official', 'published_at': '2026-11-02T08:00:00+08:00'}]
DOC = {'summary': '官方公布试玩计划。', 'source_ids': ['n1'], 'items': [{'summary': '官方公布试玩计划。', 'source_ids': ['n1'], 'category': 'announcement', 'game_names': []}], 'uncertainties': []}


def ok(doc=None):
    return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(doc or DOC)}}], 'usage': {'total_tokens': 100}})


def make(tmp_path, outcomes, **settings):
    calls, sleeps = [], []
    def handler(request):
        calls.append(request)
        outcome = outcomes[min(len(calls)-1, len(outcomes)-1)]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    config = AISettings(daily_budget_usd=100, daily_tokens=1000000, **settings)
    client = AgnesClient(api_key='secret-do-not-log', settings=config, state_dir=tmp_path,
                        transport=httpx.MockTransport(handler), sleep=sleeps.append, jitter=lambda: 0)
    return client, calls, sleeps


def test_two_429_then_success(tmp_path):
    client, calls, sleeps = make(tmp_path, [httpx.Response(429), httpx.Response(429), ok()])
    result = client.analyze(RECORDS)
    assert result.status == 'ok' and len(calls) == 3 and sleeps == [1, 2]


def test_retry_after(tmp_path):
    client, calls, sleeps = make(tmp_path, [httpx.Response(429, headers={'Retry-After': '7'}), ok()])
    assert client.analyze(RECORDS).status == 'ok'
    assert sleeps == [7]


def test_retry_after_exceeds_budget(tmp_path):
    client, calls, sleeps = make(tmp_path, [httpx.Response(429, headers={'Retry-After': '999'})], total_budget_seconds=10)
    assert client.analyze(RECORDS).status == 'failed'
    assert len(calls) == 1 and not sleeps


def test_503_recovers(tmp_path):
    client, calls, _ = make(tmp_path, [httpx.Response(503), ok()])
    assert client.analyze(RECORDS).status == 'ok' and len(calls) == 2


@pytest.mark.parametrize('status', [400, 401, 403])
def test_permanent_error_no_retry(tmp_path, status):
    client, calls, sleeps = make(tmp_path, [httpx.Response(status), ok()])
    result = client.analyze(RECORDS)
    assert result.error == f'http_{status}' and len(calls) == 1 and not sleeps


@pytest.mark.parametrize('error', [httpx.ReadTimeout('timeout'), httpx.ConnectTimeout('timeout'), httpx.ConnectError('reset'), httpx.RemoteProtocolError('reset')])
def test_timeout_and_network_retry(tmp_path, error):
    client, calls, _ = make(tmp_path, [error, ok()])
    assert client.analyze(RECORDS).status == 'ok' and len(calls) == 2


def test_illegal_json_repair_once(tmp_path):
    client, calls, _ = make(tmp_path, [httpx.Response(200, text='invalid json'), ok()])
    assert client.analyze(RECORDS).status == 'ok' and len(calls) == 2
    assert len(json.loads(calls[-1].content)['messages']) == 3


def test_schema_failure_bounded(tmp_path):
    invalid = httpx.Response(200, json={'choices': [{'message': {'content': '{}'}}]})
    client, calls, _ = make(tmp_path, [invalid])
    result = client.analyze(RECORDS)
    assert result.status == 'failed' and result.error == 'invalid_structured_output' and len(calls) == 2


def test_empty_response_repair(tmp_path):
    client, calls, _ = make(tmp_path, [httpx.Response(200, json={'choices': []}), ok()])
    assert client.analyze(RECORDS).status == 'ok' and len(calls) == 2


def test_exhaustion_exactly_five(tmp_path):
    client, calls, sleeps = make(tmp_path, [httpx.Response(503)])
    result = client.analyze(RECORDS)
    assert result.status == 'failed' and result.attempts == 5 and len(calls) == 5
    assert sleeps == [1, 2, 4, 8]


def test_success_cache_prevents_rebilling(tmp_path):
    client, calls, _ = make(tmp_path, [ok()])
    assert client.analyze(RECORDS).status == 'ok'
    assert client.analyze(RECORDS).cached
    assert len(calls) == 1
    ledger = json.loads((tmp_path / 'budget.json').read_text())
    assert next(iter(ledger.values()))['tokens'] == 100


def test_daily_budget_persists_and_unknown_usage_reserved(tmp_path):
    client, calls, _ = make(tmp_path, [httpx.Response(503)], daily_calls=1)
    assert client.analyze(RECORDS).status == 'budget_exceeded'
    assert len(calls) == 1
    second, calls2, _ = make(tmp_path, [ok()], daily_calls=1)
    assert second.analyze(RECORDS).status == 'budget_exceeded' and not calls2
    assert next(iter(json.loads((tmp_path / 'budget.json').read_text()).values()))['tokens'] > 1500


def test_no_key_no_call(tmp_path):
    assert AgnesClient(api_key='', state_dir=tmp_path).analyze(RECORDS).status == 'unavailable'
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('doc', [dict(DOC, source_ids=['fake']), dict(DOC, summary='销量 999999，确定上涨 90%')])
def test_unknown_evidence_rejected(tmp_path, doc):
    client, calls, _ = make(tmp_path, [ok(doc)])
    assert client.analyze(RECORDS).status == 'failed' and len(calls) == 2


def test_secret_never_stored_or_logged(tmp_path, caplog):
    client, _, _ = make(tmp_path, [httpx.Response(401, text='secret-do-not-log')])
    client.analyze(RECORDS)
    assert 'secret-do-not-log' not in caplog.text
    for file in tmp_path.rglob('*.json'):
        assert 'secret-do-not-log' not in file.read_text()


def test_state_corruption_fails_closed(tmp_path):
    (tmp_path / 'budget.json').write_text('broken')
    client, calls, _ = make(tmp_path, [ok()])
    assert client.analyze(RECORDS).error == 'state_storage_error' and not calls


def test_time_budget_stops(tmp_path):
    client, calls, _ = make(tmp_path, [httpx.Response(503)], total_budget_seconds=1)
    assert client.analyze(RECORDS).status == 'failed' and len(calls) == 1

@pytest.mark.parametrize('body', [None, [], 'wrong'])
def test_invalid_envelope(tmp_path, body):
    client, calls, _ = make(tmp_path, [httpx.Response(200, text=json.dumps(body))])
    assert client.analyze(RECORDS).status == 'failed' and len(calls) == 2


def test_summary_numbers_must_be_in_cited_records(tmp_path):
    records = RECORDS + [{'id': 'n2', 'title': '销量 999999'}]
    client, _, _ = make(tmp_path, [ok(dict(DOC, summary='销量 999999'))])
    assert client.analyze(records).status == 'failed'
