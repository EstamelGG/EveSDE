#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import sqlite3
import os
from typing import Dict, List, Tuple, Optional

def download_json(url: str) -> Dict:
    """下载并解析JSON文件"""
    print(f"正在下载: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"下载失败: {e}")
        raise

def create_facility_rig_effects_table(cursor: sqlite3.Cursor):
    """创建设施装配效果表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facility_rig_effects (
            id INTEGER NOT NULL,
            category INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            PRIMARY KEY (id, category, group_id)
        )
    ''')

def get_dogma_attribute_ids_from_data(activity_data: Dict) -> List[int]:
    """从活动数据中提取所有的dogmaAttributeID"""
    attribute_ids = set()
    
    # 从material中收集dogmaAttributeID
    for material in activity_data.get('material', []):
        if 'dogmaAttributeID' in material:
            attribute_ids.add(material['dogmaAttributeID'])
    
    # 从time中收集dogmaAttributeID
    for time_item in activity_data.get('time', []):
        if 'dogmaAttributeID' in time_item:
            attribute_ids.add(time_item['dogmaAttributeID'])
    
    return list(attribute_ids)

def process_industry_modifier_sources(
    modifier_data: Dict, 
    filter_data: Dict, 
    cursor: sqlite3.Cursor
) -> List[Tuple]:
    """处理工业修正源数据"""
    facility_effects = []
    
    for facility_id, facility_data in modifier_data.items():
        facility_id = int(facility_id)
        
        # 检查设施是否在types表中且marketGroupID不为null
        cursor.execute('''
            SELECT marketGroupID FROM types 
            WHERE type_id = ? AND marketGroupID IS NOT NULL
        ''', (facility_id,))
        market_group_result = cursor.fetchone()
        
        # 如果设施不在types表中或marketGroupID为null，跳过
        if not market_group_result:
            continue
        
        # 只处理manufacturing和reaction相关数据
        for activity_type in ['manufacturing', 'reaction']:
            if activity_type not in facility_data:
                continue
                
            activity_data = facility_data[activity_type]
            
            # 获取活动数据中的所有dogmaAttributeID
            dogma_attribute_ids = get_dogma_attribute_ids_from_data(activity_data)
            
            # 分别收集material和time的filterID和dogmaAttributeID映射
            material_filter_dogma_map = {}  # ME相关属性
            time_filter_dogma_map = {}      # TE相关属性
            
            # 从material中收集filterID和dogmaAttributeID的映射（ME属性）
            for material in activity_data.get('material', []):
                if 'dogmaAttributeID' in material:
                    filter_id = material.get('filterID', None)
                    dogma_attr_id = material['dogmaAttributeID']
                    material_filter_dogma_map[filter_id] = dogma_attr_id
            
            # 从time中收集filterID和dogmaAttributeID的映射（TE属性）
            for time_item in activity_data.get('time', []):
                if 'dogmaAttributeID' in time_item:
                    filter_id = time_item.get('filterID', None)
                    dogma_attr_id = time_item['dogmaAttributeID']
                    time_filter_dogma_map[filter_id] = dogma_attr_id
            
            # 合并所有的filterID，为每个filter创建记录
            all_filter_ids = set(material_filter_dogma_map.keys()) | set(time_filter_dogma_map.keys())
            
            for filter_id in all_filter_ids:
                if filter_id is None:
                    # 没有filterID，表示对所有物品有效
                    facility_effects.append((facility_id, 0, 0))
                else:
                    # 有filterID，需要查找对应的category和group
                    filter_id_str = str(filter_id)
                    if filter_id_str in filter_data:
                        filter_info = filter_data[filter_id_str]
                        
                        # 处理categoryIDs
                        if 'categoryIDs' in filter_info:
                            for category_id in filter_info['categoryIDs']:
                                facility_effects.append((facility_id, category_id, 0))
                        
                        # 处理groupIDs
                        if 'groupIDs' in filter_info:
                            for group_id in filter_info['groupIDs']:
                                facility_effects.append((facility_id, 0, group_id))
                        
                        # 如果既没有categoryIDs也没有groupIDs，使用默认值
                        if 'categoryIDs' not in filter_info and 'groupIDs' not in filter_info:
                            facility_effects.append((facility_id, 0, 0))
    
    return facility_effects

def insert_facility_rig_effects(cursor: sqlite3.Cursor, effects_data: List[Tuple]):
    """插入设施装配效果数据到数据库"""
    cursor.execute('DELETE FROM facility_rig_effects')
    
    cursor.executemany('''
        INSERT OR REPLACE INTO facility_rig_effects 
        (id, category, group_id)
        VALUES (?, ?, ?)
    ''', effects_data)

def process_facility_rig_effects(cursor: sqlite3.Cursor, lang: str):
    """处理设施装配效果数据（用于main.py集成）"""
    # 只在处理英文数据库时下载数据，避免重复下载
    global _modifier_data, _filter_data
    
    if lang == 'en':
        print("下载工业修正源数据...")
        modifier_url = "https://sde.hoboleaks.space/tq/industrymodifiersources.json"
        filter_url = "https://sde.hoboleaks.space/tq/industrytargetfilters.json"
        
        _modifier_data = download_json(modifier_url)
        _filter_data = download_json(filter_url)
        
        print(f"下载完成 - 修正源数据: {len(_modifier_data)} 个设施")
        print(f"下载完成 - 目标过滤器: {len(_filter_data)} 个过滤器")
    
    # 创建表
    create_facility_rig_effects_table(cursor)
    
    # 处理数据
    effects_data = process_industry_modifier_sources(_modifier_data, _filter_data, cursor)
    
    # 插入数据
    insert_facility_rig_effects(cursor, effects_data)
    
    # 显示统计信息
    cursor.execute('SELECT COUNT(*) FROM facility_rig_effects')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT id) FROM facility_rig_effects')
    facility_count = cursor.fetchone()[0]
    
    print(f"语言 {lang}: 总记录数 {total_count}, 设施数量 {facility_count}")

# 全局变量用于缓存下载的数据
_modifier_data = None
_filter_data = None

def main():
    """独立运行时的主函数"""
    # 下载数据
    print("开始下载工业修正源数据...")
    modifier_url = "https://sde.hoboleaks.space/tq/industrymodifiersources.json"
    filter_url = "https://sde.hoboleaks.space/tq/industrytargetfilters.json"
    
    modifier_data = download_json(modifier_url)
    filter_data = download_json(filter_url)
    
    print(f"下载完成 - 修正源数据: {len(modifier_data)} 个设施")
    print(f"下载完成 - 目标过滤器: {len(filter_data)} 个过滤器")
    
    # 连接数据库
    db_files = [
        'output/db/item_db_zh.sqlite',
        'output/db/item_db_en.sqlite'
    ]
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            print(f"数据库文件不存在: {db_file}")
            continue
            
        print(f"\n处理数据库: {db_file}")
        
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # 创建表
            create_facility_rig_effects_table(cursor)
            
            # 处理数据
            effects_data = process_industry_modifier_sources(modifier_data, filter_data, cursor)
            
            # 插入数据
            insert_facility_rig_effects(cursor, effects_data)
            
            # 提交事务
            conn.commit()
            
            # 显示统计信息
            cursor.execute('SELECT COUNT(*) FROM facility_rig_effects')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT id) FROM facility_rig_effects')
            facility_count = cursor.fetchone()[0]
            
            print(f"数据库 {db_file} 处理完成:")
            print(f"  - 总记录数: {total_count}")
            print(f"  - 设施数量: {facility_count}")

if __name__ == "__main__":
    main() 