def process_skill_requirements(cursor, language):
    """处理物品的技能需求并写入数据库"""
    # 创建技能需求表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS typeSkillRequirement (
        typeid INTEGER,
        typename TEXT,
        typeicon TEXT,
        groupid INTEGER,
        groupname TEXT,
        required_skill_id INTEGER,
        required_skill_level INTEGER,
        PRIMARY KEY (typeid, required_skill_id)
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM typeSkillRequirement')
    
    # 技能需求的属性ID映射
    skill_requirements = [
        (182, 277),   # 主技能
        (183, 278),   # 副技能
        (184, 279),   # 三级技能
        (1285, 1286), # 四级技能
        (1289, 1287), # 五级技能
        (1290, 1288)  # 六级技能
    ]
    
    # 获取所有categoryID=16的物品（技能）
    cursor.execute('''
        SELECT type_id, name, icon_filename, groupID, group_name 
        FROM types 
    ''')
    items = cursor.fetchall()
    
    # 处理每个物品的技能需求
    for item in items:
        type_id, type_name, type_icon, group_id, group_name = item
        
        # 检查每个可能的技能需求
        for skill_attr_id, level_attr_id in skill_requirements:
            # 查找技能ID
            cursor.execute('''
                SELECT value 
                FROM typeAttributes 
                WHERE type_id = ? AND attribute_id = ?
            ''', (type_id, skill_attr_id))
            skill_result = cursor.fetchone()
            
            if skill_result:
                required_skill_id = int(float(skill_result[0]))
                
                # 查找需要的等级
                cursor.execute('''
                    SELECT value 
                    FROM typeAttributes 
                    WHERE type_id = ? AND attribute_id = ?
                ''', (type_id, level_attr_id))
                level_result = cursor.fetchone()
                
                if level_result:
                    required_level = int(float(level_result[0]))
                    
                    # 插入数据
                    cursor.execute('''
                        INSERT OR REPLACE INTO typeSkillRequirement 
                        (typeid, typename, typeicon, groupid, groupname, required_skill_id, required_skill_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (type_id, type_name, type_icon, group_id, group_name, required_skill_id, required_level)) 