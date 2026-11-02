"""Run only after a successful production build; no claim about deployment success."""
import json, os, shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=root/'public/data'
latest=json.loads((data/'latest.json').read_text())
status=json.loads((data/'system/status.json').read_text())
status['build_status']='production_build_passed'
status['build_commit']=os.environ.get('GITHUB_SHA')
repo=os.environ.get('GITHUB_REPOSITORY')
run=os.environ.get('GITHUB_RUN_ID')
status['build_run_url']=f'https://github.com/{repo}/actions/runs/{run}' if repo and run else None
latest['system']=status
from pipeline.verification.validate import validate_payload
validate_payload(latest)
for path,value in [(data/'latest.json',latest),(data/'system/status.json',status)]:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    target=root/'dist/data'/path.relative_to(data)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)
