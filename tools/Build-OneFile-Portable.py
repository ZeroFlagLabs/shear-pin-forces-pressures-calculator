"""Rebuild the portable Windows application from this source."""
from pathlib import Path
import argparse,hashlib,re,subprocess,sys,zipfile
from PySide6 import __file__ as pyside_file
from PyInstaller.archive.readers import CArchiveReader
ROOT=Path(__file__).resolve().parents[1]
def run(args):
    subprocess.run([str(x) for x in args],cwd=ROOT,check=True)
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=ROOT/"dist");a=parser.parse_args()
    dest=a.output.resolve();dest.mkdir(parents=True,exist_ok=True)
    info=(ROOT/"src/app_info.py").read_text()
    version=re.search(r"^APP_VERSION = '([^']+)'$",info,re.M).group(1)
    name=f"Shear Pin Forces & Pressures Calculator v{version}"
    zip_path=dest/f"Shear-Pin-Forces-Pressures-Calculator-v{version}-Windows-Portable.zip"
    if zip_path.exists():raise RuntimeError("Refusing to overwrite existing release ZIP")
    schannel=Path(pyside_file).parent/"plugins/tls/qschannelbackend.dll"
    assert schannel.is_file()
    specdir=dest/"spec";specdir.mkdir(exist_ok=True)
    cmd=[sys.executable,"-m","PyInstaller.utils.cliutils.makespec","--onefile","--windowed","--name",name,"--paths",ROOT/"src","--specpath",specdir,"--icon",ROOT/"src/resources/icons/icon.ico",
         "--add-data",str(ROOT/"src/resources")+";resources","--add-data",str(ROOT/"src/ui")+";ui",
         "--add-binary",str(schannel)+";PySide6/plugins/tls",ROOT/"src/main.py"]
    run(cmd)
    spec=specdir/(name+".spec");s=spec.read_text(encoding="utf8");m=re.search(r"^pyz\s*=\s*PYZ\(",s,re.M);assert m
    patch="""# Remove unused Virtual Keyboard and PDF image format components.
blocked={'qt6virtualkeyboard.dll','qtvirtualkeyboardplugin.dll','qt6pdf.dll','qpdf.dll'}
for attr in ('binaries','datas'):
    setattr(a,attr,[e for e in getattr(a,attr) if e[0].replace(chr(92),'/').rsplit('/',1)[-1].lower() not in blocked])
"""
    s=s[:m.start()]+patch+s[m.start():];compile(s,str(spec),"exec");spec.write_text(s,encoding="utf8")
    run([sys.executable,"-m","PyInstaller","--noconfirm","--clean","--workpath",dest/"work","--distpath",dest/"exe",spec])
    exe=dest/"exe"/(name+".exe")
    archive=CArchiveReader(str(exe))
    listing=[k.replace(chr(92),"/").lower() for k in archive.toc]
    for suffix in ("qschannelbackend.dll","resources/icons/settings-gear.png","resources/icons/spin-chevron-up.png","resources/icons/icon.ico","ui/settings_dialog.ui","ui/inspect_results.ui"):
        assert any(k.endswith(suffix) for k in listing),suffix
    assert not any(k.rsplit("/",1)[-1] in {"qt6virtualkeyboard.dll","qtvirtualkeyboardplugin.dll","qt6pdf.dll","qpdf.dll"} for k in listing)
    assert not any("_ui_preview" in k or "docs/private" in k for k in listing)
    (dest/"archive_inventory.txt").write_text("\n".join(sorted(listing)),encoding="utf8")
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.write(exe,exe.name)
    with zipfile.ZipFile(zip_path) as z:
        assert z.namelist()==[exe.name] and z.testzip() is None
    digest=hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (dest/(zip_path.name+".sha256")).write_text(digest+"  "+zip_path.name+"\n",encoding="ascii")
    print("ZIP:",zip_path,"SHA256:",digest,"EXE bytes:",exe.stat().st_size,"ZIP bytes:",zip_path.stat().st_size,flush=True)
if __name__=="__main__":main()
