"""Read-only first-run admission: exact IDs, all phases, XML and run identity."""
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--artifacts',required=True,type=Path)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--sha',required=True)
    p.add_argument('--run-id',required=True)
    p.add_argument('--run-attempt',required=True)
    args=p.parse_args()
    if hashlib.sha256(args.manifest.read_bytes()).hexdigest()!='e4e6ddb334f15aa164d31a9dce3b9b59aff3a84c17de1d34819e1ed9c3d808b6':
        raise ValueError('Expected manifest pin differs')
    manifest=json.loads(args.manifest.read_text())
    all_main=[]
    seen=set()
    for profile,contexts in [('PDF_PROFILE',['PDF_PROFILE']),('UI_PROFILE',['UI_PROFILE']),
                             ('NAMESPACE_INTEGRATION',['NAMESPACE_BASE','NAMESPACE_OVERLAY'])]:
        matches=list(args.artifacts.glob(f'c27-r18-{profile}-{args.run_id}-{args.run_attempt}'))
        if len(matches)!=1: raise ValueError('Missing/ambiguous artifact: '+profile)
        root=matches[0]
        for line in (root/'SHA256SUMS').read_text().splitlines():
            wanted,relative=line.split('  ',1)
            if Path(relative).is_absolute() or '..' in Path(relative).parts or (root/relative).is_symlink():
                raise ValueError('Unsafe artifact checksum path')
            if hashlib.sha256((root/relative).read_bytes()).hexdigest()!=wanted:
                raise ValueError('Artifact checksum mismatch')
        identity=json.loads((root/'identity.json').read_text())
        if identity['commit']!=args.sha or identity['run_id']!=args.run_id or identity['run_attempt']!=args.run_attempt:
            raise ValueError('Artifact identity mismatch')
        job=json.loads((root/'job-outcomes.json').read_text())
        if job['status']!='PASSED' or job['failure'] is not None: raise ValueError('Job not passed')
        if job['actual_call_count']!=sum(len(manifest['profiles'][c]['nodeids']) for c in contexts):
            raise ValueError('Job call count differs')
        for context in contexts:
            seen.add(context); expected=manifest['profiles'][context]['nodeids']
            for phase in ('collect','execute'):
                evidence=root/f'{context}-{phase}'/'evidence'
                collected=json.loads((evidence/'collected.json').read_text())
                outcome=json.loads((evidence/'outcomes.json').read_text())
                command=json.loads((evidence/'command.json').read_text())
                container=json.loads((root/f'{context}-{phase}'/'container-status.json').read_text())
                if collections.Counter(collected)!=collections.Counter(expected): raise ValueError('Exact IDs differ')
                wanted='COLLECTION_VERIFIED' if phase=='collect' else 'PASSED'
                if (outcome['status']!=wanted or outcome['pytest_exit_code']!=0 or outcome['collected']!=len(expected)
                    or command['collect_only']!=(phase=='collect') or container['status']!=wanted
                    or container['container_state']['ExitCode']!=0 or container['container_state']['OOMKilled']):
                    raise ValueError('Incomplete phase: '+context+'/'+phase)
                security=json.loads((root/f'{context}-{phase}'/'security-report.json').read_text())
                if (security['network_mode']!='none' or not security['read_only_root']
                    or security['user']!='10001:10001' or security['memory']!=4*1024**3
                    or security['memory_swap']!=4*1024**3 or security['nano_cpus']!=2*10**9
                    or security['pids_limit']!=256):
                    raise ValueError('Isolation report mismatch')
                if phase=='execute':
                    reports=outcome['reports']
                    if collections.Counter((r['nodeid'],r['phase']) for r in reports)!=collections.Counter((n,s) for n in expected for s in ('setup','call','teardown')):
                        raise ValueError('Missing/extra execution phase')
                    if not all(r['outcome']=='passed' and not r['wasxfail'] for r in reports): raise ValueError('Skip/xfail/failure detected')
                    cases=list(ET.parse(evidence/'junit.xml').getroot().iter('testcase'))
                    if len(cases)!=len(expected) or any(list(c) for c in cases): raise ValueError('JUnit not clean')
                    if outcome['actual_call_count']!=len(expected) or outcome['passed_call_count']!=len(expected): raise ValueError('Executed counts differ')
                    if context in ('PDF_PROFILE','UI_PROFILE'): all_main.extend(r['nodeid'] for r in reports if r['phase']=='call')
    expected=manifest['profiles']['PDF_PROFILE']['nodeids']+manifest['profiles']['UI_PROFILE']['nodeids']
    if len(expected)!=105 or len(set(expected))!=105 or collections.Counter(all_main)!=collections.Counter(expected):
        raise ValueError('105 open IDs not executed exactly once')
    print(json.dumps({'status':'CI_EVIDENCE_VERIFIED','open_cases_executed':105,'coexistence_base':3,
                      'coexistence_overlay':4,'production':'NOT_APPROVED','integration':'BLOCKED_PENDING_REVIEW'},indent=2))


if __name__=='__main__': main()
