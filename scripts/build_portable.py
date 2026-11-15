"""Build the portable Windows ZIP using Python 3.13 and verified TinyCC inputs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen
import zipfile

REPO=Path(__file__).resolve().parent.parent
INPUTS={
    'tcc-0.9.27-win64-bin.zip':'34a721949a2583fdff725312da092fa0f5f1f284b702e6f811c6954714faabb2',
    'tcc-0.9.27.tar.bz2':'de23af78fca90ce32dff2dd45b3432b2334740bb9bb7b05bf60fdbfc396ceb9c',
}
MIRRORS=('https://download-mirror.savannah.gnu.org/releases/tinycc/',
         'https://download.savannah.gnu.org/releases/tinycc/')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(name,cache):
    target=cache/name
    if target.exists() and sha(target)==INPUTS[name]:return target
    errors=[]
    for base in MIRRORS:
        try:
            with urlopen(base+name,timeout=30) as response:data=response.read()
            if hashlib.sha256(data).hexdigest()!=INPUTS[name]:
                raise ValueError('Checksum mismatch for '+name)
            target.write_bytes(data)
            return target
        except (OSError,ValueError) as exc:errors.append(str(exc))
    raise RuntimeError('Could not download '+name+': '+'; '.join(errors))


def build():
    if os.name!='nt' or sys.version_info[:2]!=(3,13):
        raise SystemExit('Build on Windows with 64-bit Python 3.13: py -3.13 scripts/build_portable.py')
    if sys.maxsize<=2**32:raise SystemExit('A 64-bit Python installation is required.')
    cache=REPO/'build'/'downloads';cache.mkdir(parents=True,exist_ok=True)
    inputs={name:download(name,cache) for name in INPUTS}
    output=REPO/'dist';output.mkdir(exist_ok=True)
    version=(REPO/'VERSION').read_text(encoding='utf-8').strip()
    with tempfile.TemporaryDirectory(prefix='portable-',dir=REPO/'build') as temp:
        root=Path(temp)/'SQL-DSA-Lab';root.mkdir()
        app=root/'app';app.mkdir()
        files=('server.py','start.py','engine.py','hospital.py','questions.py','dsa.py',
               'test_dsa.py','test_hospital.py','test_http.py','test_lab.py')
        for name in files:shutil.copy2(REPO/name,app/name)
        shutil.copytree(REPO/'public',app/'public')
        runtime=root/'runtime';runtime.mkdir()
        python=Path(sys.base_prefix)
        for name in ('python.exe','python3.dll','python313.dll','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt'):
            shutil.copy2(python/name,runtime/name)
        dlls=runtime/'DLLs';dlls.mkdir()
        for p in (python/'DLLs').iterdir():
            if p.suffix.lower() in ('.dll','.pyd') and not p.name.startswith('_test') and p.name not in ('_ctypes_test.pyd','_tkinter.pyd','tcl86t.dll','tk86t.dll'):
                shutil.copy2(p,dlls/p.name)
        excluded={'site-packages','__pycache__','test','tests','idlelib','tkinter','turtledemo','ensurepip','venv'}
        with zipfile.ZipFile(runtime/'python313.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in (python/'Lib').rglob('*.py'):
                rel=p.relative_to(python/'Lib')
                if not any(part in excluded for part in rel.parts):z.write(p,rel.as_posix())
        (runtime/'python313._pth').write_text('python313.zip\nDLLs\n../app\n',encoding='ascii')
        compiler=root/'compiler'
        with zipfile.ZipFile(inputs['tcc-0.9.27-win64-bin.zip']) as z:
            for member in z.infolist():
                if member.is_dir():continue
                parts=Path(member.filename).parts
                if parts[0]=='tcc':parts=parts[1:]
                dest=compiler/Path(*parts)
                if not dest.resolve().is_relative_to(compiler.resolve()):raise ValueError('Unsafe compiler archive path')
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(member))
        with tarfile.open(inputs['tcc-0.9.27.tar.bz2']) as tar:
            for name in ('COPYING','README'):
                with tar.extractfile('tcc-0.9.27/'+name) as f:(compiler/name).write_bytes(f.read())
        third=root/'third-party';third.mkdir()
        shutil.copy2(inputs['tcc-0.9.27.tar.bz2'],third/'tcc-0.9.27-source.tar.bz2')
        shutil.copy2(REPO/'scripts'/'start_windows.c',root/'start-source.c')
        subprocess.run([str(compiler/'tcc.exe'),str(root/'start-source.c'),'-o',str(root/'start.exe')],check=True)
        subprocess.run([str(root/'start.exe'),'--help'],check=True,timeout=20)
        (root/'start.cmd').write_text('@echo off\nsetlocal\ncd /d "%~dp0"\n"%~dp0runtime\\python.exe" "%~dp0app\\start.py" --mode dsa %*\nif errorlevel 1 pause\n',encoding='ascii')
        unix='#!/bin/sh\ncd "$(dirname "$0")/app" || exit 1\nexec python3 start.py --mode dsa "$@"\n'
        for name in ('start','start.sh','start.command'):(root/name).write_text(unix,encoding='utf-8')
        shutil.copy2(REPO/'docs'/'PORTABLE_README.txt',root/'README - OPEN FIRST.txt')
        shutil.copy2(REPO/'CHANGELOG.md',root/'CHANGELOG.md')
        paths=[p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
        manifest={'name':'SQL + DSA Lab','version':version,'platform':'Windows x64',
                  'python':sys.version.split()[0],'compiler':'TinyCC 0.9.27',
                  'files':{p.relative_to(root).as_posix():sha(p) for p in paths}}
        (root/'PACKAGE-MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        archive=output/'SQL-DSA-Lab-Portable.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in paths+[root/'PACKAGE-MANIFEST.json']:
                info=zipfile.ZipInfo('SQL-DSA-Lab/'+p.relative_to(root).as_posix())
                info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3
                info.external_attr=((0o100755 if p.name in ('start','start.sh','start.command') else 0o100644)<<16)
                z.writestr(info,p.read_bytes())
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:raise RuntimeError('Archive verification failed')
    (output/'SHA256SUMS.txt').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
    print('Built:',archive)
    print('Size:',round(archive.stat().st_size/1_000_000,2),'MB')


if __name__=='__main__':build()
