try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import yaml
import time

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_tables(cursor):
    """创建必要的数据表"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invNames (
        itemID INTEGER NOT NULL PRIMARY KEY,
        itemName TEXT
    )
    ''')

def process_data(data, cursor, lang):
    """处理invNames数据并插入数据库
    
    Args:
        data: 从YAML文件读取的数据
        cursor: 数据库游标
        lang: 语言代码
    """
    # 创建表
    create_tables(cursor)
    
    # 清空现有数据
    cursor.execute('DELETE FROM invNames')
    
    # 用于批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    try:
        for item in data:
            itemID = item.get('itemID')
            itemName = item.get('itemName')

            # 添加到批处理列表
            batch_data.append((
                itemID, itemName
            ))
            
            # 当达到批处理大小时执行插入
            if len(batch_data) >= batch_size:
                cursor.executemany('''
                    INSERT OR REPLACE INTO invNames (
                        itemID, itemName
                    ) VALUES (?, ?)
                ''', batch_data)
                batch_data = []  # 清空批处理列表
        
        # 处理剩余的数据
        if batch_data:
            cursor.executemany('''
                INSERT OR REPLACE INTO invNames (
                    itemID, itemName
                ) VALUES (?, ?)
            ''', batch_data)
            
    except Exception as e:
        print(f"处理invNames数据时出错: {str(e)}")
        raise 