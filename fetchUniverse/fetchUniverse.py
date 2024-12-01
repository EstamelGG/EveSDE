import aiohttp
import asyncio
import json
import ssl
import certifi
import logging
import os
import random
from typing import Dict, List, Optional
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 支持的语言列表
LANGUAGES = ['de', 'en', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']

# API基础URL
BASE_URL = 'https://esi.evetech.net/latest'

# 配置超时
TIMEOUT = ClientTimeout(total=30)  # 30秒总超时
RETRY_TIMES = 3  # 最大重试次数

# 缓存配置
CACHE_DIR = './cache'

# 并发配置
BATCH_SIZE = 10  # 每批处理的星系数量, 建议10

def get_cache_path(url: str) -> str:
    """获取缓存文件路径"""
    # 只缓存详情API的响应
    if 'language=' not in url and 'stars' not in url and 'stargates' not in url and 'planets' not in url:
        return None
        
    # 详情API的URL
    if 'stars' in url:
        item_type = 'stars'
        item_id = url.split(f'/{item_type}/')[1].split('/')[0]
        filename = f"{item_type}_{item_id}.json"
    elif 'stargates' in url:
        item_type = 'stargates'
        item_id = url.split(f'/{item_type}/')[1].split('/')[0]
        filename = f"{item_type}_{item_id}.json"
    elif 'planets' in url:
        item_type = 'planets'
        item_id = url.split(f'/{item_type}/')[1].split('/')[0]
        filename = f"{item_type}_{item_id}.json"
    else:
        item_type = 'regions' if '/regions/' in url else 'constellations' if '/constellations/' in url else 'systems'
        item_id = url.split(f'/{item_type}/')[1].split('/')[0]
        lang = url.split('language=')[1].split('&')[0]
        filename = f"{item_type}_{item_id}_{lang}.json"
    
    return os.path.join(CACHE_DIR, filename)

def save_to_cache(url: str, data: dict):
    """保存数据到缓存"""
    try:
        cache_path = get_cache_path(url)
        if cache_path is None:  # 不缓存列表API的响应
            return
            
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        logger.debug(f"数据已缓存: {url}")
    except Exception as e:
        logger.error(f"保存缓存失败 {url}: {str(e)}")

def load_from_cache(url: str) -> Optional[dict]:
    """从缓存加载数据"""
    try:
        cache_path = get_cache_path(url)
        if cache_path is None:  # 不从缓存加载列表API的响应
            return None
            
        if not os.path.exists(cache_path):
            return None
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.debug(f"从缓存加载: {url}")
        return data
    except Exception as e:
        logger.error(f"读取缓存失败 {url}: {str(e)}")
        return None

@retry(stop=stop_after_attempt(RETRY_TIMES), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict:
    """通用的异步JSON获取函数"""
    # 先尝试从缓存加载
    cached_data = load_from_cache(url)
    if cached_data is not None:
        logger.debug(f"使用缓存数据: {url}")
        return cached_data
        
    try:
        async with session.get(url, timeout=TIMEOUT) as response:
            if response.status != 200:
                logger.error(f"请求失败: {url}, 状态码: {response.status}")
                response_text = await response.text()
                logger.error(f"响应内容: {response_text}")
                response.raise_for_status()
            data = await response.json()
            
            # 保存到缓存
            save_to_cache(url, data)
            # logger.info(f"从API获取新数据: {url}")
            return data
    except Exception as e:
        logger.error(f"请求出错: {url}, 错误: {str(e)}")
        raise

async def fetch_details_with_languages(session: aiohttp.ClientSession, base_url: str, item_id: int) -> Dict[str, str]:
    """获取不同语言版本的详情"""
    tasks = []
    urls = []  # 保存URL列表用于缓存查找
    for lang in LANGUAGES:
        url = f"{base_url}/{item_id}/?datasource=tranquility&language={lang}"
        urls.append(url)
        tasks.append(fetch_json(session, url))
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f"获取到的结果: {results}")
        
        # 处理可能的异常
        valid_results = []
        valid_langs = []
        for lang, result in zip(LANGUAGES, results):
            if isinstance(result, Exception):
                logger.error(f"语言 {lang} 的请求失败: {str(result)}")
                continue
            if 'name' not in result:
                logger.error(f"语言 {lang} 的响应中缺少name字段: {result}")
                continue
            valid_results.append(result)
            valid_langs.append(lang)
        
        if not valid_results:
            raise Exception("所有语言的请求都失败了")
        
        names = {lang: result['name'] for lang, result in zip(valid_langs, valid_results)}
        return names, valid_results[0]
    except Exception as e:
        logger.error(f"处理多语言数据时出错: {str(e)}")
        raise

async def fetch_star_info(session: aiohttp.ClientSession, star_id: int) -> Optional[int]:
    """获取恒星信息"""
    try:
        url = f"{BASE_URL}/universe/stars/{star_id}/?datasource=tranquility"
        star_data = await fetch_json(session, url)
        return star_data.get('type_id')
    except Exception as e:
        logger.error(f"获取恒星信息失败 star_id {star_id}: {str(e)}")
        return 6 # 默认用6号恒星类型

async def fetch_stars_batch(session: aiohttp.ClientSession, star_ids: List[int]) -> Dict[int, Optional[int]]:
    """批量获取恒星信息"""
    if not star_ids:
        return {}
    
    star_type_map = {}
    valid_star_ids = [sid for sid in star_ids if sid is not None]
    
    # 按BATCH_SIZE分批处理
    for i in range(0, len(valid_star_ids), BATCH_SIZE):
        batch_star_ids = valid_star_ids[i:i + BATCH_SIZE]
        tasks = []
        for star_id in batch_star_ids:
            url = f"{BASE_URL}/universe/stars/{star_id}/?datasource=tranquility"
            tasks.append(fetch_json(session, url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for star_id, result in zip(batch_star_ids, results):
            try:
                if isinstance(result, Exception):
                    logger.error(f"获取恒星信息失败 star_id {star_id}: {str(result)}")
                    star_type_map[star_id] = 6  # 默认用6号恒星类型
                    continue
                star_type_map[star_id] = result.get('type_id', 6)
            except Exception as e:
                logger.error(f"处理恒星信息失败 star_id {star_id}: {str(e)}")
                star_type_map[star_id] = 6  # 默认用6号恒星类型
        
        logger.info(f"完成处理恒星批次 {i//BATCH_SIZE + 1}/{(len(valid_star_ids) + BATCH_SIZE - 1)//BATCH_SIZE}, "
                   f"当前批次大小: {len(batch_star_ids)}")
            
    return star_type_map

async def process_systems_batch(session: aiohttp.ClientSession, systems_batch: List[int], 
                              total_systems_processed: int, total_systems_count: int) -> Dict[str, dict]:
    """批量处理星系数据"""
    tasks = []
    for sys_id in systems_batch:
        tasks.append(fetch_details_with_languages(
            session,
            f"{BASE_URL}/universe/systems",
            sys_id
        ))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 收集所有star_ids
    star_ids = []
    valid_systems = []
    for sys_id, result in zip(systems_batch, results):
        try:
            if isinstance(result, Exception):
                logger.error(f"处理星系 {sys_id} 时出错: {str(result)}")
                continue
            names, sys_details = result
            star_id = sys_details.get('star_id')
            if star_id:  # 只添加有效的star_id
                star_ids.append(star_id)
            valid_systems.append((sys_id, names, sys_details, star_id))
        except Exception as e:
            logger.error(f"处理星系 {sys_id} 时出错: {str(e)}")
            continue
    
    # 批量获取恒星类型
    star_type_map = {}
    if star_ids:  # 只在有有效的star_ids时调用
        star_type_map = await fetch_stars_batch(session, star_ids)
    
    # 处理结果
    systems_data = {}
    for i, (sys_id, names, sys_details, star_id) in enumerate(valid_systems):
        try:
            security_status = sys_details.get('security_status')
            solar_type_id = star_type_map.get(star_id) if star_id else None
            
            # 获取行星信息
            planets = sys_details.get('planets', [])
            
            systems_data[str(sys_id)] = {
                'system_name': names,
                'system_info': {
                    'security_status': security_status,
                    'solar_type_id': solar_type_id,
                    'star_id': star_id,
                    'position': sys_details.get('position', {}),
                    'stargates': sys_details.get('stargates', []),
                    'stations': sys_details.get('stations', []),
                    'planets': planets  # 添加行星信息
                }
            }
            
            current_processed = total_systems_processed + i + 1
            progress_percentage = (current_processed / total_systems_count) * 100
            logger.info(f"处理星系 {sys_id} 完成 - 总进度: {current_processed}/{total_systems_count} ({progress_percentage:.2f}%)")
            logger.debug(f"星系 {sys_id} 安全等级: {security_status}, 恒星ID: {star_id}, 恒星类型ID: {solar_type_id}, 行星数量: {len(planets)}")
            
        except Exception as e:
            logger.error(f"处理星系 {sys_id} 时出错: {str(e)}")
            continue
            
    return systems_data

async def fetch_universe_data():
    """获取完整的宇宙数据"""
    # 创建缓存目录
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 创建SSL上下文
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # 配置ClientSession使用SSL上下文
    conn = aiohttp.TCPConnector(ssl=ssl_context, limit=20)  # 增加并发连接数限制
    async with aiohttp.ClientSession(connector=conn, timeout=TIMEOUT) as session:
        try:
            # 获取所有ID列表
            logger.info("开始获取星域列表...")
            regions = await fetch_json(session, f"{BASE_URL}/universe/regions/?datasource=tranquility")
            logger.info(f"获取到 {len(regions)} 个星域")
            
            logger.info("开始获取星座列表...")
            constellations = await fetch_json(session, f"{BASE_URL}/universe/constellations/?datasource=tranquility")
            logger.info(f"获取到 {len(constellations)} 个星座")
            
            logger.info("开始获取星系列表...")
            systems = await fetch_json(session, f"{BASE_URL}/universe/systems/?datasource=tranquility")
            logger.info(f"获取到 {len(systems)} 个星系")

            # 构建宇宙结构
            universe_data = {}
            
            # 初始化计数器
            total_systems_processed = 0
            total_systems_count = len(systems)
            logger.info(f"开始处理宇宙结构，总计 {total_systems_count} 个星系待处理")

            # 获取所有星域详情
            for i, region_id in enumerate(regions, 1):
                logger.info(f"正在处理星域 {region_id} ({i}/{len(regions)})")
                try:
                    names, region_details = await fetch_details_with_languages(
                        session, 
                        f"{BASE_URL}/universe/regions", 
                        region_id
                    )
                    
                    # 获取该星域下的所有星座
                    constellation_data = {}
                    for const_id in region_details['constellations']:
                        logger.info(f"处理星域 {region_id} 的星座 {const_id}")
                        try:
                            const_names, const_details = await fetch_details_with_languages(
                                session,
                                f"{BASE_URL}/universe/constellations",
                                const_id
                            )
                            
                            # 获取该星座下的所有星系
                            system_data = {}
                            systems_list = const_details['systems']
                            total_systems = len(systems_list)
                            logger.info(f"星座 {const_id} 包含 {total_systems} 个星系")
                            
                            # 批量处理星系
                            for batch_start in range(0, total_systems, BATCH_SIZE):
                                batch = systems_list[batch_start:batch_start + BATCH_SIZE]
                                batch_data = await process_systems_batch(
                                    session, 
                                    batch,
                                    total_systems_processed,
                                    total_systems_count
                                )
                                system_data.update(batch_data)
                                total_systems_processed += len(batch)
                            
                            constellation_data[str(const_id)] = {
                                'constellation_name': const_names,
                                'systems': system_data
                            }
                        except Exception as e:
                            logger.error(f"处理星座 {const_id} 时出错: {str(e)}")
                            continue
                    
                    universe_data[str(region_id)] = {
                        'region_name': names,
                        'constellations': constellation_data
                    }
                except Exception as e:
                    logger.error(f"处理星域 {region_id} 时出错: {str(e)}")
                    continue

            return universe_data
        except Exception as e:
            logger.error(f"获取宇宙数据时出错: {str(e)}")
            raise

def analyze_stargates(universe_data: dict):
    """分析所有星系的星门数据"""
    # 收集所有星门ID
    stargate_ids = set()
    
    # 遍历所有星域
    for region_id, region_data in universe_data.items():
        # 遍历所有星座
        for constellation_id, constellation_data in region_data['constellations'].items():
            # 遍历所有星系
            for system_id, system_data in constellation_data['systems'].items():
                # 获取该星系的星门列表
                stargates = system_data['system_info'].get('stargates', [])
                stargate_ids.update(stargates)
    
    # 转换为列表以便随机选择
    stargate_list = list(stargate_ids)
    
    # 随机选择5个星门ID
    random_stargates = random.sample(stargate_list, min(5, len(stargate_list)))
    
    # 打印统计信息
    logger.info(f"总共有 {len(stargate_ids)} 个唯一的星门ID")
    logger.info(f"随机选择的5个星门ID: {random_stargates}")

async def fetch_stargate_info(session: aiohttp.ClientSession, stargate_id: int) -> dict:
    """获取星门信息"""
    try:
        url = f"{BASE_URL}/universe/stargates/{stargate_id}/?datasource=tranquility"
        stargate_data = await fetch_json(session, url)
        return {
            'stargate_id': stargate_id,
            'system_id': stargate_data.get('system_id'),
            'destination': {
                'system_id': stargate_data.get('destination', {}).get('system_id'),
                'stargate_id': stargate_data.get('destination', {}).get('stargate_id')
            }
        }
    except Exception as e:
        logger.error(f"获取星门信息失败 stargate_id {stargate_id}: {str(e)}")
        return None

async def fetch_all_stargates():
    """获取所有星门信息并缓存"""
    try:
        logger.info("开始获取所有星门信息...")
        
        # 读取universe_data.json获取所有星门ID
        with open('universe_data.json', 'r', encoding='utf-8') as f:
            universe_data = json.load(f)
        
        # 收集所有星门ID
        stargate_ids = set()
        for region_data in universe_data.values():
            for constellation_data in region_data['constellations'].values():
                for system_data in constellation_data['systems'].values():
                    stargate_ids.update(system_data['system_info'].get('stargates', []))
        
        logger.info(f"总共有 {len(stargate_ids)} 个唯一的星门ID")
        
        # 创建SSL上下文，增加并发连接数限制
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context, limit=150)
        
        async with aiohttp.ClientSession(connector=conn, timeout=TIMEOUT) as session:
            # 使用100并发获取星门信息
            CONCURRENT_LIMIT = 100
            semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
            
            async def fetch_with_semaphore(stargate_id: int):
                async with semaphore:
                    try:
                        return await fetch_stargate_info(session, stargate_id)
                    except Exception as e:
                        logger.error(f"获取星门信息失败 stargate_id {stargate_id}: {str(e)}")
                        return None
            
            # 创建所有任务
            tasks = [fetch_with_semaphore(stargate_id) for stargate_id in stargate_ids]
            
            # 使用gather并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            stargate_info_map = {}
            for stargate_id, result in zip(stargate_ids, results):
                try:
                    if isinstance(result, Exception):
                        logger.error(f"处理星门信息失败 stargate_id {stargate_id}: {str(result)}")
                        continue
                    if result:
                        stargate_info_map[stargate_id] = result
                except Exception as e:
                    logger.error(f"处理星门信息失败 stargate_id {stargate_id}: {str(e)}")
            
            logger.info(f"完成处理所有星门信息，共 {len(stargate_info_map)}/{len(stargate_ids)} 个成功")
            
            # 保存星门信息到文件
            with open('stargate_info.json', 'w', encoding='utf-8') as f:
                json.dump(stargate_info_map, f, ensure_ascii=False, indent=2)
            logger.info("星门信息已保存到 stargate_info.json")
            
            return stargate_info_map
            
    except Exception as e:
        logger.error(f"获取星门信息时出错: {str(e)}")
        raise

def build_system_connections(stargate_info_map: dict) -> dict:
    """根据星门信息构建星系连接关系"""
    system_connections = {}
    
    for stargate_info in stargate_info_map.values():
        if not stargate_info:
            continue
            
        source_system = str(stargate_info['system_id'])
        dest_system = stargate_info['destination']['system_id']
        
        # 添加双向连接
        if source_system not in system_connections:
            system_connections[source_system] = set()
        if dest_system not in system_connections:
            system_connections[dest_system] = set()
            
        system_connections[source_system].add(dest_system)
        system_connections[dest_system].add(source_system)
    
    # 将集合转换为列表
    for system_id in system_connections:
        system_connections[system_id] = list(system_connections[system_id])
    
    return system_connections

async def fetch_planet_info(session: aiohttp.ClientSession, planet_id: int) -> Optional[dict]:
    """获取行星信息"""
    try:
        url = f"{BASE_URL}/universe/planets/{planet_id}/?datasource=tranquility"
        planet_data = await fetch_json(session, url)
        return {
            'planet_id': planet_id,
            'type_id': planet_data.get('type_id'),
            'system_id': planet_data.get('system_id'),
            'position': planet_data.get('position', {})
        }
    except Exception as e:
        logger.error(f"获取行星信息失败 planet_id {planet_id}: {str(e)}")
        return None

async def fetch_all_planets():
    """获取所有行星信息并缓存"""
    try:
        logger.info("开始获取所有行星信息...")
        
        # 读取universe_data.json获取所有行星ID
        with open('universe_data.json', 'r', encoding='utf-8') as f:
            universe_data = json.load(f)
        
        # 收集所有行星ID
        planet_ids = set()
        for region_data in universe_data.values():
            for constellation_data in region_data['constellations'].values():
                for system_data in constellation_data['systems'].values():
                    # 获取星系中的行星ID
                    for planet in system_data['system_info'].get('planets', []):
                        if isinstance(planet, dict) and 'planet_id' in planet:
                            planet_ids.add(planet['planet_id'])
                        elif isinstance(planet, int):
                            planet_ids.add(planet)
        
        logger.info(f"总共有 {len(planet_ids)} 个唯一的行星ID")
        
        # 创建SSL上下文，增加并发连接数限制
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        conn = aiohttp.TCPConnector(ssl=ssl_context, limit=150)
        
        async with aiohttp.ClientSession(connector=conn, timeout=TIMEOUT) as session:
            # 使用50并发获取行星信息
            CONCURRENT_LIMIT = 50
            semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
            
            async def fetch_with_semaphore(planet_id: int):
                async with semaphore:
                    try:
                        return await fetch_planet_info(session, planet_id)
                    except Exception as e:
                        logger.error(f"获取行星信息失败 planet_id {planet_id}: {str(e)}")
                        return None
            
            # 创建所有任务
            tasks = [fetch_with_semaphore(planet_id) for planet_id in planet_ids]
            
            # 使用gather并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            planet_info_map = {}
            planet_types = set()  # 收集所有行星类型
            for planet_id, result in zip(planet_ids, results):
                try:
                    if isinstance(result, Exception):
                        logger.error(f"处理行星信息失败 planet_id {planet_id}: {str(result)}")
                        continue
                    if result:
                        planet_info_map[planet_id] = result
                        # 添加行星类型到集合中
                        if 'type_id' in result and result['type_id']:
                            planet_types.add(result['type_id'])
                except Exception as e:
                    logger.error(f"处理行星信息失败 planet_id {planet_id}: {str(e)}")
            
            logger.info(f"完成处理所有行星信息，共 {len(planet_info_map)}/{len(planet_ids)} 个成功")
            logger.info(f"发现 {len(planet_types)} 种不同的行星类型: {sorted(list(planet_types))}")
            
            # 保存行星信息到文件
            with open('planet_info.json', 'w', encoding='utf-8') as f:
                json.dump(planet_info_map, f, ensure_ascii=False, indent=2)
            logger.info("行星信息已保存到 planet_info.json")
            
            # 保存行星类型列表到文件
            with open('planet_types.json', 'w', encoding='utf-8') as f:
                json.dump(sorted(list(planet_types)), f, ensure_ascii=False, indent=2)
            logger.info("行星类型列表已保存到 planet_types.json")
            
            return planet_info_map, planet_types
            
    except Exception as e:
        logger.error(f"获取行星信息时出错: {str(e)}")
        raise

def merge_universe_data():
    """合并universe_data.json和星门信息"""
    try:
        logger.info("开始合并宇宙数据和星门信息...")
        
        # 读取universe_data.json
        with open('universe_data.json', 'r', encoding='utf-8') as f:
            universe_data = json.load(f)
            
        # 读取星门信息
        with open('stargate_info.json', 'r', encoding='utf-8') as f:
            stargate_info_map = json.load(f)
        
        # 读取行星信息
        planet_info_map = {}
        planet_types = set()
        if os.path.exists('planet_info.json'):
            with open('planet_info.json', 'r', encoding='utf-8') as f:
                planet_info_map = json.load(f)
            if os.path.exists('planet_types.json'):
                with open('planet_types.json', 'r', encoding='utf-8') as f:
                    planet_types = set(json.load(f))
        
        # 构建星系连接关系
        system_connections = build_system_connections(stargate_info_map)
        
        # 合并数据
        merged_data = merge_system_connections(universe_data, system_connections)
        
        # 添加行星信息到合并后的数据中
        if planet_info_map:
            logger.info("开始添加行星信息到宇宙数据中...")
            for region_data in merged_data.values():
                for constellation_data in region_data['constellations'].values():
                    for system_id, system_data in constellation_data['systems'].items():
                        # 获取星系中的行星
                        planets = system_data['system_info'].get('planets', [])
                        if planets:
                            # 按类型组织行星
                            planets_by_type = {}
                            # 初始化所有类型的空列表
                            for planet_type in planet_types:
                                planets_by_type[f"type_{planet_type}"] = []
                            
                            # 将行星按类型分类
                            for planet in planets:
                                planet_id = planet['planet_id'] if isinstance(planet, dict) else planet
                                if str(planet_id) in planet_info_map:
                                    planet_info = planet_info_map[str(planet_id)]
                                    type_id = planet_info.get('type_id')
                                    if type_id:
                                        type_key = f"type_{type_id}"
                                        if type_key not in planets_by_type:
                                            planets_by_type[type_key] = []
                                        planets_by_type[type_key].append(planet_id)
                            
                            # 更新星系中的行星信息
                            system_data['system_info']['planets'] = planets_by_type
            
            logger.info("行星信息已添加到宇宙数据中")
        
        # 直接覆盖 universe_data.json
        with open('universe_data.json', 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        logger.info("合并后的数据已保存到 universe_data.json")
        
    except FileNotFoundError as e:
        logger.error(f"找不到所需的文件: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"合并数据时出错: {str(e)}")
        raise

async def main():
    """主函数"""
    try:
        logger.info("开始获取宇宙数据...")
        universe_data = await fetch_universe_data()
        
        # 将数据保存到文件
        output_file = 'universe_data.json'
        logger.info(f"正在将数据保存到 {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(universe_data, f, ensure_ascii=False, indent=2)
        logger.info("数据保存完成")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise

def merge_system_connections(universe_data: dict, system_connections: dict) -> dict:
    """将星系连接关系合并到宇宙数据中"""
    try:
        logger.info("开始合并星系连接关系...")
        
        # 遍历所有星域
        for region_data in universe_data.values():
            # 遍历所有星座
            for constellation_data in region_data['constellations'].values():
                # 遍历所有星系
                for system_id, system_data in constellation_data['systems'].items():
                    # 添加neighbours字段
                    system_data['system_info']['neighbours'] = system_connections.get(system_id, [])
        
        logger.info("星系连接关系合并完成")
        return universe_data
    except Exception as e:
        logger.error(f"合并星系连接关系时出错: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # 第一步：获取宇宙数据
        logger.info("第一步：获取宇宙数据...")
        asyncio.run(main())

        # 第二步：获取所有星门信息
        logger.info("第二步：获取所有星门信息...")
        asyncio.run(fetch_all_stargates())
        
        # 第三步：获取所有行星信息
        logger.info("第三步：获取所有行星信息...")
        asyncio.run(fetch_all_planets())

        # 第四步：合并数据
        logger.info("第四步：合并数据...")
        merge_universe_data()
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise
