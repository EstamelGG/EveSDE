import sqlite3

def process_single_data(type_id, traits_data, language):
    """处理单个物品的traits数据"""
    results = []
    
    # 处理 roleBonuses
    if 'roleBonuses' in traits_data: # role bonuses,船体加成
        for bonus in traits_data['roleBonuses']:
            content = None
            if 'bonusText' in bonus:
                content = bonus['bonusText'].get(language, '')
                if not content:  # 如果当前语言的内容为空，使用英语
                    content = bonus['bonusText'].get('en', '')
                
                if content:  # 只有在有内容的情况下才处理
                    # 如果有bonus和unitID，需要添加到文本前面
                    if 'bonus' in bonus and 'unitID' in bonus:
                        bonus_num = int(bonus['bonus']) if isinstance(bonus['bonus'], int) or bonus[
                            'bonus'].is_integer() else round(bonus['bonus'], 2)
                        if bonus['unitID'] == 105:  # 百分比
                            prefix = f"<b>{bonus_num}%</b> "
                        elif bonus['unitID'] == 104:  # 倍乘
                            prefix = f"<b>{bonus_num}x</b> "
                        elif bonus['unitID'] == 139:  # 加号
                            prefix = f"<b>{bonus_num}+</b> "
                        else:
                            prefix = f"<b>{bonus_num}</b>  "
                        content = prefix + content
                    
                    results.append((type_id, content, None, bonus.get('importance', 999999), "roleBonuses"))
    
    # 处理 typeBonuses
    if 'types' in traits_data: # type bonuses,技能加成
        for skill_id, skill_bonuses in traits_data['types'].items():
            for bonus in skill_bonuses:
                content = None
                if 'bonusText' in bonus:
                    content = bonus['bonusText'].get(language, '')
                    if not content:  # 如果当前语言的内容为空，使用英语
                        content = bonus['bonusText'].get('en', '')
                    
                    if content:  # 只有在有内容的情况下才处理
                        # 如果有bonus和unitID，需要添加到文本前面
                        if 'bonus' in bonus and 'unitID' in bonus:
                            bonus_num = int(bonus['bonus']) if isinstance(bonus['bonus'], int) or bonus[
                                'bonus'].is_integer() else round(bonus['bonus'], 2)
                            if bonus['unitID'] == 105:  # 百分比
                                prefix = f"<b>{bonus_num}%</b> "
                            elif bonus['unitID'] == 104:  # 倍乘
                                prefix = f"<b>{bonus_num}x</b> "
                            elif bonus['unitID'] == 139:  # 加号
                                prefix = f"<b>{bonus_num}+</b> "
                            else:
                                prefix = f"<b>{bonus_num}</b>  "
                            content = prefix + content
                        
                        results.append((type_id, content, skill_id, bonus.get('importance', 999999), "typeBonuses"))
    
    # 处理 miscBonuses
    if 'miscBonuses' in traits_data: # misc bonuses,其他加成
        for bonus in traits_data['miscBonuses']:
            content = None
            if 'bonusText' in bonus:
                content = bonus['bonusText'].get(language, '')
                if not content:  # 如果当前语言的内容为空，使用英语
                    content = bonus['bonusText'].get('en', '')
                
                if content:  # 只有在有内容的情况下才处理
                    # 如果有bonus和unitID，需要添加到文本前面
                    if 'bonus' in bonus and 'unitID' in bonus:
                        bonus_num = int(bonus['bonus']) if isinstance(bonus['bonus'], int) or bonus[
                            'bonus'].is_integer() else round(bonus['bonus'], 2)
                        if bonus['unitID'] == 105:  # 百分比
                            prefix = f"<b>{bonus_num}%</b> "
                        elif bonus['unitID'] == 104:  # 倍乘
                            prefix = f"<b>{bonus_num}x</b> "
                        elif bonus['unitID'] == 139:  # 加号
                            prefix = f"<b>{bonus_num}+</b> "
                        else:
                            prefix = f"<b>{bonus_num}</b>  "
                        content = prefix + content
                    
                    results.append((type_id, content, None, bonus.get('importance', 999999), "miscBonuses"))
    
    # 按importance排序
    return sorted(results, key=lambda x: x[3])

def process_trait_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建traits表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS traits (
        typeid INTEGER NOT NULL,
        importance INTEGER,
        bonus_type TEXT,
        content TEXT NOT NULL,
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
            for type_id, content, skill, importance, bonus_type in traits:
                # 逐个插入
                cursor.execute(
                    'INSERT OR REPLACE INTO traits (typeid, importance, bonus_type, content, skill) VALUES (?, ?, ?, ?, ?)',
                    (type_id, importance, bonus_type, content, skill)
                )