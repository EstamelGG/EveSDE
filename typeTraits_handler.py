import sqlite3

def process_single_data(type_id, traits_data, language):
    """处理单个物品的traits数据"""
    results = []
    
    # 处理roleBonuses
    if 'roleBonuses' in traits_data: # role bonuses,船体加成
        for bonus in traits_data['roleBonuses']:
            if 'bonusText' in bonus and language in bonus['bonusText']:
                content = bonus['bonusText'][language]
                
                # 如果有bonus和unitID，需要添加到文本前面
                if 'bonus' in bonus and 'unitID' in bonus:
                    bonus_num = int(bonus['bonus']) if isinstance(bonus['bonus'], int) or bonus[
                        'bonus'].is_integer() else round(bonus['bonus'], 2)
                    if bonus['unitID'] == 105:  # 百分比
                        prefix = f"{bonus_num}% "
                    elif bonus['unitID'] == 104:  # 倍乘
                        prefix = f"{bonus_num}x "
                    elif bonus['unitID'] == 139:  # 加号
                        prefix = f"{bonus_num}+ "
                    else:
                        prefix = f"{bonus_num} "
                    content = prefix + content
                
                results.append((type_id, content, 'none', bonus.get('importance', 999999)))
    
    # 处理types
    if 'types' in traits_data: # type bonues,技能加成
        for skill_id, skill_bonuses in traits_data['types'].items():
            for bonus in skill_bonuses:
                if 'bonusText' in bonus and language in bonus['bonusText']:
                    content = bonus['bonusText'][language]
                    # 如果有bonus和unitID，需要添加到文本前面
                    if 'bonus' in bonus and 'unitID' in bonus:
                        bonus_num = int(bonus['bonus']) if isinstance(bonus['bonus'], int) or bonus[
                            'bonus'].is_integer() else round(bonus['bonus'], 2)
                        if bonus['unitID'] == 105:  # 百分比
                            prefix = f"{bonus_num}% "
                        elif bonus['unitID'] == 104:  # 倍乘
                            prefix = f"{bonus_num}x "
                        elif bonus['unitID'] == 139:  # 加号
                            prefix = f"{bonus_num}+ "
                        else:
                            prefix = f"{bonus_num} "
                        content = prefix + content
                    
                    results.append((type_id, content, skill_id, bonus.get('importance', 999)))
    
    # 按importance排序
    return sorted(results, key=lambda x: x[3])

def process_trait_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建traits表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS traits (
        typeid INTEGER,
        content TEXT,
        skill INTEGER,
        PRIMARY KEY (typeid, content, skill)
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM traits')

    # 处理每个物品的traits数据
    for type_id, type_data in yaml_data.items():
        if 'traits' in type_data:
            traits = process_single_data(type_id, type_data['traits'], language)
            for type_id, content, skill, _ in traits:
                # 逐个插入
                cursor.execute(
                    'INSERT OR REPLACE INTO traits (typeid, content, skill) VALUES (?, ?, ?)',
                    (type_id, content, skill)
                )