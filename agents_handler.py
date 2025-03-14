import yaml
import time
import os

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def read_agents_yaml(file_path):
    """读取agents.yaml文件"""
    return read_yaml(file_path)

def read_agents_in_space_yaml(file_path):
    """读取agentsInSpace.yaml文件"""
    return read_yaml(file_path)

def process_agents_data(agents_data, agents_in_space_data, cursor, language=None):
    """处理代理数据并写入数据库"""
    # 创建agents表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agents (
        agent_id INTEGER NOT NULL PRIMARY KEY,
        agent_type INTEGER,
        corporationID INTEGER,
        divisionID INTEGER,
        isLocator INTEGER,
        level INTEGER,
        locationID INTEGER,
        solarSystemID INTEGER
    )
    ''')
    
    # 创建索引以优化查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_solarSystemID ON agents(solarSystemID)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_locationID ON agents(locationID)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_agents_corporationID ON agents(corporationID)')
    
    # 清空现有数据
    cursor.execute('DELETE FROM agents')
    
    # 首先，从agentsInSpace.yaml中提取所有代理的太阳系ID
    agents_solar_systems = {}
    for agent_id, agent_data in agents_in_space_data.items():
        agents_solar_systems[agent_id] = agent_data.get('solarSystemID')
    
    # 处理每个代理
    for agent_id, agent_data in agents_data.items():
        # 获取代理数据
        agent_type = agent_data.get('agentTypeID')
        corporation_id = agent_data.get('corporationID')
        division_id = agent_data.get('divisionID')
        is_locator = 1 if agent_data.get('isLocator', False) else 0
        level = agent_data.get('level')
        location_id = agent_data.get('locationID')
        
        # 如果代理在太空中，获取其太阳系ID，否则为NULL
        solar_system_id = agents_solar_systems.get(agent_id)
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO agents 
            (agent_id, agent_type, corporationID, divisionID, isLocator, level, locationID, solarSystemID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            agent_id, 
            agent_type,
            corporation_id,
            division_id,
            is_locator,
            level,
            location_id,
            solar_system_id
        )) 