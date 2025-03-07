#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
import hashlib
import csv
import datetime
from tabulate import tabulate

def get_tables(db_path):
    """获取数据库中所有表的名称"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_schema(db_path, table_name):
    """获取表的结构信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    schema = cursor.fetchall()
    conn.close()
    return schema

def get_row_count(db_path, table_name):
    """获取表中的行数"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_primary_key(db_path, table_name):
    """获取表的主键列"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    primary_keys = [column[1] for column in columns if column[5] == 1]  # column[5] 是 pk 标志
    conn.close()
    return primary_keys

def get_all_columns(db_path, table_name):
    """获取表的所有列名"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [column[1] for column in cursor.fetchall()]
    conn.close()
    return columns

def get_table_data(db_path, table_name, primary_keys=None):
    """获取表的所有数据，如果提供了主键，则以主键为键返回字典"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取列名
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [column[1] for column in cursor.fetchall()]
    
    # 获取所有数据
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    
    result = {}
    if primary_keys:
        # 找到主键列的索引
        pk_indices = [columns.index(pk) for pk in primary_keys]
        
        for row in rows:
            # 使用主键值的组合作为字典键
            pk_values = tuple(row[idx] for idx in pk_indices)
            if len(pk_values) == 1:
                pk_values = pk_values[0]  # 如果只有一个主键，不使用元组
            result[pk_values] = {columns[i]: row[i] for i in range(len(columns))}
    else:
        # 如果没有主键，使用行的哈希值作为键
        for row in rows:
            row_hash = hashlib.md5(str(row).encode()).hexdigest()
            result[row_hash] = {columns[i]: row[i] for i in range(len(columns))}
    
    conn.close()
    return result

def compare_table_data(old_data, new_data):
    """比较两个表的数据差异"""
    old_keys = set(old_data.keys())
    new_keys = set(new_data.keys())
    
    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys
    common_keys = old_keys.intersection(new_keys)
    
    # 找出修改的记录
    modified_keys = []
    for key in common_keys:
        if old_data[key] != new_data[key]:
            modified_keys.append(key)
    
    return {
        'added': added_keys,
        'removed': removed_keys,
        'modified': modified_keys
    }

def get_column_differences(old_row, new_row):
    """获取行中哪些列发生了变化"""
    differences = {}
    for col in old_row:
        if col in new_row and old_row[col] != new_row[col]:
            differences[col] = (old_row[col], new_row[col])
    return differences

