"""Portable Windows launcher: first-run seed, migration, local server and splash UI."""
import argparse
import ctypes
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import queue
import shutil
import socket
import sqlite3
import sys
import threading
import time
import urllib.request
import webbrowser
from contextlib import closing

FROZEN=bool(getattr(sys,'frozen',False))
RESOURCE=Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parent
DEFAULT_ROOT=Path(sys.executable).parent if FROZEN else RESOURCE.parent
EVENTS=queue.Queue()
SERVER=None


def progress(message,value):
    logging.info(message)
    EVENTS.put(('progress',message,value))


def initialize(data_dir,port):
    global SERVER
    os.environ['EXAM_RESOURCE_DIR']=str(RESOURCE)
    os.environ['EXAM_DATA_DIR']=str(data_dir)
    os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
    db=data_dir/'db.sqlite3'
    if not db.exists():
        progress('正在初始化本地数据…',20)
        shutil.copy2(RESOURCE/'resources'/'db_seed.sqlite3',db)
    with closing(sqlite3.connect(db)) as connection:
        if connection.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise RuntimeError('本地数据库检查失败。请保留 data 文件夹，使用有效备份恢复。')
    progress('正在检查数据结构…',42)
    import django
    django.setup()
    from django.core.management import call_command
    from io import StringIO
    output=StringIO()
    call_command('migrate',interactive=False,stdout=output,verbosity=0)
    call_command('seed_services',stdout=output,verbosity=0)
    progress('正在加载离线工作台…',72)
    from django.core.wsgi import get_wsgi_application
    from waitress import create_server
    application=get_wsgi_application()
    for candidate in range(port,port+30):
        try:
            SERVER=create_server(application,host='127.0.0.1',port=candidate,threads=4,max_request_body_size=110*1024*1024)
            port=candidate
            break
        except OSError:
            continue
    if SERVER is None: raise RuntimeError('找不到可用本机端口，请关闭占用程序后重试。')
    url=f'http://127.0.0.1:{port}'
    thread=threading.Thread(target=SERVER.run,daemon=True,name='offline-web-server')
    thread.start()
    for _ in range(60):
        try:
            with urllib.request.urlopen(url+'/api/v1/health/',timeout=2) as response:
                if response.status==200: break
        except Exception: time.sleep(.1)
    else: raise RuntimeError('本地服务未通过启动检查，请查看 data/logs/application.log。')
    (data_dir/'runtime.json').write_text(json.dumps({'url':url,'pid':os.getpid()},ensure_ascii=False),encoding='utf-8')
    progress('准备就绪，开启下一步。',100)
    EVENTS.put(('ready',url,100))
    return url


def existing_instance(data_dir):
    if os.name!='nt': return None
    name='Local\\ExamAssistantV2_'+hashlib.sha256(str(data_dir.resolve()).lower().encode()).hexdigest()[:20]
    kernel=ctypes.windll.kernel32
    kernel.CreateMutexW.restype=ctypes.c_void_p
    handle=kernel.CreateMutexW(None,False,name)
    if not handle: raise RuntimeError('无法创建应用实例锁。')
    if kernel.GetLastError()==183:
        kernel.CloseHandle(ctypes.c_void_p(handle))
        info=data_dir/'runtime.json'
        for _ in range(30):
            if info.exists():
                try:
                    url=json.loads(info.read_text(encoding='utf-8'))['url']
                    with urllib.request.urlopen(url+'/api/v1/health/',timeout=1): pass
                    webbrowser.open(url)
                    return True
                except Exception: pass
            time.sleep(.2)
        raise RuntimeError('本目录中的程序正在启动，请稍后再试。')
    return handle


