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

def get_cache_path(url: str) -> str:
    """获取缓存文件路径"""
    # 从URL中提取ID和语言参数
    if 'language=' in url:
        # 详情API的URL
        item_type = 'regions' if '/regions/' in url else 'constellations' if '/constellations/' in url else 'systems'
        item_id = url.split(f'/{item_type}/')[1].split('/')[0]
        lang = url.split('language=')[1].split('&')[0]
        filename = f"{item_type}_{item_id}_{lang}.json"
    else:
        # 列表API的URL
        item_type = 'regions' if '/regions' in url else 'constellations' if '/constellations' in url else 'systems'
        filename = f"{item_type}_list.json"
    
    return os.path.join(CACHE_DIR, filename)

def save_to_cache(url: str, data: dict):
    """保存数据到缓存"""
    try:
        cache_path = get_cache_path(url)
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
            logger.info(f"从API获取新数据: {url}")
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

async def fetch_universe_data():
    """获取完整的宇宙数据"""
    # 创建缓存目录
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 创建SSL上下文
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # 配置ClientSession使用SSL上下文
    conn = aiohttp.TCPConnector(ssl=ssl_context, limit=10)  # 限制并发连接数
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
                            total_systems = len(const_details['systems'])
                            logger.info(f"星座 {const_id} 包含 {total_systems} 个星系")
                            
                            for sys_index, sys_id in enumerate(const_details['systems'], 1):
                                total_systems_processed += 1
                                progress_percentage = (total_systems_processed / total_systems_count) * 100
                                logger.info(f"处理星系 {sys_id} - 星座进度: {sys_index}/{total_systems}, 总进度: {total_systems_processed}/{total_systems_count} ({progress_percentage:.2f}%)")
                                try:
                                    sys_names, sys_details = await fetch_details_with_languages(
                                        session,
                                        f"{BASE_URL}/universe/systems",
                                        sys_id
                                    )
                                    
                                    security_status = sys_details.get('security_status')
                                    logger.debug(f"星系 {sys_id} 安全等级: {security_status}")
                                    
                                    system_data[str(sys_id)] = {
                                        'name': sys_names,
                                        'contains': {
                                            'security_status': security_status
                                        }
                                    }
                                    logger.debug(f"星系 {sys_id} 处理完成，名称: {sys_names.get('zh', 'N/A')}")
                                except Exception as e:
                                    logger.error(f"处理星系 {sys_id} 时出错: {str(e)}")
                                    continue
                            
                            constellation_data[str(const_id)] = {
                                'name': const_names,
                                'contains': system_data
                            }
                        except Exception as e:
                            logger.error(f"处理星座 {const_id} 时出错: {str(e)}")
                            continue
                    
                    universe_data[str(region_id)] = {
                        'name': names,
                        'contains': constellation_data
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
