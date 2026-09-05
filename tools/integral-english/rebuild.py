"""Clean collection-patch build and local packaging; never writes to the game.

Nine families: the eight of 2026-09-04 plus en_abst (the MISSION LOG, added
2026-09-05), whose overlay abst.bin is compiled alongside option.bin and
preope.bin.

Usage: py rebuild.py --output D:/mgsbuild/repro1 [--compare-deployed]
Requires the local decomp Git repository, PSYQ SDK, and installed collection.
The output directory must not exist. It retains inputs, logs and build hashes.
"""
from pathlib import Path
import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
import tarfile
import zipfile
from iso import Disc
from portio import (INTEGRAL_IMAGES, USA_IMAGES, stage, relocation, sha256,
                    read_ppf)

TOOLS = Path(__file__).resolve().parent
FAMILIES = ('items', 'menu', 'menu2', 'preope', 'brf', 'option', 'savemsg', 'camsave', 'abst')
BASE = '7964de7'
EXE_HASHES = {
    'int1.exe': '4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f',
    'int2.exe': '4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f',
    'us1.exe': '615e136083336957ed0b9b3805145bf5bbb35f7a16c2f160dba8f17bb71cc640',
    'us2.exe': '615e136083336957ed0b9b3805145bf5bbb35f7a16c2f160dba8f17bb71cc640',
}


def run(args, cwd, env, log):
    with log.open('ab') as stream:
        stream.write(('\n'+repr([str(a) for a in args])+'\n').encode())
        result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Command failed; see '+str(log))


def extract(game, work, executables):
    inputs = {}
    for prefix, container, bases, boots in (
        ('int', 'windata/dlc/dlc_japan.bin', INTEGRAL_IMAGES, ('SLPM_862.47','SLPM_862.48')),
        ('usa', 'windata/alldata.bin', USA_IMAGES, ('SLUS_005.94','SLUS_007.76'))):
        for disc, (base, boot) in enumerate(zip(bases, boots), 1):
            image = Disc(game/container, base)
            try:
                files = {n.upper(): (l,s) for n,l,s,d in image.walk() if not d}
                for name, key in ((prefix+str(disc)+'_stage.dir','/MGS/STAGE.DIR;1'),
                                  (('us' if prefix=='usa' else prefix)+str(disc)+'.exe','/MGS/'+boot+';1')):
                    lba, size = files[key]
                    data = image.read(lba,size)
                    source = 'collection ISO'
                    if name.endswith('.exe'):
                        # The collection preloads code from RAM snapshots and
                        # leaves these ISO executable extents zero-filled.
                        data = (executables/name).read_bytes()
                        assert data[:8] == b'PS-X EXE' and len(data) == size, name
                        assert sha256(data) == EXE_HASHES[name], 'unsupported retail executable: '+name
                        source = 'separately supplied retail PS-X EXE'
                    (work/name).write_bytes(data)
                    inputs[name] = dict(container=container, image_base=base, iso_path=key,
                                        source=source, lba=lba, bytes=size, sha256=sha256(data))
            finally:
                image.f.close()
    return inputs


