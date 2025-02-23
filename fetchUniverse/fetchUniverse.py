import aiohttp
import asyncio
import json
import ssl
import certifi
import logging
import os
from typing import Dict, List, Optional
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, timedelta

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
BATCH_SIZE = 10  # 每批处理的星系数量

def get_cache_path(url: str) -> str:
    """获取缓存文件路径"""
    # 只缓存详情API的响应
    if 'language=' not in url and 'stars' not in url:
        return None
        
    # 详情API的URL
    if 'stars' in url:
        item_type = 'stars'
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
            star_ids.append(star_id)
            valid_systems.append((sys_id, names, sys_details, star_id))
        except Exception as e:
            logger.error(f"处理星系 {sys_id} 时出错: {str(e)}")
            continue
    
    # 批量获取恒星类型
    star_type_map = await fetch_stars_batch(session, star_ids)
    
    # 处理结果
    systems_data = {}
    for i, (sys_id, names, sys_details, star_id) in enumerate(valid_systems):
        try:
            security_status = sys_details.get('security_status')
            solar_type_id = star_type_map.get(star_id) if star_id else None
            
            systems_data[str(sys_id)] = {
                'system_name': names,
                'system_info': {
                    'security_status': security_status,
                    'solar_type_id': solar_type_id,
                    'star_id': star_id
                }
            }
            
            current_processed = total_systems_processed + i + 1
            progress_percentage = (current_processed / total_systems_count) * 100
            logger.info(f"处理星系 {sys_id} 完成 - 总进度: {current_processed}/{total_systems_count} ({progress_percentage:.2f}%)")
            logger.debug(f"星系 {sys_id} 安全等级: {security_status}, 恒星ID: {star_id}, 恒星类型ID: {solar_type_id}")
            
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

if __name__ == "__main__":
    asyncio.run(main())
