#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
station_localization_handler.py
用于更新stations表的本地化信息
"""

import os
import json
import sqlite3
import re
from typing import Dict, Optional
from pathlib import Path

# 定义输出目录和语言列表
output_db_dir = './output/db'
languages = ['en', 'de', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']

def load_json_file(file_path: str) -> Optional[dict]:
    """加载JSON文件"""
    try:
        if not os.path.exists(file_path):
            print(f"错误：找不到文件 {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {e}")
        return None

def process_template(template: str, localization_data: Dict, lang: str) -> str:
    """
    处理模板字符串，替换为对应语言的文本
    例如："{271747} X - {63584} 3 - {61158} {61515}"
    """
    def replace_match(match):
        template_id = match.group(1)
        if template_id in localization_data:
            translations = localization_data[template_id]
            # 如果没有对应语言的翻译，回退到英文
            translated_text = translations.get(lang, translations.get('en', match.group(0)))
            # print(f"替换模板ID {template_id}: {translated_text} ({lang})")  # 添加调试信息
            return translated_text
        print(f"未找到模板ID {template_id} 的翻译")  # 添加调试信息
        return match.group(0)
    
    # print(f"\n处理模板: {template}")  # 添加调试信息
    
    # 先检查模板中的所有ID是否都能找到对应的翻译
    template_ids = re.findall(r'{(\d+)}', template)
    # print(f"发现的模板ID: {template_ids}")
    
    missing_ids = []
    for template_id in template_ids:
        if template_id not in localization_data:
            missing_ids.append(template_id)
            print(f"警告：模板ID {template_id} 在本地化数据中不存在")
    
    if missing_ids:
        print(f"警告：以下模板ID未找到对应的翻译: {missing_ids}")
    
    # 使用正则表达式替换所有模板ID
    result = template
    for template_id in template_ids:
        if template_id in localization_data:
            translations = localization_data[template_id]
            translated_text = translations.get(lang, translations.get('en', f"{{{template_id}}}"))
            # print(f"替换模板ID {template_id}: {translated_text} ({lang})")
            # 使用更精确的替换
            result = result.replace(f"{{{template_id}}}", translated_text)
    
    # print(f"处理结果: {result}")  # 添加调试信息
    return result

def update_stations_localization():
    """更新stations表的本地化信息"""
    # 加载模板和本地化数据
    templates_file = "station_name_localization/station_name_templates.json"
    localization_file = "accounting_entry_types/output/combined_localization.json"
    
    templates = load_json_file(templates_file)
    localization_data = load_json_file(localization_file)
    
    if not templates or not localization_data:
        return False
        
    # 打印一些本地化数据的统计信息
    print(f"\n本地化数据统计:")
    print(f"- 总条目数: {len(localization_data)}")
    print(f"- 包含的语言: {list(next(iter(localization_data.values())).keys())}")
    
    # 确保输出目录存在
    os.makedirs(output_db_dir, exist_ok=True)
    
    success_count = 0
    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        
        if not os.path.exists(db_filename):
            print(f"警告：数据库文件 {db_filename} 不存在，跳过")
            continue
            
        print(f"\n处理数据库: {db_filename}, 语言代码: {lang}")
        
        try:
            # 连接数据库
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()
            
            # 检查stations表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stations'")
            if not cursor.fetchone():
                print(f"警告：数据库 {db_filename} 中不存在stations表，跳过")
                conn.close()
                continue
            
            # 获取所有stations记录
            cursor.execute("SELECT stationID, stationName FROM stations")
            stations = cursor.fetchall()
            
            # 更新每个空间站的名称
            updated_count = 0
            not_found_count = 0
            no_change_count = 0
            
            for station_id, original_name in stations:
                station_id_str = str(station_id)
                if station_id_str in templates:
                    template = templates[station_id_str]
                    # 处理模板，生成本地化名称
                    localized_name = process_template(template, localization_data, lang)
                    
                    # 检查是否有实际变化
                    if localized_name != original_name:
                        # 检查是否还有未替换的模板ID
                        if re.search(r'{(\d+)}', localized_name):
                            print(f"警告：空间站 {station_id} 的名称中仍有未替换的模板ID")
                            print(f"模板: {template}")
                            print(f"结果: {localized_name}")
                            continue
                            
                        # 更新数据库
                        cursor.execute("""
                            UPDATE stations 
                            SET stationName = ? 
                            WHERE stationID = ?
                        """, (localized_name, station_id))
                        updated_count += 1
                        # print(f"空间站 {station_id} 更新:")
                        # print(f"原名称: {original_name}")
                        # print(f"新名称: {localized_name}")
                    else:
                        no_change_count += 1
                else:
                    not_found_count += 1
                    print(f"警告：未找到空间站 {station_id} 的模板")
            
            # 提交更改
            conn.commit()
            print(f"\n处理完成:")
            print(f"- 更新记录数: {updated_count}")
            print(f"- 无变化记录数: {no_change_count}")
            print(f"- 未找到模板记录数: {not_found_count}")
            success_count += 1
            
        except Exception as e:
            print(f"处理数据库 {db_filename} 时出错: {e}")
            raise  # 添加这行以显示完整的错误堆栈
        finally:
            if 'conn' in locals():
                conn.close()
    
    print(f"\n本地化更新完成，成功处理了 {success_count} 个数据库")
    return success_count > 0

if __name__ == "__main__":
    update_stations_localization() 