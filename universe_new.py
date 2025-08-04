import json
import time
import logging
import re
import os
from typing import List, Tuple, Set

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 用于缓存universe数据
_universe_data: List[Tuple] = []

planetary_typeIdMapping = {
    "temperate": 11,
    "barren": 2016,
    "oceanic": 2014,
    "ice": 12,
    "gas": 13,
    "lava": 2015,
    "storm": 2017,
    "plasma": 2063
}

def read_jove_systems(file_path: str = 'thirdparty_data_source/jo.txt') -> Set[str]:
    """读取jo.txt文件，返回Jove星系名称集合"""
    jove_systems = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line and line_num > 1:  # 跳过标题行
                    parts = line.split(',')
                    if len(parts) >= 2:
                        system_name = parts[1].strip()
                        jove_systems.add(system_name)
        logger.info(f"从 {file_path} 读取了 {len(jove_systems)} 个Jove星系")
        return jove_systems
    except FileNotFoundError:
        logger.warning(f"文件 {file_path} 不存在，将不会标记Jove星系")
        return set()
    except Exception as e:
        logger.error(f"读取 {file_path} 时出错: {str(e)}")
        return set()

def create_table(cursor):
    """创建universe表和starmap表"""
    # 使用硬编码的行星类型列名
    table_schema = '''
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
            jove BOOLEAN NOT NULL DEFAULT 0
    '''
    
    # 添加硬编码的行星类型列
    for planet_name in planetary_typeIdMapping.keys():
        table_schema += f',\n            {planet_name} INTEGER NOT NULL DEFAULT 0'
    
    # 添加主键约束
    table_schema += ''',
            PRIMARY KEY (region_id, constellation_id, solarsystem_id)
        )
    '''
    
    # 执行创建表语句
    cursor.execute(table_schema)
    logger.info(f"创建了包含 {len(planetary_typeIdMapping)} 种行星类型和jove列的表结构")
    
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

def process_universe_data(data: dict, cursor=None, jove_systems: Set[str] = None) -> List[Tuple]:
    """处理universe数据"""
    universe_data = []
    neighbour_count = 0
    
    # 编译JSpace正则表达式
    jspace_pattern = re.compile(r'^J\d+$')
    
    # 创建行星类型ID到名称的反向映射
    planet_type_to_name = {type_id: name for name, type_id in planetary_typeIdMapping.items()}
    
    # 用于收集邻居星系数据
    neighbours_data = {}
    
    # 如果没有提供jove_systems，则读取jo.txt文件
    if jove_systems is None:
        jove_systems = read_jove_systems()
    
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
                
                # 处理行星数据
                planets = sys_info.get('system_info', {}).get('planets', {})
                # 初始化所有行星类型的计数为0
                planet_counts = {name: 0 for name in planetary_typeIdMapping.keys()}
                
                if isinstance(planets, dict):
                    # 如果planets已经是按类型组织的字典
                    for type_key, planet_list in planets.items():
                        if type_key.startswith('type_'):
                            try:
                                planet_type = int(type_key.split('_')[1])
                                # 只统计在planetary_typeIdMapping中定义的行星类型
                                if planet_type in planet_type_to_name:
                                    planet_name = planet_type_to_name[planet_type]
                                    planet_counts[planet_name] = len(planet_list) if isinstance(planet_list, list) else 0
                            except (ValueError, IndexError):
                                logger.warning(f"无法解析行星类型: {type_key}")
                elif isinstance(planets, list):
                    # 如果planets是列表，按类型计数
                    for planet in planets:
                        if isinstance(planet, dict) and 'type_id' in planet:
                            planet_type = planet['type_id']
                            # 只统计在planetary_typeIdMapping中定义的行星类型
                            if planet_type in planet_type_to_name:
                                planet_name = planet_type_to_name[planet_type]
                                planet_counts[planet_name] += 1
                
                # 检查是否为Jove星系
                is_jove = system_name in jove_systems
                
                # 构建数据元组
                data_tuple = [
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
                    is_jspace,
                    is_jove
                ]
                
                # 添加行星类型计数，按照planetary_typeIdMapping的顺序
                for planet_name in planetary_typeIdMapping.keys():
                    data_tuple.append(planet_counts.get(planet_name, 0))
                
                universe_data.append(tuple(data_tuple))
                
                # 处理邻居星系
                system_info = sys_info.get('system_info', {})
                if 'neighbours' in system_info:
                    neighbours = system_info['neighbours']
                    if neighbours:
                        # 将邻居星系ID添加到字典中
                        neighbours_data[str(sys_id)] = [int(neighbour) for neighbour in neighbours]
                        neighbour_count += len(neighbours)
    
    # 如果提供了cursor，执行批量插入
    if cursor and universe_data:
        # 构建动态SQL语句
        placeholders = ', '.join(['?' for _ in range(len(universe_data[0]))])
        columns = [
            'region_id', 'constellation_id', 'solarsystem_id', 
            'system_security', 'system_type', 'x', 'y', 'z', 
            'hasStation', 'hasJumpGate', 'isJSpace', 'jove'
        ]
        
        # 添加行星类型列，按照planetary_typeIdMapping的顺序
        for planet_name in planetary_typeIdMapping.keys():
            columns.append(planet_name)
        
        columns_str = ', '.join(columns)
        sql = f'INSERT OR REPLACE INTO universe ({columns_str}) VALUES ({placeholders})'
        
        batch_size = 1000
        for i in range(0, len(universe_data), batch_size):
            batch = universe_data[i:i + batch_size]
            cursor.executemany(sql, batch)
            logger.debug(f"已插入 {i + len(batch)}/{len(universe_data)} 条记录")
    
    # 保存邻居星系数据到JSON文件
    if neighbours_data:
        save_neighbours_to_json(neighbours_data)
    
    logger.info(f"已处理 {neighbour_count} 条邻居星系关系")
    return universe_data

def save_neighbours_to_json(neighbours_data: dict, output_file: str = 'output/db/neighbours_data.json'):
    """将邻居星系数据保存为JSON文件"""
    # 检查文件是否已存在
    if os.path.exists(output_file):
        logger.info(f"邻居星系数据文件 {output_file} 已存在，跳过保存")
        return
        
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(neighbours_data, file, indent=2)
        logger.info(f"邻居星系数据已保存到 {output_file}")
    except Exception as e:
        logger.error(f"保存邻居星系数据失败: {str(e)}")

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
            
            # 构建动态SQL语句
            if _universe_data:
                placeholders = ', '.join(['?' for _ in range(len(_universe_data[0]))])
                
                # 构建列名
                columns = [
                    'region_id', 'constellation_id', 'solarsystem_id', 
                    'system_security', 'system_type', 'x', 'y', 'z', 
                    'hasStation', 'hasJumpGate', 'isJSpace', 'jove'
                ]
                
                # 添加行星类型列，按照planetary_typeIdMapping的顺序
                for planet_name in planetary_typeIdMapping.keys():
                    columns.append(planet_name)
                
                columns_str = ', '.join(columns)
                sql = f'INSERT OR REPLACE INTO universe ({columns_str}) VALUES ({placeholders})'
                
                # 批量插入数据
                batch_size = 1000
                for i in range(0, len(_universe_data), batch_size):
                    batch = _universe_data[i:i + batch_size]
                    cursor.executemany(sql, batch)
                    logger.debug(f"已插入 {i + len(batch)}/{len(_universe_data)} 条记录")
            else:
                logger.warning("没有找到有效的宇宙数据记录")
            
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