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
# The VR disc's own port (2026-09-06/07). Its tools are separate because the disc
# is a separate game - its own executable, overlays and containers - but the
# build is the same discipline, so it belongs in the same isolated run.
VR_SCRIPTS = ('vr_windows.py --build', 'vr_exe.py', 'vr_option.py', 'vr_menus.py',
              'vr_camera.py', 'vr_movie.py')
VR_FAMILIES = ('missions', 'items', 'savemsg', 'option', 'title', 'camsave', 'movie')
VR_EXE_HASHES = {
    # Integral's VR executable is not on the collection's disc in usable form,
    # so it is BUILT from the decomp here (obj_vr/_mgsi.exe) and checked against
    # this hash rather than copied in. USA's is a supplied retail input.
    'vrint.exe': 'c370f8e41ec8fb78238bfe2ddbfc25a6d37ec8f0972c86ebfde075ecd4ee8dca',
    'vrus.exe': '8e8e59a97b5cc7cec137dd782fdeaa09097de1e53b1801c5617aa9132a2fb814',
}
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
    # The VR disc is a third and fourth image, inside the same two containers.
    # vrlib knows where; this only needs STAGE.DIR out of each.
    from vrlib import INT_VR_BASE, USA_VR_BASE
    for name, container, base in (('vrint_stage.dir', 'windata/dlc/dlc_japan.bin', INT_VR_BASE),
                                  ('vrus_stage.dir', 'windata/alldata.bin', USA_VR_BASE)):
        image = Disc(game/container, base)
        try:
            lba, size = next((l, s) for n, l, s, d in image.walk()
                             if not d and n.upper() == '/MGS/STAGE.DIR;1')
            data = image.read(lba, size)
            (work/name).write_bytes(data)
            inputs[name] = dict(container=container, image_base=base, iso_path='/MGS/STAGE.DIR;1',
                                source='collection ISO (VR)', lba=lba, bytes=size, sha256=sha256(data))
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
    parser.add_argument('--variant', choices=('collection', 'raw'), default='collection',
                        help='collection (the default, what mods/ gets) or raw, for a real PSX '
                             'disc image: SC_KEEP_LINES 6, OPTION_MC_CONTROL_SETTINGS 0, and '
                             'en_menu3 included')
    parser.add_argument('--compare-deployed', action='store_true')
    args = parser.parse_args()
    output, game, source, psyq = (p.resolve() for p in (args.output,args.game,args.decomp,args.psyq))
    if output.exists():
        parser.error('output must be a new directory; existing runs are never overwritten')
    if args.variant == 'raw' and args.compare_deployed:
        parser.error('--compare-deployed compares against mods/, which is the collection build')
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
               INTEGRAL_ENGLISH_VARIANT=args.variant,
               PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    report = dict(variant=args.variant, base_commit=subprocess.check_output(
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
    # The second variant constant lives in the decomp, not in a tool: opt.c
    # reproduces the collection's KEY CONFIG doorbell, which a raw PSX disc has
    # nothing to intercept and no RAM at 0x80200000 to write. Flip it in the
    # isolated export so the compiled overlay matches the variant.
    optc = decomp/'source/onoda/option/opt.c'
    want = '#define OPTION_MC_CONTROL_SETTINGS %d' % (0 if args.variant == 'raw' else 1)
    text = optc.read_text(encoding='utf-8')
    assert text.count('#define OPTION_MC_CONTROL_SETTINGS 1') == 1, 'opt.c constant moved'
    optc.write_text(text.replace('#define OPTION_MC_CONTROL_SETTINGS 1', want), encoding='utf-8')
    report['variant_constants'] = {'OPTION_MC_CONTROL_SETTINGS': 0 if args.variant == 'raw' else 1,
                                   'SC_KEEP_LINES': 6 if args.variant == 'raw' else 4}
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
    # Integral's VR executable: the collection's copy is unusable, so it is built
    # here rather than trusted. The generator has to run again for the vr_exe
    # variant (it writes a different ninja file), then one target.
    print('Building the VR executable from the decomp...',flush=True)
    run([sys.executable,'build.py','--psyq_path',psyq,'--variant','vr_exe'],decomp/'build',env,log)
    run([sys.executable,'-m','ninja','-j','2','../obj_vr/_mgsi.exe'],decomp/'build',env,log)
    vrint = (decomp/'obj_vr/_mgsi.exe').read_bytes()
    assert sha256(vrint) == VR_EXE_HASHES['vrint.exe'], 'the rebuilt VR executable is not the expected build'
    (work/'vrint.exe').write_bytes(vrint)
    report['inputs']['vrint.exe'] = dict(source='built here from the decomp (obj_vr/_mgsi.exe)',
                                         bytes=len(vrint), sha256=sha256(vrint))
    vrus = (args.executables.resolve()/'vrus.exe').read_bytes()
    assert sha256(vrus) == VR_EXE_HASHES['vrus.exe'], 'unsupported USA VR executable'
    (work/'vrus.exe').write_bytes(vrus)
    report['inputs']['vrus.exe'] = dict(source='separately supplied retail SLUS-00957',
                                        bytes=len(vrus), sha256=sha256(vrus))
    # Only source geometry is copied; all derived placements are regenerated.
    (work/'brf_quads_all.json').write_bytes((TOOLS/'brf_quads_all.json').read_bytes())
    scripts = ['items.py','menu2.py','preope_usa.py','brf_build.py','optsctext.py',
               'savemsg.py','camsave.py','abst_build.py']
    families = list(FAMILIES)
    if args.variant == 'raw':
        # en_menu3 exists only here: the collection patches that same block, so
        # deploying it there kills the title stage (README, "Why `en_menu3` is
        # raw-disc only"). menu3.py refuses --deploy for the same reason.
        scripts.append('menu3.py')
        families.append('menu3')
    print('Building %d patch families (%s)...' % (len(families), args.variant),flush=True)
    for script in scripts:
        run([sys.executable,TOOLS/script],TOOLS,env,log)
    print('Building the VR disc: seven patches (vr_windows rebuilds 92 stages)...',flush=True)
    for script in VR_SCRIPTS:
        parts = script.split()
        # vr_movie composes on the PPFs this run just made, not on a deployed set
        run([sys.executable,TOOLS/parts[0]]+parts[1:],TOOLS,
            dict(env,INTEGRAL_ENGLISH_VR_PPF_DIR=str(work)),log)
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
            for family in families:
                name = 'INTEGRAL_disc%d_en_%s.ppf' % (disc+1,family)
                built = work/name
                if family == 'option':
                    built = work/('option_sctext_disc%d.ppf' % (disc+1))
                elif family == 'menu3':
                    built = work/('INTEGRAL_disc%d_en_menu3_raw.ppf' % (disc+1))
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
    # The VR disc's own folder. Ketchup gives it no numbered subdirectory (one
    # disk in that version), and its PPF offsets address a different image, so
    # it gets its own overlap check below rather than joining the main one.
    from vrlib import INT_VR_BASE
    vrmods = dist/'mods/INTEGRAL/VR-DISK'
    vrmods.mkdir(parents=True)
    vrimage = Disc(game/'windata/dlc/dlc_japan.bin',INT_VR_BASE)
    try:
        for family in VR_FAMILIES:
            name = 'INTEGRAL_vr_en_%s.ppf' % family
            built = work/name
            (vrmods/name).write_bytes(built.read_bytes())
            from ppfcheck import check
            problems,n,span,desc = check(vrmods/name)
            assert not problems, (name,problems)
            report['outputs'][name] = dict(sha256=sha256(built.read_bytes()),
                                           bytes=built.stat().st_size,records=n,
                                           changed_bytes=len(effects(vrmods/name,vrimage)))
            if args.compare_deployed:
                reference = game/'mods/INTEGRAL/VR-DISK'/name
                prior, effective = effects(reference,vrimage), effects(vrmods/name,vrimage)
                mismatch = [p for p in effective.keys() | prior.keys() if effective.get(p)!=prior.get(p)]
                report['outputs'][name]['reference_sha256'] = sha256(reference.read_bytes())
                report['outputs'][name]['reference_effect_equal'] = not mismatch
                report['outputs'][name]['difference_count'] = len(mismatch)
                report['outputs'][name]['difference_addresses'] = [hex(p) for p in sorted(mismatch)[:12]]
    finally:
        vrimage.f.close()
    # vr_en_movie deliberately overlaps vr_en_missions - it is built on top of it
    # and must land last, which Ketchup's name order gives (README, "The
    # composite trap"). So the VR set is checked for overlaps EXCEPT that pair.
    vrwrites = {}
    for path in sorted(vrmods.glob('*.ppf')):
        for off,data in read_ppf(path):
            for k,value in enumerate(data):
                prior = vrwrites.get(off+k)
                if prior and prior[1] != path.name:
                    pair = {prior[1],path.name}
                    assert pair == {'INTEGRAL_vr_en_missions.ppf','INTEGRAL_vr_en_movie.ppf'},                         (path.name,hex(off+k),prior[1])
                vrwrites[off+k] = (value,path.name)
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
    zip_path = output/('Integral-English-%s.zip' % args.variant)
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(dist.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(dist).as_posix(),(2026,9,4,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info,path.read_bytes())
    print('Verified %d PPFs (%s variant, %d main + %d VR); %s'
          % (2*len(families)+len(VR_FAMILIES), args.variant, 2*len(families), len(VR_FAMILIES), zip_path),flush=True)


if __name__ == '__main__':
    main()
