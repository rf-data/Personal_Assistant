"""R18 CI orchestration; never executed during preparation."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

PLAN = Path(__file__).resolve().parents[1]
PIN = 'e4e6ddb334f15aa164d31a9dce3b9b59aff3a84c17de1d34819e1ed9c3d808b6'
GIB = 1024**3


def host_capacity(path, initial=False):
    memory = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                  if line.startswith('MemTotal:'))
    free = shutil.disk_usage(path).free
    cpus = len(os.sched_getaffinity(0))
    if cpus < 2 or memory < 7*GIB or free < (10 if initial else 6)*GIB:
        raise RuntimeError('Runner capacity below admission/reserve limits')
    return {'available_cpus':cpus,'memory_total_bytes':memory,'disk_free_bytes':free}


def bounded(command, logfile, timeout, scratch, env=None, output_tree=None):
    with logfile.open('xb') as output:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, env=env)
        start = time.monotonic()
        try:
            while process.poll() is None:
                if time.monotonic()-start > timeout:
                    raise TimeoutError('Command wall time exceeded')
                if logfile.stat().st_size > 32*1024**2:
                    raise RuntimeError('Command log exceeded 32 MiB')
                if output_tree and sum(p.stat().st_size for p in output_tree.rglob('*') if p.is_file()) > 128*1024**2:
                    raise RuntimeError('Evidence exceeded 128 MiB soft watchdog budget')
                host_capacity(scratch)
                time.sleep(2)
            if logfile.stat().st_size > 32*1024**2:
                raise RuntimeError('Command log exceeded 32 MiB')
            if output_tree and sum(p.stat().st_size for p in output_tree.rglob('*') if p.is_file()) > 128*1024**2:
                raise RuntimeError('Evidence exceeded 128 MiB soft watchdog budget')
            host_capacity(scratch)
            return process.returncode
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


def verify(root, scope):
    subprocess.run([sys.executable,'-B',str(PLAN/'support/verify_payload.py'),
                    '--manifest',str(PLAN/'support/r16_manifest.json'),
                    '--expected-manifest-sha256',PIN,'--root',str(root),'--scope',scope],check=True)


def run_phase(image, source, scope, profile, collect, destination, scratch):
    destination.mkdir()
    persistent = scratch / ('results-' + os.urandom(8).hex())
    persistent.mkdir(mode=0o777)
    persistent.chmod(0o777)  # Only this fresh output directory is writable by UID 10001.
    phase = 'collect' if collect else 'execute'
    name = 'c27-r18-' + os.urandom(8).hex()
    argv = ['docker','create','--pull','never','--platform','linux/amd64','--name',name,'--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges',
            '--cpus','2','--memory','4g','--memory-swap','4g','--pids-limit','256',
            '--shm-size','64m','--ulimit','nofile=1024:1024',
            '--ulimit','fsize=134217728:134217728',
            '--log-driver','local','--log-opt','max-size=10m','--log-opt','max-file=1','--log-opt','compress=false',
            '--tmpfs','/work:rw,nosuid,nodev,size=2g,mode=1777',
            '--tmpfs','/tmp:rw,nosuid,nodev,size=512m,mode=1777',
            '--mount',f'type=bind,src={persistent},dst=/results',
            '--mount',f'type=bind,src={source},dst=/input,readonly',
            '--mount',f'type=bind,src={PLAN},dst=/plan,readonly',
            '--workdir','/input','--user','10001:10001','--entrypoint','/opt/venv/bin/python',
            '--mount',f'type=bind,src={scratch / "venv"},dst=/opt/venv,readonly',
            image,'-B','/plan/support/run_profile.py',profile,
            '--manifest','/plan/support/r16_manifest.json',
            '--expected-manifest-sha256',PIN,
            '--work','/work/profile','--results','/results/evidence']
    if collect:
        argv.append('--collect-only')
    verify(source, scope)
    subprocess.run(argv,check=True,stdout=subprocess.DEVNULL)
    status = {'profile':profile,'phase':phase,'status':'INCOMPLETE','actual_call_count':0}
    try:
        inspected=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
        host=inspected['HostConfig']; config=inspected['Config']
        security={'network_mode':host['NetworkMode'],'read_only_root':host['ReadonlyRootfs'],
                  'cap_drop':host['CapDrop'],'security_opt':host['SecurityOpt'],
                  'user':config['User'],'working_dir':config['WorkingDir'],
                  'memory':host['Memory'],'memory_swap':host['MemorySwap'],
                  'nano_cpus':host['NanoCpus'],'pids_limit':host['PidsLimit']}
        (destination/'security-report.json').write_text(json.dumps(security,indent=2)+'\n')
        if (security['network_mode']!='none' or not security['read_only_root']
            or security['user']!='10001:10001' or security['working_dir']!='/input'
            or not any(v.lower()=='all' for v in security['cap_drop'])
            or not any(v.startswith('no-new-privileges') for v in security['security_opt'])
            or security['memory']!=4*GIB or security['memory_swap']!=4*GIB
            or security['nano_cpus']!=2*10**9 or security['pids_limit']!=256):
            raise RuntimeError('Docker isolation configuration mismatch; tests blocked')
        try:
            rc = bounded(['docker','start','--attach',name],destination/'stdout-stderr.log',
                         180 if collect else 900,scratch, output_tree=persistent)
            status['docker_attach_exit_code'] = rc
        except Exception as error:
            status['termination_reason'] = str(error)
            subprocess.run(['docker','kill',name],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        state = json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',name]))
        status['container_state'] = state
        subprocess.run(['docker','cp',name+':/results/.',str(destination)],check=True)
        evidence = destination/'evidence/outcomes.json'
        if evidence.is_file():
            outcome = json.loads(evidence.read_text())
            status.update({key:outcome.get(key) for key in ('expected','collected','actual_call_count','passed_call_count','elapsed_seconds')})
            status['pytest_status'] = outcome['status']
            wanted = 'COLLECTION_VERIFIED' if collect else 'PASSED'
            if (outcome['status'] == wanted and state['ExitCode'] == 0 and not state['OOMKilled']
                    and not state['Running'] and not status.get('termination_reason')):
                status['status'] = wanted
        verify(source, scope)
        return status
    finally:
        status['security'] = {'network':'none','user':'10001:10001','read_only_root':True,
            'capabilities':'ALL dropped','new_privileges':False,'credentials_forwarded':False,
            'result_storage':'dedicated bind mount; 128 MiB soft watchdog, no hard total quota'}
        (destination/'container-status.json').write_text(json.dumps(status,indent=2)+'\n')
        # Normal removal of this task's unique stopped container; never --force.
        subprocess.run(['docker','rm',name],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile',choices=['PDF_PROFILE','UI_PROFILE','NAMESPACE_INTEGRATION'],required=True)
    parser.add_argument('--python-image',required=True)
    parser.add_argument('--checkout',required=True,type=Path)
    parser.add_argument('--scratch',required=True,type=Path)
    parser.add_argument('--reports',required=True,type=Path)
    args = parser.parse_args()
    args.reports.mkdir(parents=True,exist_ok=False)
    phases=[]
    failure=None
    try:
        if not re.fullmatch(r'docker\.io/library/python:3\.12-slim-bookworm@sha256:[0-9a-f]{64}',args.python_image):
            raise ValueError('A reviewed immutable official Python image digest is required')
        if hashlib.sha256((PLAN/'support/r16_manifest.json').read_bytes()).hexdigest()!=PIN:
            raise ValueError('R16 manifest drift')
        args.scratch.mkdir(parents=False,exist_ok=False)
        capacity=host_capacity(args.scratch,initial=True)
        (args.reports/'capacity.json').write_text(json.dumps(capacity,indent=2)+'\n')
        prepare=[sys.executable,'-B',str(PLAN/'support/prepare_input.py'),
                 '--source',str(args.checkout),'--destination',str(args.scratch/'inputs')]
        if args.profile=='NAMESPACE_INTEGRATION':
            prepare.append('--namespace')
        subprocess.run(prepare,check=True)
        # No Docker build or legacy-builder dependency. One immutable image for all phases.
        image = args.python_image
        if bounded(['docker','pull','--platform','linux/amd64',image],
                   args.reports/'image-pull.log',300,args.scratch)!=0:
            raise RuntimeError('Pinned image acquisition failed')
        for name in ('wheelhouse','venv','setup-evidence'):
            (args.scratch/name).mkdir(mode=0o755)
            (args.scratch/name).chmod(0o755)
        setup_common = ['docker','create','--pull','never','--platform','linux/amd64',
            '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--cpus','2','--memory','4g','--memory-swap','4g','--pids-limit','256',
            '--user',f'{os.getuid()}:{os.getgid()}',
            '--tmpfs','/tmp:rw,nosuid,nodev,size=512m,mode=1777',
            '--mount',f'type=bind,src={PLAN},dst=/plan,readonly']
        for mode,network in [('fetch','bridge'),('install','none')]:
            setup_name='c27-r18-setup-'+os.urandom(8).hex()
            setup = setup_common + ['--name',setup_name,'--network',network,
                '--mount',f'type=bind,src={args.scratch / "wheelhouse"},dst=/wheelhouse'+(',readonly' if mode=='install' else ''),
                '--mount',f'type=bind,src={args.scratch / "venv"},dst=/opt/venv',
                '--mount',f'type=bind,src={args.scratch / "setup-evidence"},dst=/evidence',
                '--entrypoint','python',image,'-B','/plan/support/dependencies.py',mode,args.profile]
            subprocess.run(setup,check=True,stdout=subprocess.DEVNULL)
            try:
                if bounded(['docker','start','--attach',setup_name],args.reports/(mode+'-dependencies.log'),600,args.scratch)!=0:
                    raise RuntimeError(mode+' dependency phase failed; no tests executed')
                setup_state=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',setup_name]))
                (args.reports/(mode+'-container-state.json')).write_text(json.dumps(setup_state,indent=2)+'\n')
                if setup_state['ExitCode']!=0 or setup_state['OOMKilled'] or setup_state['Running']:
                    raise RuntimeError(mode+' container failed')
            finally:
                state=subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',setup_name]).decode().strip()
                if state=='true':
                    subprocess.run(['docker','kill',setup_name],check=True,stdout=subprocess.DEVNULL)
                subprocess.run(['docker','rm',setup_name],check=True,stdout=subprocess.DEVNULL)
        shutil.copytree(args.scratch/'setup-evidence',args.reports/'dependencies')
        identity={'base_image':args.python_image,'base_image_id':subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image]).decode().strip(),
                  'commit':os.environ.get('GITHUB_SHA'),'run_id':os.environ.get('GITHUB_RUN_ID'),
                  'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
                  'requirements_sha256':hashlib.sha256((PLAN/'requirements'/f'{args.profile}.txt').read_bytes()).hexdigest(),
                  'offline_requirements_sha256':hashlib.sha256((PLAN/'requirements'/f'{args.profile}.offline.txt').read_bytes()).hexdigest(),
                  'manifest_sha256':PIN,'uv':'not used; no resolution or sync',
                  'test_network':'none','test_credentials':'none forwarded'}
        (args.reports/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
        contexts=[(args.profile,'learning','input')] if args.profile!='NAMESPACE_INTEGRATION' else [
            ('NAMESPACE_BASE','learning','input'),('NAMESPACE_OVERLAY','acceptance','acceptance')]
        for profile,root,scope in contexts:
            source=args.scratch/'inputs'/root
            collected=run_phase(image,source,scope,profile,True,args.reports/(profile+'-collect'),args.scratch)
            phases.append(collected)
            if collected['status']=='COLLECTION_VERIFIED':
                phases.append(run_phase(image,source,scope,profile,False,args.reports/(profile+'-execute'),args.scratch))
    except Exception as error:
        failure=type(error).__name__+': '+str(error)
        (args.reports/'orchestration-error.log').write_text(traceback.format_exc())
    if (args.scratch/'setup-evidence').is_dir() and not (args.reports/'dependencies').exists():
        shutil.copytree(args.scratch/'setup-evidence',args.reports/'dependencies')
    execution=[p for p in phases if p['phase']=='execute']
    expected_contexts=2 if args.profile=='NAMESPACE_INTEGRATION' else 1
    complete=(failure is None and len(execution)==expected_contexts and all(p['status']=='PASSED' for p in execution))
    total=sum(p.get('actual_call_count') or 0 for p in execution)
    expected={'PDF_PROFILE':96,'UI_PROFILE':9,'NAMESPACE_INTEGRATION':7}[args.profile]
    result={'status':'PASSED' if complete else 'INCOMPLETE_OR_FAILED','expected':expected,
            'actual_call_count':total,'failure':failure,'phases':phases}
    (args.reports/'job-outcomes.json').write_text(json.dumps(result,indent=2)+'\n')
    rows=['| Context | Phase | Status | Collected | Actual calls | Passed calls |',
          '| --- | --- | --- | ---: | ---: | ---: |']
    rows.extend(f"| {p['profile']} | {p['phase']} | {p['status']} | {p.get('collected',0)} | {p.get('actual_call_count',0)} | {p.get('passed_call_count',0)} |" for p in phases)
    (args.reports/'job-report.md').write_text(f"# {args.profile}\n\nStatus: {result['status']}. Expected executions: {expected}; actual call reports: {total}.\n\n"+
                                           '\n'.join(rows)+'\n\n'+(failure or '')+'\n')
    sums=[]
    for artifact in sorted(args.reports.rglob('*')):
        if artifact.is_file() and artifact.name!='SHA256SUMS':
            if artifact.is_symlink():
                raise ValueError('Unexpected artifact symlink')
            sums.append(hashlib.sha256(artifact.read_bytes()).hexdigest()+'  '+str(artifact.relative_to(args.reports)))
    (args.reports/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
    return 0 if complete and total==expected else 1


if __name__=='__main__':
    sys.exit(main())
