"""Assemble a clean offline delivery. Never includes live data, secrets or development caches."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sqlite3
from contextlib import closing
import zipfile

SOURCE=Path(__file__).resolve().parent.parent
EXCLUDED={'.venv','node_modules','__pycache__','build','dist','data','.git'}

def source_files():
    for file in SOURCE.rglob('*'):
        relative=file.relative_to(SOURCE)
        if file.is_file() and not any(part in EXCLUDED for part in relative.parts) and file.suffix not in ['.pyc','.log']:
            yield file,relative

def write_code_text(output):
    chunks=['报考小助手 2.0 完整工程源码（按模块分区）\n说明：这是真实可编辑源码，不是反编译字节码清单。\n']
    for file,relative in source_files():
        if file.suffix in ['.py','.vue','.js','.cjs','.css','.json','.yaml','.toml','.spec','.cmd'] and 'frontend_dist' not in relative.parts:
            chunks.append('\n'+'='*80+'\n模块 / 文件：'+relative.as_posix()+'\n'+'='*80+'\n'+file.read_text(encoding='utf-8')+'\n')
    (output/'工程源码_按模块.txt').write_text(''.join(chunks),encoding='utf-8')

def write_archives(output,runtime):
    customer=output/'ExamAssistant_Offline_v2_客户运行包.zip'
    with zipfile.ZipFile(customer,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file in runtime.rglob('*'):
            if file.is_file():archive.write(file,file.relative_to(output).as_posix())
    complete=output/'ExamAssistant_Offline_v2_完整交付包.zip'
    with zipfile.ZipFile(complete,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for file in runtime.rglob('*'):
            if file.is_file():archive.write(file,file.relative_to(output).as_posix())
        for file,relative in source_files():archive.write(file,'source/'+relative.as_posix())
        for name in ['一键启动.cmd','交付说明.txt','工程源码_按模块.txt','SQLite数据.txt','SQLite初始数据.sqlite3']:archive.write(output/name,name)
    manifest={file.name:{'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()} for file in [customer,complete,output/'工程源码_按模块.txt',output/'SQLite数据.txt']}
    (output/'交付文件校验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-root',type=Path,default=SOURCE.parent)
    parser.add_argument('--refresh-artifacts',action='store_true',help='只刷新未使用过的交付目录的说明、源码汇总和 ZIP，不覆盖运行文件或数据库。')
    args=parser.parse_args()
    output=args.output_root.resolve();output.mkdir(parents=True,exist_ok=True)
    runtime=output/'ExamAssistant_Offline_v2'
    if args.refresh_artifacts:
        if not (runtime/'ExamAssistant.exe').is_file() or any((runtime/'data').rglob('*')):
            raise RuntimeError('仅允许刷新已有且 data 为空的交付目录。')
        shutil.copytree(SOURCE/'docs',runtime/'docs',dirs_exist_ok=True)
        shutil.copy2(SOURCE/'README.md',runtime/'README.md')
        write_code_text(output)
        write_archives(output,runtime)
        return
    if runtime.exists(): raise RuntimeError('拒绝覆盖已有运行目录（可能包含客户数据）。请指定新的 --output-root。')
    built=SOURCE/'dist'/'ExamAssistant_Windows_x64_Offline'
    if not (built/'ExamAssistant.exe').is_file():raise RuntimeError('请先构建可执行文件。')
    shutil.copytree(built,runtime)
    (runtime/'data').mkdir()
    (runtime/'一键启动.cmd').write_text('@echo off\r\nstart "" "%~dp0ExamAssistant.exe"\r\n',encoding='utf-8')
    (output/'一键启动.cmd').write_text('@echo off\r\nstart "" "%~dp0ExamAssistant_Offline_v2\\ExamAssistant.exe"\r\n',encoding='utf-8')
    for directory in ['docs']:
        shutil.copytree(SOURCE/directory,runtime/directory)
    shutil.copy2(SOURCE/'README.md',runtime/'README.md')
    instructions='报考小助手 离线重构版 2.0\n\n请完整解压后双击 一键启动.cmd。无需安装 Python 或 Node.js，无需联网。\n不要单独发送 exe：必须发送完整文件夹或客户运行包 ZIP。\n\n管理员：admin / Admin@123456\n普通体验账号：demo / Demo@123456\n正式使用请先修改密码。\n\n动态登录、骨架加载、卡片入场和演示导航已加入。Alt+D 打开演示导航。\n公共服务与报考数据管理为新增完整模块。\n\n数据保存在运行目录 data/db.sqlite3，备份包含个人信息。请保留整个 data 目录。\n移动程序请先关闭启动器，再移动完整目录。\n\n源码在 source 文件夹；按模块汇总文本为 工程源码_按模块.txt，数据SQL为 SQLite数据.txt。\n详细功能、测试、开发与运行边界见 source/docs 和 source/README.md。\n'
    (output/'交付说明.txt').write_text(instructions,encoding='utf-8')
    (runtime/'使用说明.txt').write_text(instructions,encoding='utf-8')
    licenses=runtime/'licenses';licenses.mkdir()
    for distribution in importlib.metadata.distributions():
        for item in distribution.files or []:
            if Path(str(item)).name.lower().startswith(('license','copying','copyright')):
                file=Path(distribution.locate_file(item))
                if file.is_file():
                    folder=licenses/distribution.metadata['Name'];folder.mkdir(exist_ok=True)
                    shutil.copy2(file,folder/file.name)
    for name,relative in [('vue','vue'),('vue-router','vue-router'),('lucide','@lucide/vue')]:
        directory=SOURCE/'frontend'/'node_modules'/relative
        for file in directory.glob('*'):
            if file.is_file() and file.name.lower().startswith(('license','copying')):
                folder=licenses/name;folder.mkdir(exist_ok=True);shutil.copy2(file,folder/file.name)
    write_code_text(output)
    # Produce SQL from a pristine migrated seed, never from a QA or customer database.
    temporary=output/'sql_seed_work'
    temporary.mkdir()
    import subprocess,sys,os
    env={**os.environ,'EXAM_DATA_DIR':str(temporary),'PYTHONIOENCODING':'utf-8'}
    shutil.copy2(SOURCE/'backend'/'resources'/'db_seed.sqlite3',temporary/'db.sqlite3')
    subprocess.run([sys.executable,str(SOURCE/'backend'/'manage.py'),'migrate','--noinput'],env=env,check=True,stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable,str(SOURCE/'backend'/'manage.py'),'seed_services'],env=env,check=True,stdout=subprocess.DEVNULL)
    with closing(sqlite3.connect(temporary/'db.sqlite3')) as connection:
        sql='-- 原离线种子数据 + 重构新增结构与服务指南；不含客户运行数据。\n-- SQLite SQL，UTF-8。密码字段为原有哈希，不是明文。\n'+'\n'.join(connection.iterdump())+'\n'
    (output/'SQLite数据.txt').write_text(sql,encoding='utf-8')
    shutil.copy2(temporary/'db.sqlite3',output/'SQLite初始数据.sqlite3')
    # This exact directory was created by this invocation and contains only our scratch seed.
    assert temporary.parent==output and temporary.name=='sql_seed_work'
    shutil.rmtree(temporary)
    write_archives(output,runtime)

if __name__=='__main__':main()