def graphical(data_dir,port,no_browser,self_test=False):
    import tkinter as tk
    from tkinter import ttk,messagebox
    root=tk.Tk()
    root.title('报考小助手 · 离线工作台')
    root.configure(bg='#11282b')
    width,height=520,350
    root.geometry(f'{width}x{height}+{(root.winfo_screenwidth()-width)//2}+{(root.winfo_screenheight()-height)//2}')
    root.resizable(False,False)
    root.attributes('-topmost',True)
    tk.Label(root,text='EXAM ASSISTANT / OFFLINE',fg='#71988b',bg='#11282b',font=('Segoe UI',10)).pack(pady=(31,15))
    tk.Label(root,text='为下一步，做好准备。',fg='#e2eedf',bg='#11282b',font=('Microsoft YaHei',23)).pack()
    status=tk.StringVar(value='正在启动你的离线工作台…')
    tk.Label(root,textvariable=status,fg='#98b6a5',bg='#11282b',font=('Microsoft YaHei',10),wraplength=450).pack(pady=(19,16))
    style=ttk.Style(root)
    style.theme_use('clam')
    style.configure('Offline.Horizontal.TProgressbar',troughcolor='#24403f',background='#83baa1',bordercolor='#24403f',lightcolor='#83baa1',darkcolor='#83baa1')
    value=tk.DoubleVar(value=5)
    bar=ttk.Progressbar(root,length=400,variable=value,maximum=100,style='Offline.Horizontal.TProgressbar')
    bar.pack(pady=10)
    buttons=tk.Frame(root,bg='#11282b');buttons.pack(pady=20)
    state={'url':None,'closed':False}
    def close():
        if state['url'] and not messagebox.askyesno('关闭本地服务','关闭前请确认答案已保存或交卷。关闭启动器将停止本地服务。',parent=root): return
        state['closed']=True
        if SERVER: SERVER.close()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW',close)
    def worker():
        try: initialize(data_dir,port)
        except Exception as error:
            logging.exception('Startup failed')
            EVENTS.put(('error',str(error),0))
    threading.Thread(target=worker,daemon=True).start()
    def pump():
        if state['closed']: return
        try:
            while True:
                kind,text,amount=EVENTS.get_nowait()
                if kind=='progress': status.set(text);value.set(amount)
                elif kind=='ready':
                    state['url']=text
                    status.set('本地服务已启动 · 数据保存在本机\n'+text)
                    root.attributes('-topmost',False)
                    for label,command in [('打开工作台',lambda:webbrowser.open(text)),('打开数据目录',lambda:os.startfile(data_dir)),('关闭程序',close)]:
                        tk.Button(buttons,text=label,command=command,bg='#2b6658',fg='#e9f4e8',activebackground='#3c7d68',activeforeground='#fff',relief='flat',font=('Microsoft YaHei',10),padx=13,pady=8).pack(side='left',padx=4)
                    if not no_browser: webbrowser.open(text)
                    if self_test:
                        logging.info('GUI_SELF_TEST_OK')
                        root.after(800,root.destroy)
                elif kind=='error':
                    status.set('启动失败，请查看日志')
                    messagebox.showerror('启动失败',text+'\n日志：'+str(data_dir/'logs'/'application.log'),parent=root)
        except queue.Empty: pass
        root.after(100,pump)
    root.after(100,pump)
    root.mainloop()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--self-test-ui',action='store_true')
    parser.add_argument('--data-dir',type=Path,default=DEFAULT_ROOT/'data')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    data_dir=args.data_dir.resolve()
    data_dir.mkdir(parents=True,exist_ok=True)
    logs=data_dir/'logs';logs.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,handlers=[RotatingFileHandler(logs/'application.log',maxBytes=2*1024*1024,backupCount=3,encoding='utf-8')],format='%(asctime)s %(levelname)s %(message)s')
    mutex=None
    try:
        mutex=existing_instance(data_dir)
        if mutex is True: return
        if args.headless:
            url=initialize(data_dir,args.port)
            if sys.stdout: print('READY '+url,flush=True)
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt: pass
        else: graphical(data_dir,args.port,args.no_browser or args.self_test_ui,args.self_test_ui)
    except Exception as error:
        logging.exception('Launcher failed')
        if args.headless: sys.exit(1)
        from tkinter import messagebox
        messagebox.showerror('启动失败',str(error))
    finally:
        if SERVER: SERVER.close()
        if mutex and mutex is not True and os.name=='nt': ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(mutex))


if __name__=='__main__': main()
