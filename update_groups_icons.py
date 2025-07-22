import sqlite3

def update_groups_with_icon_filename(cursor):
    """根据 group_id 从 types 表获取 icon_filename，并更新 groups 表"""
    # 使用单个JOIN查询获取所有需要的数据
    cursor.execute('''
        WITH RankedIcons AS (
            SELECT 
                t.groupID,
                t.icon_filename,
                ROW_NUMBER() OVER (
                    PARTITION BY t.groupID 
                    ORDER BY 
                        CASE WHEN t.published = 1 THEN 0 ELSE 1 END,  -- 优先已发布
                        t.metaGroupID                                -- 然后按 metaGroupID 升序
                ) AS rn
            FROM types t
            WHERE t.icon_filename NOT IN ("items_73_16_50.png", "items_7_64_15.png", "icon_0_64.png")
        )
        UPDATE groups
        SET icon_filename = COALESCE(
            (SELECT icon_filename 
             FROM RankedIcons 
             WHERE groupID = groups.group_id AND rn = 1),
            "items_73_16_50.png"
        );
    ''')