def effects(path, image):
    """Effective changed bytes, independent of PPF descriptions/run boundaries."""
    result = {}
    for offset, payload in read_ppf(path):
        within = offset % 2352
        assert 24 <= within and within+len(payload) <= 2072, 'sector-tail write'
        image.f.seek(image.base+offset)
        original = image.f.read(len(payload))
        assert len(original) == len(payload)
        for k, (old,new) in enumerate(zip(original,payload)):
            if new != old:
                result[offset+k] = new
            else:
                result.pop(offset+k,None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--game', type=Path, default=Path('D:/Steam/SteamApps/common/MGS1'))
    parser.add_argument('--decomp', type=Path, default=Path('D:/mgsbuild/d'))
    parser.add_argument('--psyq', type=Path, default=Path('D:/mgsbuild/psyq'))
    parser.add_argument('--executables', type=Path,
                        default=Path('D:/mgsbuild/integral-english-work/work'))
    parser.add_argument('--compare-deployed', action='store_true')
    args = parser.parse_args()
    output, game, source, psyq = (p.resolve() for p in (args.output,args.game,args.decomp,args.psyq))
    if output.exists():
        parser.error('output must be a new directory; existing runs are never overwritten')
    if len(str(output)) > 65 or ' ' in str(output):
        parser.error('use a short path without spaces for the PSYQ toolchain')
    output.mkdir(parents=True)
    work = output/'work'
    work.mkdir()
    decomp = output/'decomp'
    decomp.mkdir()
    log = output/'build.log'
    env = dict(os.environ, INTEGRAL_ENGLISH_WORK=str(output),
               INTEGRAL_ENGLISH_GAME=str(game), INTEGRAL_ENGLISH_DECOMP=str(decomp),
               PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    report = dict(variant='collection', base_commit=subprocess.check_output(
        ['git','-C',str(source),'rev-parse',BASE],text=True).strip(),
        python=sys.version, packages={n:importlib.metadata.version(n)
                                    for n in ('Pillow','ninja')}, inputs={}, outputs={})
    report['sources'] = {p.name:sha256(p.read_bytes()) for p in sorted(TOOLS.iterdir())
                         if p.suffix in ('.py','.patch','.json')}
    report['sdk_files'] = {p.relative_to(psyq).as_posix():sha256(p.read_bytes())
                           for p in sorted(psyq.rglob('*'))
                           if p.is_file() and '.git' not in p.relative_to(psyq).parts}
    print('Extracting original Integral and USA files...',flush=True)
    report['inputs'] = extract(game,work,args.executables.resolve())
    print('Compiling overlays in an isolated decomp export...',flush=True)
    archive = output/'decomp-source.tar'
    run(['git','-C',source,'archive','--format=tar','--output',archive,BASE],TOOLS,env,log)
    with tarfile.open(archive) as tar:
        tar.extractall(decomp,filter='data')
    patch = TOOLS/'decomp-overlay-changes.patch'
    run(['git','apply','--check',patch],decomp,env,log)
    run(['git','apply',patch],decomp,env,log)
    # Exported build.py normally builds/compares the entire matching game.
    # Stop after generation so only the three changed overlays are compiled.
    generator = decomp/'build/build.py'
    text = generator.read_text(encoding='utf-8')
    marker = 'time_before = time.time()'
    assert text.count(marker) == 1
    generator.write_text(text.split(marker)[0]+'sys.exit(0)\n',encoding='utf-8')
    run([sys.executable,'build.py','--psyq_path',psyq,'--variant','main_exe'],decomp/'build',env,log)
    run([sys.executable,'-m','ninja','-j','2','../obj/preope.bin','../obj/option.bin','../obj/abst.bin'],decomp/'build',env,log)
    report['overlays'] = {n:sha256((decomp/'obj'/(n+'.bin')).read_bytes()) for n in ('option','preope','abst')}
    # Only source geometry is copied; all derived placements are regenerated.
    (work/'brf_quads_all.json').write_bytes((TOOLS/'brf_quads_all.json').read_bytes())
    print('Building nine patch families...',flush=True)
    for script in ('items.py','menu2.py','preope_usa.py','brf_build.py','optsctext.py',
                   'savemsg.py','camsave.py','abst_build.py'):
        run([sys.executable,TOOLS/script],TOOLS,env,log)
    dist = output/'package'
    mods = dist/'mods/INTEGRAL/INTEGRAL'
    for disc, base in enumerate(INTEGRAL_IMAGES):
        image = Disc(game/'windata/dlc/dlc_japan.bin',base)
        target = mods/str(disc)
        target.mkdir(parents=True)
        try:
            brf = relocation(image,'brf',(work/'brf_en.bin').read_bytes(),128,
                             'MGS Integral: English brf')
            (work/('INTEGRAL_disc%d_en_brf.ppf' % (disc+1))).write_bytes(brf)
            for family in FAMILIES:
                name = 'INTEGRAL_disc%d_en_%s.ppf' % (disc+1,family)
                built = work/('option_sctext_disc%d.ppf' % (disc+1)) if family=='option' else work/name
                (target/name).write_bytes(built.read_bytes())
                from ppfcheck import check
                problems,n,span,desc = check(target/name)
                assert not problems, (name,problems)
                effective = effects(target/name,image)
                item = dict(sha256=sha256(built.read_bytes()),bytes=built.stat().st_size,
                            records=n,changed_bytes=len(effective))
                if args.compare_deployed:
                    reference = game/'mods/INTEGRAL/INTEGRAL'/str(disc)/name
                    prior = effects(reference,image)
                    mismatch = [p for p in effective.keys() | prior.keys() if effective.get(p)!=prior.get(p)]
                    item['reference_sha256'] = sha256(reference.read_bytes())
                    item['reference_effect_equal'] = not mismatch
                    item['difference_count'] = len(mismatch)
                    item['difference_addresses'] = [hex(p) for p in sorted(mismatch)[:12]]
                report['outputs'][name] = item
        finally:
            image.f.close()
    # Check overlapping writes in the actual packaged set, before offering it.
    for disc in (0,1):
        writes = {}
        for path in sorted((mods/str(disc)).glob('*.ppf')):
            for off,data in read_ppf(path):
                for k,value in enumerate(data):
                    assert off+k not in writes or writes[off+k][0] == value, (path.name,hex(off+k),writes[off+k][1])
                    writes[off+k] = (value,path.name)
    (output/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    bad = [n for n,v in report['outputs'].items() if v.get('reference_effect_equal') is False]
    if bad:
        raise RuntimeError('Deployed comparison differs: '+', '.join(bad)+'; see build-report.json. No ZIP created.')
    (dist/'README.txt').write_bytes((TOOLS/'PACKAGE-README.txt').read_bytes())
    (dist/'build-report.json').write_bytes((output/'build-report.json').read_bytes())
    manifest = {str(p.relative_to(dist)).replace('\\','/'):sha256(p.read_bytes())
                for p in sorted(dist.rglob('*')) if p.is_file()}
    (dist/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()),encoding='utf-8')
    # Fixed ZIP metadata and ordering; the report records the build environment.
    zip_path = output/'Integral-English-collection.zip'
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(dist.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(dist).as_posix(),(2026,9,4,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info,path.read_bytes())
    print('Verified %d PPFs; %s' % (2*len(FAMILIES), zip_path),flush=True)


if __name__ == '__main__':
    main()