def export_to_csv(results, csv_path):
    """将结果导出到CSV文件"""
    # 创建目录（如果不存在）
    dir_name = os.path.dirname(csv_path)
    if dir_name:  # 只有当路径包含目录时才创建
        os.makedirs(dir_name, exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # 写入标题行
        writer.writerow(['表名', '变化类型', '结构变化', '旧行数', '新行数', '行数差异', 
                         '新增记录数', '删除记录数', '修改记录数', '记录ID', '字段名', '旧值', '新值'])
        
        # 写入表级别的变化
        for table_info in results['changed_tables']:
            table_name = table_info['表名']
            table_diff = results['table_diffs'].get(table_name, {})
            
            # 基本信息行
            writer.writerow([
                table_name, 
                '表级别变化',
                '是' if table_info['结构变化'] else '否',
                table_info['旧行数'],
                table_info['新行数'],
                table_info['行数差异'],
                len(table_diff.get('added', [])),
                len(table_diff.get('removed', [])),
                len(table_diff.get('modified', [])),
                '', '', '', ''
            ])
            
            # 新增记录
            for record_id in table_diff.get('added', []):
                writer.writerow([
                    table_name, '新增记录', '', '', '', '', '', '', '', record_id, '', '', ''
                ])
            
            # 删除记录
            for record_id in table_diff.get('removed', []):
                writer.writerow([
                    table_name, '删除记录', '', '', '', '', '', '', '', record_id, '', '', ''
                ])
            
            # 修改记录
            for record_id in table_diff.get('modified', []):
                differences = table_diff.get('differences', {}).get(record_id, {})
                if not differences:
                    writer.writerow([
                        table_name, '修改记录', '', '', '', '', '', '', '', record_id, '', '', ''
                    ])
                else:
                    for field, (old_val, new_val) in differences.items():
                        writer.writerow([
                            table_name, '修改记录', '', '', '', '', '', '', '', record_id, field, old_val, new_val
                        ])
    
    print(f"\n详细报告已导出到: {csv_path}")

def compare_databases(old_db_path, new_db_path, detail_level=0, export_csv=None):
    """比较两个数据库的差异
    detail_level: 详细程度
        0 - 只显示表级别的变化
        1 - 显示记录级别的变化数量
        2 - 显示具体哪些记录发生了变化
    export_csv: 导出CSV报告的文件路径
    """
    print(f"对比数据库: \n旧: {old_db_path}\n新: {new_db_path}\n")
    
    # 检查文件是否存在
    if not os.path.exists(old_db_path):
        print(f"错误: 找不到旧数据库文件 {old_db_path}")
        return
    if not os.path.exists(new_db_path):
        print(f"错误: 找不到新数据库文件 {new_db_path}")
        return
    
    # 获取两个数据库中的所有表
    old_tables = set(get_tables(old_db_path))
    new_tables = set(get_tables(new_db_path))
    
    # 找出新增和删除的表
    added_tables = new_tables - old_tables
    removed_tables = old_tables - new_tables
    common_tables = old_tables.intersection(new_tables)
    
    # 用于存储结果的字典
    results = {
        'added_tables': sorted(added_tables),
        'removed_tables': sorted(removed_tables),
        'changed_tables': [],
        'table_diffs': {}
    }
    
    # 输出新增和删除的表
    if added_tables:
        print("新增的表:")
        for table in sorted(added_tables):
            row_count = get_row_count(new_db_path, table)
            print(f"  - {table} (行数: {row_count})")
        print()
    
    if removed_tables:
        print("删除的表:")
        for table in sorted(removed_tables):
            print(f"  - {table}")
        print()
    
    # 比较共有表的结构和行数
    changed_tables = []
    for table in sorted(common_tables):
        old_schema = get_table_schema(old_db_path, table)
        new_schema = get_table_schema(new_db_path, table)
        old_count = get_row_count(old_db_path, table)
        new_count = get_row_count(new_db_path, table)
        
        schema_changed = old_schema != new_schema
        count_changed = old_count != new_count
        
        if schema_changed or count_changed:
            table_info = {
                "表名": table,
                "结构变化": "是" if schema_changed else "否",
                "旧行数": old_count,
                "新行数": new_count,
                "行数差异": new_count - old_count
            }
            changed_tables.append(table_info)
            results['changed_tables'].append(table_info)
    
    if changed_tables:
        print("变化的表:")
        headers = ["表名", "结构变化", "旧行数", "新行数", "行数差异"]
        table_data = [[t["表名"], t["结构变化"], t["旧行数"], t["新行数"], t["行数差异"]] for t in changed_tables]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # 如果需要更详细的比较
        if detail_level > 0:
            print("\n表内容详细对比:")
            for table_info in changed_tables:
                table_name = table_info["表名"]
                print(f"\n表 '{table_name}' 的变化:")
                
                # 获取主键
                primary_keys = get_primary_key(old_db_path, table_name)
                if not primary_keys:
                    print(f"  警告: 表 '{table_name}' 没有主键，将使用行哈希进行比较")
                
                # 获取表数据
                old_data = get_table_data(old_db_path, table_name, primary_keys)
                new_data = get_table_data(new_db_path, table_name, primary_keys)
                
                # 比较数据
                diff = compare_table_data(old_data, new_data)
                
                # 存储差异信息
                results['table_diffs'][table_name] = {
                    'added': list(diff['added']),
                    'removed': list(diff['removed']),
                    'modified': list(diff['modified']),
                    'differences': {}
                }
                
                print(f"  - 新增记录数: {len(diff['added'])}")
                print(f"  - 删除记录数: {len(diff['removed'])}")
                print(f"  - 修改记录数: {len(diff['modified'])}")
                
                # 如果需要显示具体的记录变化
                if detail_level > 1:
                    # 显示新增的记录
                    if diff['added'] and len(diff['added']) <= 10:
                        print("\n  新增的记录:")
                        for key in diff['added']:
                            print(f"    - ID: {key}")
                    elif diff['added'] and len(diff['added']) > 10:
                        print(f"\n  新增的记录 (显示前10条，共{len(diff['added'])}条):")
                        for key in list(diff['added'])[:10]:
                            print(f"    - ID: {key}")
                    
                    # 显示删除的记录
                    if diff['removed'] and len(diff['removed']) <= 10:
                        print("\n  删除的记录:")
                        for key in diff['removed']:
                            print(f"    - ID: {key}")
                    elif diff['removed'] and len(diff['removed']) > 10:
                        print(f"\n  删除的记录 (显示前10条，共{len(diff['removed'])}条):")
                        for key in list(diff['removed'])[:10]:
                            print(f"    - ID: {key}")
                    
                    # 显示修改的记录
                    if diff['modified'] and len(diff['modified']) <= 10:
                        print("\n  修改的记录:")
                        for key in diff['modified']:
                            differences = get_column_differences(old_data[key], new_data[key])
                            results['table_diffs'][table_name]['differences'][key] = differences
                            print(f"    - ID: {key}")
                            for col, (old_val, new_val) in differences.items():
                                print(f"      {col}: {old_val} -> {new_val}")
                    elif diff['modified'] and len(diff['modified']) > 10:
                        print(f"\n  修改的记录 (显示前10条，共{len(diff['modified'])}条):")
                        for key in list(diff['modified'])[:10]:
                            differences = get_column_differences(old_data[key], new_data[key])
                            results['table_diffs'][table_name]['differences'][key] = differences
                            print(f"    - ID: {key}")
                            for col, (old_val, new_val) in differences.items():
                                print(f"      {col}: {old_val} -> {new_val}")
    else:
        print("没有表发生变化")
    
    # 导出到CSV
    if export_csv:
        export_to_csv(results, export_csv)
    
    return results

if __name__ == "__main__":
    old_db_path = "output_old/db/item_db_zh.sqlite"
    new_db_path = "output/db/item_db_zh.sqlite"
    detail_level = 2  # 默认显示记录级别的变化数量
    export_csv = None
    
    if len(sys.argv) > 2:
        old_db_path = sys.argv[1]
        new_db_path = sys.argv[2]
    
    if len(sys.argv) > 3:
        detail_level = int(sys.argv[3])
    
    # 默认导出CSV报告
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    export_csv = f"db_diff_report_{timestamp}.csv"
    
    if len(sys.argv) > 4:
        export_csv = sys.argv[4]
    
    compare_databases(old_db_path, new_db_path, detail_level, export_csv)
