import yaml
import time
import os
import requests
from pathlib import Path

def download_faction_icon(faction_id, output_dir):
    """从EVE CDN下载派系图标"""
    # 构建图标URL和输出路径
    icon_url = f"https://images.evetech.net/corporations/{faction_id}/logo"
    icon_path = Path(output_dir) / f"faction_{faction_id}.png"
    default_icon_path = Path(output_dir) / "corporations_default.png"
    
    # 如果文件已存在则跳过
    if icon_path.exists():
        return
        
    try:
        # 下载图标
        response = requests.get(icon_url)
        response.raise_for_status()
        
        # 保存图标
        with open(icon_path, 'wb') as f:
            f.write(response.content)
            
        print(f"下载图标成功: faction_{faction_id}")
        
    except Exception as e:
        print(f"下载图标失败 faction_{faction_id}: {str(e)}")
        # 如果默认图标不存在，先下载默认图标
        if not default_icon_path.exists():
            try:
                default_response = requests.get("https://images.evetech.net/corporations/1/logo")
                default_response.raise_for_status()
                with open(default_icon_path, 'wb') as f:
                    f.write(default_response.content)
                print("下载默认图标成功")
            except Exception as e:
                print(f"下载默认图标失败: {str(e)}")
                return
        
        # 复制默认图标
        import shutil
        shutil.copy2(default_icon_path, icon_path)
        print(f"使用默认图标: faction_{faction_id}")

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建输出目录
    output_dir = "output/Icons"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建factions表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS factions (
        id INTEGER NOT NULL PRIMARY KEY,
        name TEXT,
        iconName TEXT
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM factions')
    
    # 处理每个派系
    for faction_id, faction_data in yaml_data.items():
        # 获取当前语言的名称
        name = faction_data.get('nameID', {}).get(language, '')
        if not name:  # 如果当前语言的name为空，尝试获取英语的name
            name = faction_data.get('nameID', {}).get('en', '')
        
        # 下载图标
        download_faction_icon(faction_id, output_dir)
        
        # 设置图标文件名
        icon_name = f"faction_{faction_id}.png"
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO factions 
            (id, name, iconName)
            VALUES (?, ?, ?)
        ''', (faction_id, name, icon_name))