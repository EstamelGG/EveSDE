import yaml
import time

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_tables(cursor):
    """创建必要的数据表"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invFlags (
        flagID INTEGER NOT NULL PRIMARY KEY,
        flagName TEXT,
        flagText TEXT,
        orderID INTEGER
    )
    ''')

def process_data(data, cursor, lang):
    """处理invFlags数据并插入数据库"""
    create_tables(cursor)
    
    # 清空现有数据
    cursor.execute('DELETE FROM invFlags')
    
    # 用于批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for flag in data:
        flagID = flag.get('flagID')
        flagName = flag.get('flagName')
        flagText = flag.get('flagText')
        orderID = flag.get('orderID')
        
        # 添加到批处理列表
        batch_data.append((
            flagID, flagName, flagText, orderID
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO invFlags (
                    flagID, flagName, flagText, orderID
                ) VALUES (?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO invFlags (
                flagID, flagName, flagText, orderID
            ) VALUES (?, ?, ?, ?)
        ''', batch_data) 