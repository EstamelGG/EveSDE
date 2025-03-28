import json
import time
import logging
import re
from typing import List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 用于缓存universe数据
_universe_data: List[Tuple[int, int, int, float, int, float, float, float, bool, bool, bool]] = []

def create_table(cursor):
    """创建universe表和starmap表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universe (
            region_id INTEGER NOT NULL,
            constellation_id INTEGER NOT NULL,
            solarsystem_id INTEGER NOT NULL,
            system_security REAL,
            system_type INTEGER,
            x REAL,
            y REAL,
            z REAL,
            hasStation BOOLEAN NOT NULL DEFAULT 0,
            hasJumpGate BOOLEAN NOT NULL DEFAULT 0,
            isJSpace BOOLEAN NOT NULL DEFAULT 0,
            PRIMARY KEY (region_id, constellation_id, solarsystem_id)
        )
    ''')
    
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS starmap (
    #         system_id INTEGER NOT NULL,
    #         neighbour INTEGER NOT NULL,
    #         PRIMARY KEY (system_id, neighbour)
    #     )
    # ''')

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

def process_universe_data(data: dict, cursor=None) -> List[Tuple[int, int, int, float, int, float, float, float, bool, bool, bool]]:
    """处理universe数据"""
    universe_data = []
    neighbour_count = 0
    
    # 编译JSpace正则表达式
    jspace_pattern = re.compile(r'^J\d+$')
    
    # 遍历所有星域
    for region_id, region_info in data.items():
        # 遍历星域下的所有星座
        for const_id, const_info in region_info.get('constellations', {}).items():
            # 遍历星座下的所有恒星系
            for sys_id, sys_info in const_info.get('systems', {}).items():
                # 获取安全等级
                security_status = sys_info.get('system_info', {}).get('security_status', 0.0)
                # 默认恒星类型为6（标准黄色恒星）
                system_type = sys_info.get('system_info', {}).get('solar_type_id', 6)
                
                # 获取坐标
                position = sys_info.get('system_info', {}).get('position', {})
                x = position.get('x', 0.0)
                y = position.get('y', 0.0)
                z = position.get('z', 0.0)
                
                # 检查是否有空间站
                stations = sys_info.get('system_info', {}).get('stations', [])
                has_station = isinstance(stations, list) and len(stations) > 0
                
                # 检查是否有星门
                jump_gates = sys_info.get('system_info', {}).get('stargates', [])
                has_stargates = isinstance(jump_gates, list) and len(jump_gates) > 0
                
                # 检查是否为JSpace
                system_name = sys_info.get('system_name', {}).get('en', '')
                is_jspace = bool(jspace_pattern.match(system_name) or system_name == "J1226-0") and not has_stargates
                
                # 将数据添加到列表
                universe_data.append((
                    int(region_id),
                    int(const_id),
                    int(sys_id),
                    float(security_status),
                    system_type,
                    float(x),
                    float(y),
                    float(z),
                    has_station,
                    has_stargates,
                    is_jspace
                ))
                
                # 处理邻居星系
                # system_info = sys_info.get('system_info', {})
                # if cursor and 'neighbours' in system_info:
                #     neighbours = system_info['neighbours']
                #     for neighbour in neighbours:
                #         try:
                #             cursor.execute(
                #                 'INSERT OR REPLACE INTO starmap (system_id, neighbour) VALUES (?, ?)',
                #                 (int(sys_id), int(neighbour))
                #             )
                #             neighbour_count += 1
                #         except Exception as e:
                #             logger.error(f"插入邻居星系数据失败: system_id={sys_id}, neighbour={neighbour}, error={str(e)}")
                #
    # 如果提供了cursor，执行批量插入
    if cursor and universe_data:
        batch_size = 1000
        for i in range(0, len(universe_data), batch_size):
            batch = universe_data[i:i + batch_size]
            cursor.executemany(
                'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security, system_type, x, y, z, hasStation, hasJumpGate, isJSpace) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                batch
            )
            logger.debug(f"已插入 {i + len(batch)}/{len(universe_data)} 条记录")
    
    logger.info(f"已处理 {neighbour_count} 条邻居星系关系")
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
                    'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security, system_type, x, y, z, hasStation, hasJumpGate, isJSpace) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    batch
                )
            
            # 重新读取数据以处理starmap
            data = read_universe_data()
            if data:
                process_universe_data(data, cursor)
            else:
                logger.error("无法读取universe数据用于处理starmap")
        else:
            logger.warning("没有找到缓存的宇宙数据")
    
    end_time = time.time()
    logger.info(f"处理universe数据耗时: {end_time - start_time:.2f} 秒") 