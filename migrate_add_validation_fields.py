#!/usr/bin/env python3
"""数据库迁移：添加标签验证状态字段"""

import sqlite3
from pathlib import Path

def migrate_add_validation_fields():
    """添加validation_status和invalid_tags字段到music_semantic表"""

    db_path = Path('data/semantic.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 添加validation_status字段
        try:
            cursor.execute('''
                ALTER TABLE music_semantic
                ADD COLUMN validation_status TEXT DEFAULT 'valid'
            ''')
            print('OK - add validation_status field')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print('OK - validation_status field exists, skip')
            else:
                raise

        # 添加invalid_tags字段
        try:
            cursor.execute('''
                ALTER TABLE music_semantic
                ADD COLUMN invalid_tags TEXT
            ''')
            print('OK - add invalid_tags field')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print('OK - invalid_tags field exists, skip')
            else:
                raise

        # 为现有记录设置默认值
        cursor.execute('''
            UPDATE music_semantic
            SET validation_status = 'valid'
            WHERE validation_status IS NULL OR validation_status = ''
        ''')
        updated = cursor.rowcount
        print(f'OK - update {updated} existing records')

        conn.commit()
        print('\nMigration completed!')

        # 显示新表结构
        print('\n更新后的表结构:')
        cursor.execute('PRAGMA table_info(music_semantic)')
        for col in cursor.fetchall():
            print(f'  {col[1]} {col[2]} {"DEFAULT " + str(col[4]) if col[4] else ""}')

    except Exception as e:
        conn.rollback()
        print(f'\n错误: {e}')
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_add_validation_fields()
