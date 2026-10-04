from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules,collect_data_files

root=Path(SPECPATH)
backend=root/'backend'
sys.path.insert(0,str(backend))
hidden=[]
for module in backend.rglob('*.py'):
    if '__pycache__' in module.parts or module.stem in ['launcher','manage','tests']: continue
    relative=module.relative_to(backend).with_suffix('')
    parts=list(relative.parts)
    if parts[-1]=='__init__': parts.pop()
    if parts: hidden.append('.'.join(parts))
for package in ['config','core','services','rest_framework','rest_framework_simplejwt','django.db.backends.sqlite3','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions']:
    hidden+=collect_submodules(package)
datas=[(str(backend/'resources'),'resources'),(str(backend/'frontend_dist'),'frontend_dist')]
for package in ['django','rest_framework','rest_framework_simplejwt']:
    datas+=collect_data_files(package,include_py_files=False)
a=Analysis([str(backend/'launcher.py')],pathex=[str(backend)],binaries=[],datas=datas,hiddenimports=hidden,excludes=['pytest','IPython','matplotlib','numpy','pandas','scipy','core.tests'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='ExamAssistant',debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='ExamAssistant_Windows_x64_Offline')
