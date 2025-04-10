#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
agent_localization_handler.py
用于更新agents表的本地化信息
"""

import os
import json
import sqlite3
import glob
from pathlib import Path

def load_localization_mapping():
    """
    加载英文到多种语言的映射文件
    """
    mapping_file = os.path.join("accounting_entry_types", "output", "en_multi_lang_mapping.json")
    
    if not os.path.exists(mapping_file):
        print(f"错误：找不到本地化映射文件 {mapping_file}")
        return None
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载本地化映射文件时出错: {e}")
        return None

def get_language_code(db_file_path):
    """
    从数据库文件名中提取语言代码
    """
    file_name = os.path.basename(db_file_path)
    # 假设文件名格式为: language_code.db 或 language_code_something.db
    parts = file_name.split('_')
    return parts[0]

def update_agents_localization():
    """
    更新agents表的本地化信息
    """
    # 加载本地化映射
    localization_mapping = load_localization_mapping()
    if not localization_mapping:
        return False
    
    # 获取所有数据库文件
    db_files = glob.glob("*.db")
    if not db_files:
        print("错误：找不到数据库文件")
        return False
    
    success_count = 0
    for db_file in db_files:
        language_code = get_language_code(db_file)
        print(f"处理数据库: {db_file}, 语言代码: {language_code}")
        
        try:
            # 连接数据库
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 检查agents表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
            if not cursor.fetchone():
                print(f"警告：数据库 {db_file} 中不存在agents表，跳过")
                conn.close()
                continue
            
            # 检查invNames表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invNames'")
            if not cursor.fetchone():
                print(f"警告：数据库 {db_file} 中不存在invNames表，跳过")
                conn.close()
                continue
            
            # 检查agent_name列是否存在，如果不存在则添加
            cursor.execute("PRAGMA table_info(agents)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'agent_name' not in columns:
                print(f"在数据库 {db_file} 中添加agent_name列")
                cursor.execute("ALTER TABLE agents ADD COLUMN agent_name TEXT")
            
            # 获取所有agents记录
            cursor.execute("""
                SELECT a.agent_id, n.itemName 
                FROM agents a 
                JOIN invNames n ON a.agent_id = n.itemID
            """)
            agents = cursor.fetchall()
            
            # 更新每条记录的agent_name
            updated_count = 0
            for agent_id, english_name in agents:
                # 查找对应的本地化文本
                if english_name in localization_mapping and language_code in localization_mapping[english_name]:
                    localized_name = localization_mapping[english_name][language_code]
                    
                    # 更新agent_name
                    cursor.execute("""
                        UPDATE agents 
                        SET agent_name = ? 
                        WHERE agent_id = ?
                    """, (localized_name, agent_id))
                    
                    updated_count += 1
            
            # 提交更改
            conn.commit()
            print(f"成功更新了 {updated_count} 条记录")
            success_count += 1
            
        except Exception as e:
            print(f"处理数据库 {db_file} 时出错: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    print(f"本地化更新完成，成功处理了 {success_count} 个数据库")
    return success_count > 0

if __name__ == "__main__":
    update_agents_localization() 