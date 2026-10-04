"""Read-only archive checks and an in-memory round-trip of the delivered SQL."""
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile


def main():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / '交付文件校验.json').read_text(encoding='utf-8'))
    for name, expected in manifest.items():
        file = root / name
        assert file.stat().st_size == expected['bytes'], name
        assert hashlib.sha256(file.read_bytes()).hexdigest() == expected['sha256'], name
    print('PASS SHA256 and file sizes')
    prefix = 'ExamAssistant_Offline_v2/'
    for name in ['ExamAssistant_Offline_v2_客户运行包.zip', 'ExamAssistant_Offline_v2_完整交付包.zip']:
        with zipfile.ZipFile(root / name) as archive:
            assert archive.testzip() is None, name
            names = set(archive.namelist())
            assert prefix + 'ExamAssistant.exe' in names
            assert prefix + '一键启动.cmd' in names
            assert prefix + '_internal/resources/db_seed.sqlite3' in names
            assert not any('.secret' in n or '/data/' in n or 'node_modules/' in n or '.venv/' in n for n in names)
            assert not any(n.startswith('/') or '..' in Path(n).parts for n in names)
            if '完整交付包' in name:
                for required in ['source/backend/core/models.py', 'source/frontend/src/App.vue',
                                 'source/requirements-lock.txt', 'source/frontend/pnpm-lock.yaml',
                                 '工程源码_按模块.txt', 'SQLite数据.txt', '一键启动.cmd']:
                    assert required in names, required
            print(f'PASS ZIP integrity and clean contents: {name} ({len(names)} files)')
    connection = sqlite3.connect(':memory:')
    try:
        connection.executescript((root / 'SQLite数据.txt').read_text(encoding='utf-8'))
        assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not connection.execute('PRAGMA foreign_key_check').fetchall()
        expected_counts = {'core_opportunity': 105, 'core_question': 180,
                           'core_serviceresource': 6, 'core_applicationrecord': 0,
                           'core_servicerequest': 0}
        for table, count in expected_counts.items():
            actual = connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            assert actual == count, (table, actual, count)
        print('PASS SQL round-trip, integrity, foreign keys and pristine seed counts')
    finally:
        connection.close()
    print('ALL DELIVERY CHECKS PASSED')


if __name__ == '__main__':
    main()
