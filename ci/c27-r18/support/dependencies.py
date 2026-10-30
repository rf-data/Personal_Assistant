"""Approved future CI only: fetch hashed wheels, then install without any network."""
import hashlib
import json
import os
import platform
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

PLAN = Path(__file__).resolve().parents[1]


def verify(wheelhouse, packages):
    expected = {p['filename'] for p in packages}
    if {p.name for p in wheelhouse.iterdir()} != expected:
        raise ValueError('Wheelhouse set differs from locked closure')
    evidence = []
    for package in packages:
        wheel = wheelhouse/package['filename']
        if wheel.is_symlink() or not wheel.is_file() or wheel.stat().st_size != package['size']:
            raise ValueError('Wheel size/type mismatch')
        actual = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if 'sha256:'+actual != package['hash']:
            raise ValueError('Wheel SHA-256 mismatch')
        with zipfile.ZipFile(wheel) as archive:
            metadata = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
            if len(metadata) != 1:
                raise ValueError('Ambiguous wheel metadata')
            from email.parser import BytesParser
            msg = BytesParser().parsebytes(archive.read(metadata[0]))
        if msg['Name'].lower().replace('_','-') != package['name'].lower().replace('_','-') or msg['Version'] != package['version']:
            raise ValueError('Wheel metadata identity mismatch')
        evidence.append({'filename':wheel.name,'sha256':actual,'bytes':wheel.stat().st_size,
                         'requires_python':msg['Requires-Python'],'requires_dist':msg.get_all('Requires-Dist',[])})
    return evidence


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirects forbidden during controlled wheel procurement')


def main():
    os.umask(0o022)
    mode, profile = sys.argv[1:]
    if mode not in ('fetch','install') or profile not in ('PDF_PROFILE','UI_PROFILE','NAMESPACE_INTEGRATION'):
        raise ValueError('Unsupported dependency phase/profile')
    if sys.version_info[:2] != (3,12) or platform.machine() != 'x86_64':
        raise ValueError('CPython 3.12 Linux x86_64 required')
    cgroup=Path('/sys/fs/cgroup')
    limits={n:(cgroup/n).read_text().strip() for n in ('memory.max','memory.swap.max','pids.max','cpu.max')}
    quota,period=limits['cpu.max'].split()
    if (limits['memory.max']=='max' or int(limits['memory.max'])>4*1024**3 or limits['memory.swap.max']!='0'
        or limits['pids.max']=='max' or int(limits['pids.max'])>256 or quota=='max' or int(quota)>2*int(period)):
        raise ValueError('Setup cgroup isolation not enforced')
    resolution=json.loads((PLAN/'support/dependency_resolution.json').read_text())
    packages=resolution['profiles'][profile]['packages']
    # Resolution metadata is cross-checked against the immutable original requirements.
    online=(PLAN/'requirements'/f'{profile}.txt').read_text()
    offline=(PLAN/'requirements'/f'{profile}.offline.txt').read_text()
    for package in packages:
        if package['url'] not in online or package['hash'] not in online:
            raise ValueError('Resolution/original requirements mismatch')
    if offline != ''.join(f"{p['name']}=={p['version']} --hash={p['hash']}\n" for p in packages):
        raise ValueError('Offline requirements drift')
    wheelhouse=Path('/wheelhouse')
    if mode=='fetch':
        if list(wheelhouse.iterdir()):
            raise ValueError('Fresh wheelhouse required')
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirects())
        for package in packages:
            url=urllib.parse.urlsplit(package['url'])
            if (url.scheme!='https' or url.netloc!='files.pythonhosted.org' or url.query or url.fragment
                    or Path(url.path).name != package['filename'] or '/' in package['filename'] or not package['filename'].endswith('.whl')):
                raise ValueError('URL not in reviewed HTTPS wheel allowlist')
            digest=hashlib.sha256(); total=0
            with opener.open(package['url'],timeout=60) as response, (wheelhouse/package['filename']).open('xb') as target:
                while chunk:=response.read(1024*1024):
                    total+=len(chunk)
                    if total>package['size']:
                        raise ValueError('Download size exceeds lock')
                    digest.update(chunk); target.write(chunk)
            if total!=package['size'] or 'sha256:'+digest.hexdigest()!=package['hash']:
                raise ValueError('Downloaded wheel does not match lock')
    wheels=verify(wheelhouse,packages)
    (Path('/evidence')/(mode+'-wheels.json')).write_text(json.dumps({'phase':mode,'profile':profile,'cgroup':limits,'wheels':wheels},indent=2)+'\n')
    if mode=='install':
        subprocess.run([sys.executable,'-m','venv','/opt/venv'],check=True)
        pip=['/opt/venv/bin/python','-m','pip','--isolated','--disable-pip-version-check']
        subprocess.run(pip+['install','--no-cache-dir','--no-compile','--no-index','--no-deps','--require-hashes',
                           '--only-binary=:all:','--find-links','/wheelhouse','--report','/evidence/install-report.json',
                           '-r',str(PLAN/'requirements'/f'{profile}.offline.txt')],check=True)
        subprocess.run(pip+['check'],check=True)
        versions=subprocess.check_output(pip+['list','--format=json']).decode()
        Path('/evidence/package-versions.json').write_text(versions)
        Path('/evidence/python-version.txt').write_text(sys.version+'\n')
    print(json.dumps({'phase':mode,'profile':profile,'wheels_verified':len(wheels),'installed':mode=='install'}))


if __name__=='__main__':
    main()
