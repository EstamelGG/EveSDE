import json
import time
import logging
from typing import List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 用于缓存universe数据
_universe_data: List[Tuple[int, int, int, float, int]] = []

def create_table(cursor):
    """创建universe表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universe (
            region_id INTEGER NOT NULL,
            constellation_id INTEGER NOT NULL,
            solarsystem_id INTEGER NOT NULL,
            system_security REAL,
            system_type INTEGER,
            PRIMARY KEY (region_id, constellation_id, solarsystem_id)
        )
    ''')

def read_universe_data(file_path: str = 'fetchUniverse/universe_data.json') -> dict:
    """读取universe_data.json文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"文件 {file_path} 不存在")
        return {}
    except json.JSONDecodeError:
        logger.error(f"文件 {file_path} 不是有效的JSON格式")
        return {}

def process_universe_data(data: dict, cursor=None) -> List[Tuple[int, int, int, float, int]]:
    """处理universe数据"""
    universe_data = []
    
    # 遍历所有星域
    for region_id, region_info in data.items():
        # 遍历星域下的所有星座
        for const_id, const_info in region_info.get('constellations', {}).items():
            # 遍历星座下的所有恒星系
            for sys_id, sys_info in const_info.get('systems', {}).items():
                # 获取安全等级
                security_status = sys_info.get('system_info', {}).get('security_status', 0.0)
                # 默认恒星类型为6（标准黄色恒星）
                system_type = 6
                
                # 将数据添加到列表
                universe_data.append((
                    int(region_id),
                    int(const_id),
                    int(sys_id),
                    float(security_status),
                    system_type
                ))
    
    # 如果提供了cursor，执行批量插入
    if cursor and universe_data:
        batch_size = 1000
        for i in range(0, len(universe_data), batch_size):
            batch = universe_data[i:i + batch_size]
            cursor.executemany(
                'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security, system_type) VALUES (?, ?, ?, ?, ?)',
                batch
            )
            logger.debug(f"已插入 {i + len(batch)}/{len(universe_data)} 条记录")
    
    return universe_data

def process_data(cursor, lang: str = 'en'):
    """主处理函数"""
    global _universe_data
    start_time = time.time()
    
    # 创建表
    create_table(cursor)
    
    # 只在处理英文数据时读取文件
    if lang == 'en':
        logger.info("处理英文宇宙数据...")
        _universe_data.clear()  # 清空缓存
        
        # 读取数据
        data = read_universe_data()
        if not data:
            logger.error("无法读取universe数据")
            return
            
        # 处理数据
        _universe_data = process_universe_data(data, cursor)
        logger.info(f"缓存了 {len(_universe_data)} 条宇宙数据记录")
    else:
        # 使用缓存数据
        if _universe_data:
            logger.info(f"使用缓存数据插入 {len(_universe_data)} 条宇宙数据记录...")
            batch_size = 1000
            for i in range(0, len(_universe_data), batch_size):
                batch = _universe_data[i:i + batch_size]
                cursor.executemany(
                    'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security, system_type) VALUES (?, ?, ?, ?, ?)',
                    batch
                )
        else:
            logger.warning("没有找到缓存的宇宙数据")
    
    end_time = time.time()
    logger.info(f"处理universe数据耗时: {end_time - start_time:.2f} 秒") 