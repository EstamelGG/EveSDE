import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import os
import time
import aiohttp
import asyncio
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_yaml(file_path):
    """读取 npcCorporations.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

async def download_corporation_icon(corp_id, output_dir, semaphore, retry_count=5):
    """下载单个军团图标，带有重试逻辑"""
    url = f"https://images.evetech.net/corporations/{corp_id}/logo?size=128"
    filename = f"corperation_{corp_id}_128.png"
    filepath = Path(output_dir) / filename
    
    # 如果文件已存在，直接返回文件名
    if filepath.exists():
        logger.info(f"图标已存在，跳过下载: {filename}")
        return filename
    
    async with semaphore:  # 使用信号量限制并发数
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            logger.info(f"成功下载图标: {filename}")
                            return filename
                        else:
                            logger.warning(f"下载失败 (HTTP {response.status}): {filename}")
            except asyncio.TimeoutError:
                logger.warning(f"超时 (尝试 {attempt + 1}/{retry_count}): {filename}")
            except Exception as e:
                logger.warning(f"错误 (尝试 {attempt + 1}/{retry_count}): {filename} - {str(e)}")
            
            if attempt < retry_count - 1:
                await asyncio.sleep(1)  # 重试前等待1秒
    
    logger.error(f"所有重试均失败: {filename}")
    return None

async def download_all_corporation_icons(corp_ids, output_dir):
    """下载所有军团图标"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建信号量以限制并发请求数
    semaphore = asyncio.Semaphore(10)
    
    # 创建下载任务
    tasks = [
        download_corporation_icon(corp_id, output_dir, semaphore)
        for corp_id in corp_ids
    ]
    
    print(f"准备下载 {len(corp_ids)} 个军团图标...")
    
    # 异步执行所有下载任务
    results = await asyncio.gather(*tasks)
    
    # 返回结果字典
    return {corp_id: filename for corp_id, filename in zip(corp_ids, results) if filename}

def create_npc_corporations_table(cursor):
    """创建 npcCorporations 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS npcCorporations (
            corporation_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT,
            de_name TEXT,
            en_name TEXT,
            es_name TEXT,
            fr_name TEXT,
            ja_name TEXT,
            ko_name TEXT,
            ru_name TEXT,
            zh_name TEXT,
            description TEXT,
            faction_id INTEGER,
            icon_filename TEXT
        )
    ''')
    
    # 创建索引以优化查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_npcCorporations_faction_id ON npcCorporations(faction_id)')

async def process_data_async(corporations_data, cursor, lang):
    """处理 npcCorporations 数据并插入数据库（异步版本）"""
    create_npc_corporations_table(cursor)
    
    # 获取所有军团ID
    corp_ids = list(corporations_data.keys())
    
    # 下载所有图标
    output_dir = "output/Icons"
    icon_filenames = await download_all_corporation_icons(corp_ids, output_dir)
    
    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for corp_id, corp_info in corporations_data.items():
        # 获取当前语言的名称作为主要name
        name = corp_info.get('nameID', {}).get(lang) or corp_info.get('nameID', {}).get('en')
        
        # 获取所有语言的名称
        names = {
            'de': corp_info.get('nameID', {}).get('de', name),
            'en': corp_info.get('nameID', {}).get('en', name),
            'es': corp_info.get('nameID', {}).get('es', name),
            'fr': corp_info.get('nameID', {}).get('fr', name),
            'ja': corp_info.get('nameID', {}).get('ja', name),
            'ko': corp_info.get('nameID', {}).get('ko', name),
            'ru': corp_info.get('nameID', {}).get('ru', name),
            'zh': corp_info.get('nameID', {}).get('zh', name)
        }
        
        # 获取描述，如果没有对应语言的就用英文
        description = corp_info.get('descriptionID', {}).get(lang) or corp_info.get('descriptionID', {}).get('en')
        
        # 获取其他信息
        faction_id = corp_info.get('factionID', 500021)
        
        # 获取图标文件名
        icon_filename = icon_filenames.get(corp_id, "corporations_default.png")
        
        # 添加到批处理列表
        batch_data.append((
            corp_id,
            name,
            names['de'],
            names['en'],
            names['es'],
            names['fr'],
            names['ja'],
            names['ko'],
            names['ru'],
            names['zh'],
            description,
            faction_id,
            icon_filename
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO npcCorporations (
                    corporation_id,
                    name,
                    de_name, en_name, es_name, fr_name,
                    ja_name, ko_name, ru_name, zh_name,
                    description,
                    faction_id,
                    icon_filename
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO npcCorporations (
                corporation_id,
                name,
                de_name, en_name, es_name, fr_name,
                ja_name, ko_name, ru_name, zh_name,
                description,
                faction_id,
                icon_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)

def process_data(corporations_data, cursor, lang):
    """处理YAML数据并写入数据库（同步包装器）"""
    # 运行异步版本
    asyncio.run(process_data_async(corporations_data, cursor, lang)) 