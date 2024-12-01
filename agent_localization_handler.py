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

# 定义输出目录和语言列表
output_db_dir = 'output/db'
languages = ['en', 'de', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']  # en 务必在第一个否则有些功能可能会有缺失

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

def update_agents_localization():
    """
    更新agents表的本地化信息
    """
    # 加载本地化映射
    localization_mapping = load_localization_mapping()
    if not localization_mapping:
        return False
    
    # 确保输出目录存在
    os.makedirs(output_db_dir, exist_ok=True)
    
    success_count = 0
    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        
        if not os.path.exists(db_filename):
            print(f"警告：数据库文件 {db_filename} 不存在，跳过")
            continue
            
        print(f"处理数据库: {db_filename}, 语言代码: {lang}")
        
        try:
            # 连接数据库
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()
            
            # 检查agents表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
            if not cursor.fetchone():
                print(f"警告：数据库 {db_filename} 中不存在agents表，跳过")
                conn.close()
                continue
            
            # 检查invNames表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invNames'")
            if not cursor.fetchone():
                print(f"警告：数据库 {db_filename} 中不存在invNames表，跳过")
                conn.close()
                continue
            
            # 检查agent_name列是否存在，如果不存在则添加
            cursor.execute("PRAGMA table_info(agents)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'agent_name' not in columns:
                print(f"在数据库 {db_filename} 中添加agent_name列")
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
            not_found_count = 0
            for agent_id, english_name in agents:
                # 查找对应的本地化文本
                if english_name in localization_mapping and lang in localization_mapping[english_name]:
                    localized_name = localization_mapping[english_name][lang]
                    
                    # 更新agent_name
                    cursor.execute("""
                        UPDATE agents 
                        SET agent_name = ? 
                        WHERE agent_id = ?
                    """, (localized_name, agent_id))
                    
                    updated_count += 1
                else:
                    # 如果找不到本地化文本，使用原始英文名称
                    cursor.execute("""
                        UPDATE agents 
                        SET agent_name = ? 
                        WHERE agent_id = ?
                    """, (english_name, agent_id))
                    
                    not_found_count += 1
            
            # 提交更改
            conn.commit()
            print(f"成功更新了 {updated_count} 条记录，{not_found_count} 条记录使用原始英文名称")
            success_count += 1
            
        except Exception as e:
            print(f"处理数据库 {db_filename} 时出错: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    print(f"本地化更新完成，成功处理了 {success_count} 个数据库")
    return success_count > 0

if __name__ == "__main__":
    update_agents_localization() 