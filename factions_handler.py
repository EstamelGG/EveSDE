import yaml
import time
import os
import aiohttp
import asyncio
from pathlib import Path
import shutil

async def download_faction_icon(faction_ids, output_dir):
    """从EVE CDN下载派系图标，支持异步并发下载和自动重试
    
    Args:
        faction_ids: 单个faction_id或faction_id列表
        output_dir: 输出目录
    """
    # 确保我们处理的是列表
    if not isinstance(faction_ids, list):
        faction_ids = [faction_ids]
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 确保默认图标存在
    default_icon_path = Path(output_dir) / "corporations_default.png"
    if not default_icon_path.exists():
        await _download_default_icon(default_icon_path)
    
    # 过滤出需要下载的faction_ids(文件不存在的)
    new_faction_ids = [
        faction_id for faction_id in faction_ids 
        if not (Path(output_dir) / f"faction_{faction_id}.png").exists()
    ]
    
    # 如果没有新的faction_ids需要下载，直接返回
    if not new_faction_ids:
        print("所有派系图标已存在，跳过下载")
        return
    
    # 创建信号量以限制并发请求数
    semaphore = asyncio.Semaphore(10)
    
    # 创建下载任务
    tasks = [
        _download_single_icon(faction_id, output_dir, default_icon_path, semaphore) 
        for faction_id in new_faction_ids
    ]
    
    print(f"准备下载 {len(new_faction_ids)} 个新的派系图标...")
    
    # 异步执行所有下载任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    for faction_id, result in zip(new_faction_ids, results):
        if isinstance(result, Exception):
            print(f"下载过程发生异常 faction_{faction_id}: {str(result)}")
        elif result:
            print(f"下载图标成功: faction_{faction_id}")
        else:
            print(f"下载失败，使用默认图标: faction_{faction_id}")

async def _download_single_icon(faction_id, output_dir, default_icon_path, semaphore):
    """下载单个派系图标，带有重试逻辑"""
    icon_url = f"https://images.evetech.net/corporations/{faction_id}/logo"
    icon_path = Path(output_dir) / f"faction_{faction_id}.png"
    
    # 如果文件已存在则跳过 (额外检查，虽然之前已过滤)
    if icon_path.exists():
        return True
    
    # 重试5次，每次超时3秒
    max_retries = 5
    timeout = 3
    
    async with semaphore:  # 使用信号量限制并发数
        for attempt in range(max_retries):
            try:
                # 使用上下文管理器确保资源被正确释放
                async with aiohttp.ClientSession() as session:
                    # 设置超时
                    async with session.get(icon_url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                        if response.status != 200:
                            response.raise_for_status()
                        
                        # 读取响应内容
                        content = await response.read()
                        
                        # 保存图标
                        with open(icon_path, 'wb') as f:
                            f.write(content)
                            
                return True
                
            except (aiohttp.ClientError, asyncio.TimeoutError, IOError) as e:
                # 如果不是最后一次尝试，等待一小段时间后重试
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (attempt + 1)  # 逐渐增加等待时间
                    print(f"下载 faction_{faction_id} 失败，{wait_time}秒后重试 ({attempt+1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"下载 faction_{faction_id} 失败，已达到最大重试次数: {str(e)}")
    
    # 如果所有重试都失败，使用默认图标
    try:
        shutil.copy2(default_icon_path, icon_path)
        return False
    except Exception as e:
        print(f"复制默认图标失败 faction_{faction_id}: {str(e)}")
        return False

async def _download_default_icon(default_icon_path):
    """下载默认图标，带有重试逻辑"""
    # 如果默认图标已存在，直接返回
    if default_icon_path.exists():
        return True
        
    max_retries = 5
    timeout = 3
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://images.evetech.net/corporations/1/logo", 
                                       timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        response.raise_for_status()
                    
                    content = await response.read()
                    with open(default_icon_path, 'wb') as f:
                        f.write(content)
                    
                    print("下载默认图标成功")
                    return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 0.5 * (attempt + 1)
                print(f"下载默认图标失败，{wait_time}秒后重试 ({attempt+1}/{max_retries}): {str(e)}")
                await asyncio.sleep(wait_time)
            else:
                print(f"下载默认图标失败，已达到最大重试次数: {str(e)}")
                return False

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

async def process_data_async(yaml_data, cursor, language):
    """处理YAML数据并写入数据库（异步版本）"""
    # 创建输出目录
    output_dir = "output/Icons"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建factions表，为每种语言添加一个列
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS factions (
        id INTEGER NOT NULL PRIMARY KEY,
        name TEXT,
        de_name TEXT,
        en_name TEXT,
        es_name TEXT,
        fr_name TEXT,
        ja_name TEXT,
        ko_name TEXT,
        ru_name TEXT,
        zh_name TEXT,
        iconName TEXT
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM factions')
    
    # 处理每个派系
    all_faction_ids = list(yaml_data.keys())
    
    # 批量下载所有图标 (异步)
    await download_faction_icon(all_faction_ids, output_dir)
    
    # 处理每个派系数据并写入数据库
    for faction_id, faction_data in yaml_data.items():
        # 获取当前语言的名称作为主要name
        name = faction_data.get('nameID', {}).get(language, '')
        if not name:  # 如果当前语言的name为空，使用英语名称
            name = faction_data.get('nameID', {}).get('en', '')
            
        # 获取所有语言的名称
        names = {
            'de': faction_data.get('nameID', {}).get('de', ''),
            'en': faction_data.get('nameID', {}).get('en', ''),
            'es': faction_data.get('nameID', {}).get('es', ''),
            'fr': faction_data.get('nameID', {}).get('fr', ''),
            'ja': faction_data.get('nameID', {}).get('ja', ''),
            'ko': faction_data.get('nameID', {}).get('ko', ''),
            'ru': faction_data.get('nameID', {}).get('ru', ''),
            'zh': faction_data.get('nameID', {}).get('zh', '')
        }
        
        # 设置图标文件名
        icon_name = f"faction_{faction_id}.png"
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO factions 
            (id, name, de_name, en_name, es_name, fr_name, ja_name, ko_name, ru_name, zh_name, iconName)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            faction_id, 
            name,
            names['de'],
            names['en'],
            names['es'],
            names['fr'],
            names['ja'],
            names['ko'],
            names['ru'],
            names['zh'],
            icon_name
        ))

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库（同步包装器）"""
    # 运行异步版本
    asyncio.run(process_data_async(yaml_data, cursor, language))