from sqlite2duckdb import sqlite_to_duckdb
from pathlib import Path
import os
import time

def main():
    # 获取output/db目录下的所有SQLite数据库文件
    db_dir = Path("output/db")
    if not db_dir.exists():
        print("错误: output/db 目录不存在")
        return
    
    sqlite_files = list(db_dir.glob("*.sqlite"))
    if not sqlite_files:
        print("错误: 未找到SQLite数据库文件")
        return
    
    print(f"找到 {len(sqlite_files)} 个SQLite数据库文件")
    
    # 转换每个数据库文件
    for sqlite_file in sqlite_files:
        duckdb_file = sqlite_file.with_suffix('.duckdb')
        print(f"\n开始转换: {sqlite_file.name}")
        
        start_time = time.time()
        try:
            sqlite_to_duckdb(str(sqlite_file), str(duckdb_file))
            
            # 获取数据库大小
            sqlite_size = os.path.getsize(sqlite_file)
            duckdb_size = os.path.getsize(duckdb_file)
            
            end_time = time.time()
            print(f"转换完成！")
            print(f"耗时: {end_time - start_time:.2f} 秒")
            print(f"SQLite数据库大小: {sqlite_size / 1024 / 1024:.2f} MB")
            print(f"DuckDB数据库大小: {duckdb_size / 1024 / 1024:.2f} MB")
            print(f"压缩率: {(1 - duckdb_size / sqlite_size) * 100:.2f}%")
            
        except Exception as e:
            print(f"转换过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 