"""Black-box runtime checks: restart persistence and restore against a disposable data directory."""
import argparse
import json
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
import uuid

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('executable',type=Path)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8890)
    parser.add_argument('--python',type=Path)
    args=parser.parse_args()
    args.data_dir.mkdir(parents=True,exist_ok=True)
    results=[]
    def stop(process):
        if process.poll() is not None:return
        if __import__('os').name=='nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        else: process.terminate()
        process.wait(timeout=10)
    def passed(name): results.append({'name':name,'status':'passed'});print('PASS '+name,flush=True)
    def launch():
        command=([str(args.python)] if args.python else [])+[str(args.executable),'--headless','--no-browser','--data-dir',str(args.data_dir),'--port',str(args.port)]
        started=time.time()
        process=subprocess.Popen(command,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            info=args.data_dir/'runtime.json'
            if info.exists():
                try:
                    state=json.loads(info.read_text(encoding='utf-8'))
                    if info.stat().st_mtime < started-.1: time.sleep(.1);continue
                    with urllib.request.urlopen(state['url']+'/api/v1/health/',timeout=1) as res:
                        if res.status==200: return process,state['url']
                except Exception: pass
            if process.poll() is not None: raise RuntimeError('Launcher exited: '+str(process.returncode))
            time.sleep(.1)
        stop(process);raise RuntimeError('Startup timeout; inspect application.log')
    process,base=launch()
    def call(path,method='GET',body=None,token=None,raw=False):
        headers={}
        if token: headers['Authorization']='Bearer '+token
        if body is not None:
            body=json.dumps(body,ensure_ascii=False).encode();headers['Content-Type']='application/json'
        request=urllib.request.Request(base+'/api/v1/'+path,data=body,headers=headers,method=method)
        with urllib.request.urlopen(request,timeout=30) as res:
            value=res.read()
            return value if raw else json.loads(value)['data']
    try:
        passed('cold-start executable and SQLite migration')
        home=call('home/')
        assert home['counts']=={'opportunities':105,'questions':180,'services':6}
        passed('original seed retained, missing services initialized')
        admin=call('auth/login/','POST',{'username':'admin','password':'Admin@123456'})['access']
        demo=call('auth/login/','POST',{'username':'demo','password':'Demo@123456'})['access']
        marker='QA_RUNTIME_'+uuid.uuid4().hex[:8]
        plan=call('application-plans/','POST',{'title':marker,'exam_type':'civil'},demo)
        identifier=plan['id']
        stop(process)
        process,base=launch()
        demo=call('auth/login/','POST',{'username':'demo','password':'Demo@123456'})['access']
        assert call(f'application-plans/{identifier}/',token=demo)['title']==marker
        passed('restart preserves user data')
        admin=call('auth/login/','POST',{'username':'admin','password':'Admin@123456'})['access']
        backup=call('admin/backups/','POST',{},admin)['filename']
        backup_bytes=call('admin/backups/'+backup+'/',token=admin,raw=True)
        assert backup_bytes.startswith(b'SQLite format 3')
        call(f'application-plans/{identifier}/','PATCH',{'title':'modified after backup'},demo)
        boundary='OfflineQA'+uuid.uuid4().hex
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="confirm"\r\n\r\nRESTORE\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="backup.sqlite3"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+backup_bytes+f'\r\n--{boundary}--\r\n'.encode())
        request=urllib.request.Request(base+'/api/v1/admin/restore/',data=body,method='POST',headers={'Authorization':'Bearer '+admin,'Content-Type':'multipart/form-data; boundary='+boundary})
        with urllib.request.urlopen(request,timeout=30) as response: assert json.loads(response.read())['success']
        passed('valid backup download and database restore')
        try:
            call('auth/me/',token=demo)
            raise AssertionError('Old token survived restore')
        except urllib.error.HTTPError as error: assert error.code==401
        passed('restore invalidates old login sessions')
        demo=call('auth/login/','POST',{'username':'demo','password':'Demo@123456'})['access']
        assert call(f'application-plans/{identifier}/',token=demo)['title']==marker
        passed('restored record matches backup snapshot')
        with urllib.request.urlopen(base+'/',timeout=10) as response:index=response.read()
        assert b'type="module"' in index
        passed('offline frontend served by executable')
        (args.data_dir.parent/'runtime_results.json').write_text(json.dumps({'executable':str(args.executable),'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        stop(process)
    print('ALL PASSED '+str(len(results)))

if __name__=='__main__':main()
