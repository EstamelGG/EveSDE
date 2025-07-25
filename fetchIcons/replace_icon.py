import os
import shutil
import time
from PIL import Image


def get_file_size(image_path):
    """获取图片文件的尺寸（字节数）"""
    return os.path.getsize(image_path)


def clear_directory(path):
    if not os.path.isdir(path):
        print(f"路径无效或不是目录: {path}")
        return

    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # 删除文件或符号链接
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 删除目录及其内容
        except Exception as e:
            print(f"删除失败: {item_path} - 错误: {e}")
    print(f"已清空目录: {path}")
    time.sleep(3)


def copy_icon_batch():
    """从fetchIcons/icon_fix目录复制修正过的图标到Data/Types目录

    这些图片是已知某些typeid对应的图片存在错误，因此通过手动修正后放在icon_fix目录中
    复制到Data/Types目录后，就能确保在处理时使用正确的图片

    同时处理一些特殊情况：某些图片需要复制为多个不同type_id的文件
    """

    source_dir = "./icon_fix"
    target_dir = "../Data/Types"

    # 有些物品，如无人机，其衍生等级相同，但均使用了错误的图标
    # 定义特殊文件映射字典: key为源文件名，value为需要复制成的type_id列表
    # SELECT t.type_id, t.name, t.metaGroupID, t.icon_filename FROM types AS t JOIN (SELECT icon_filename, categoryID, metaGroupID FROM types WHERE type_id = 12200) AS ref ON t.icon_filename = ref.icon_filename AND t.categoryID = ref.categoryID AND t.metaGroupID = ref.metaGroupID
    # 可以这样查询到，由于只有部分物品存在此问题，因此暂时使用硬编码。
    special_file_mapping = {
        '2173': [2173, 23702, 23709, 23725],  # 渗透者 I
        '2174': [2174, 23703, 23710, 23726],  # 渗透者 I
        '2183': [2183,23713,33704],  # 战锤 I
        '2184': [2184,23714,33705],  # 战锤 I
        '2193': [2193, 22572, 23510, 23523],  # 执政官 I
        '2194': [2194, 22573, 23511, 23524],  # 执政官 I
        '2203': [2203, 3549, 17565, 22574, 22713, 23659, 23711, 23727],  # 侍僧 I
        '2204': [2204, 23660, 23712, 23728],  # 侍僧 I
        '2464': [2464, 23707, 23719],  # 大黄蜂 I
        '2454': [2454,23715,32465,33706],  # 地精灵 I
        '2455': [2455,23716,33707],  # 地精灵 I
        '2444': [2444,16206,22780,23506,33671],  # 蛮妖 I
        '2445': [2445,22781,23507,33672],  # 蛮妖 I
        '2465': [2465, 23708, 23720],  # 大黄蜂 I
        '15508': [15508, 23705, 23717],  # 金星 I
        '15509': [15509, 23706, 23718],  # 金星 I
        '2446': [2446, 33708],  # 蛮妖 II
        '2175': [2175, 28205],  # 渗透者 II
        '2476': [2476],  # 狂战士 I
        '2477': [2477],  # 狂战士 I
        '15510': [15510, 23721, 23729],  # 瓦尔基里 I
        '15511': [15511, 23722, 23730],  # 瓦尔基里 I
        '2486': [2486, 23723, 23731],  # 武士 I
        '2487': [2487, 23724, 23732],  # 武士 I
        '40553': [40553, 40559, 40571],  # 因赫吉 II
        '41386': [41374, 41384, 41386],  # 因赫吉 II
        '40570': [40555, 40558, 40570],  # 萨梯 II
        '41372': [41372, 41381, 41383],  # 萨梯 II
        '40569': [40554, 40557, 40569],  # 蚱蜢 II
        '41370': [41370, 41378, 41380],  # 蚱蜢 II
        '40568': [40552, 40556, 40568],  # 圣殿骑士 II
        '41368': [41368, 41375, 41377],  # 圣殿骑士 II
        '40560': [40560, 40561],  # 阿米特 II
        '41356': [41356, 41352],  # 阿米特 II
        '40562': [40562, 40563],  # 独眼巨人 II
        '41351': [41351, 41364],  # 独眼巨人 II
        '40566': [40566, 40567],  # 白蚁 II
        '40362': [32340,40362,45673,45675,47124,47116],  # 槌骨 I
        '40364': [32325,40364,47126,47117],  # 独眼巨人 I
        '41363': [32326,41363,47245,47237,47233],  # 独眼巨人 I BPO
        '41355': [32341,41355,47234,47241],  # 槌骨 I
        '41362': [41362, 41353],  # 白蚁 II
        '41361': [41361, 32345, 47236, 47243],  # 白蚁 I BPO
        '40565': [40564, 40565],  # 斩裂剑 II
        '41354': [41354, 41366],  # 斩裂剑 II
        '47036': [47036, 47133, 47140],  # 屹立德洛米 I
        '47211': [47211, 47222, 47230],  # 屹立德洛米 I
        '47145': [47035, 47131, 47145],  # 屹立修道士 I
        '47213': [47208, 47213, 47224],  # 屹立修道士 I
        '47138': [47132, 47138, 47146],  # 屹立圣甲虫 I
        '47209': [47209, 47216, 47226],  # 屹立圣甲虫 I
        '47147': [47037, 47139, 47147],  # 屹立掷矛手 I
        '47219': [47210, 47219, 47228],  # 屹立掷矛手 I
        '47151': [47137, 47144, 47151],  # 屹立德洛米 II
        '47223': [47221, 47223, 47231],  # 屹立德洛米 II
        '47148': [47134, 47141, 47148],  # 屹立圣殿骑士 II
        '47214': [47212, 47214, 47225],  # 屹立圣殿骑士 II
        '47142': [47135, 47142, 47149],  # 屹立蜻蜓 II
        '47215': [47215, 47217, 47227],  # 屹立蜻蜓 II
        '47150': [47136, 47143, 47150],  # 屹立掷矛手 II
        '47220': [47218, 47220, 47229],  # 屹立掷矛手 II
        '28270': [28270, 28272],  # 集成型战锤
        '28271': [28271, 28273],  # 集成型战锤
        '28274': [28274, 28276],  # 集成型地精灵
        '28275': [28275, 28277],  # 集成型地精灵
        '28286': [28286, 28288],  # 集成型蛮妖
        '28287': [28287, 28289],  # 集成型蛮妖
        '28278': [28278, 28280],  # 集成型大黄蜂
        '28279': [28279, 28281],  # 集成型大黄蜂
        '28306': [28306, 28308],  # 集成型胡蜂
        '28307': [28307, 28309],  # 集成型胡蜂
        '28298': [28298, 28300],  # 集成型金星
        '28299': [28299, 28301],  # 集成型金星
        '28282': [28282, 28284],  # 集成型渗透者
        '28283': [28283, 28285],  # 集成型渗透者
        '28262': [28262, 28264],  # 集成型侍僧
        '28263': [28263, 28265],  # 集成型侍僧
        '28302': [28302, 28304],  # 集成型武士
        '28303': [28303, 28305],  # 集成型武士
        '28290': [28290, 28292],  # 集成型执政官
        '28291': [28291, 28293],  # 集成型执政官
        '47127': [47127, 47119],  # 屹立槌骨 II
        '47242': [47242, 47238],  # 屹立槌骨 II
        '47129': [47129, 47121],  # 屹立独眼巨人 II
        '47246': [47237, 47246],  # 屹立独眼巨人 II
        '47128': [47128, 47120],  # 屹立螳螂 II
        '47244': [47244, 47239],  # 屹立螳螂 II
        '47122': [47122, 47130],  # 屹立斩裂剑 II
        '47240': [47240, 47248],  # 屹立斩裂剑 II
        '32342': [32342, 40365, 47118, 47039],  # 斩裂剑 I
        '32343': [32343, 41365, 47235, 47247],  # 斩裂剑 I

        '12200': [4386, 12198, 12199, 12200],  # 大型机动跃迁扰断器 I
        '12301': [12297, 12300, 12301],  # 大型机动跃迁扰断器 I
        '26888': [26888, 26890, 26892],  # 大型机动跃迁扰断器 II
        '26889': [26889, 26891, 26893],  # 大型机动跃迁扰断器 II
        '27560': [27560, 27562, 27638, 27640, 27641, 27643],  # 古斯塔斯超大型鱼雷发射台
        '27557': [27542, 27544, 27545, 27547, 27548, 27550, 27551, 27553, 27554, 27556, 27557, 27559, 27766, 27767, 27772, 27773],  # 血袭者大型脉冲激光炮台
        '16689': [16689, 16692, 16694, 16867, 17402, 17406, 17770],  # 大型火炮塔台
        '2805': [2803, 2804, 2805, 2807, 2829, 2830],  # 大型火炮塔台
        '16631': [16631, 16688, 17771, 17772],  # 小型火炮塔台
        '2816': [2810, 2814, 2816, 2819],  # 小型火炮塔台
        '17167': [17167, 17168, 17407, 17408],  # 小型集束激光炮台
        '2826': [2825, 2826, 2827, 2828],  # 小型集束激光炮台
        '27583': [27570, 27573, 27574, 27576, 27577, 27579, 27580, 27582, 27583, 27585, 27778, 27779, 27855, 27856, 27857, 27858],  # 天使停滞缠绕光束发射台
        '27565': [27563, 27565, 27567, 27569],  # 天蛇跃迁扰断波发射台
        '16690': [16690, 16691, 17403, 17404],  # 小型磁轨炮台
        '2815': [2806, 2808, 2813, 2815],  # 小型磁轨炮台
        '17773': [16222,16695,16696,16697,17188,17773],  # 轻型导弹发射台
        '2823': [2822,2823,2824],  # 轻型导弹发射台
        '27945': [27944,27945,27946,27947,27948,27949],  # 古斯塔斯超大型鱼雷发射塔蓝图
        '2796': [2741,2763,2788,2792,2794,2796,2798,2799],  # 停滞网状光束发射台蓝图

        # 增效剂修复
        '10151': [10151],
        '10152': [10152],
        '10155': [10155],
        '10156': [10156],
        '10164': [10164],
        '10165': [10165],
        '10166': [10166],
        '15457': [15457],
        '15458': [15458],
        '15459': [15459],
        '15460': [15460],
        '15461': [15461],
        '15462': [15462],
        '15463': [15463],
        '15464': [15464],
        '15465': [15465],
        '15466': [15466],
        '15477': [15477],
        '15478': [15478],
        '15479': [15479],
        '15480': [15480],
        '25344': [25344],
        '25349': [25349],
        '28670': [28670],
        '28672': [28672],
        '28674': [28674],
        '28676': [28676],
        '28678': [28678],
        '28680': [28680],
        '28682': [28682],
        '28684': [28684],
        '9947': [9947],
        '9950': [9950],

        # 可以根据需要添加更多映射
    }

    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"警告：{source_dir}目录不存在，跳过图标批量复制")
        return

    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 复制普通文件
    copy_count = 0
    for item_id in special_file_mapping.keys():
        # 检查是否是特殊映射文件
        file_name = f"{item_id}_64.png"
        source_path = os.path.join(source_dir, file_name)
        if os.path.exists(source_path):
            # 为每个指定的type_id创建一个复制
            for type_id in special_file_mapping[item_id]:
                target_file_name = f"{type_id}_64.png"
                target_path = os.path.join(target_dir, target_file_name)
                shutil.copy2(source_path, target_path)
                copy_count += 1
        else:
            print(f"找不到源文件: {source_path}")

    print(f"\n已从{source_dir}复制{copy_count}个修正图标到{target_dir}")

def copy_icons_from_source(source_dir):
    """从指定源目录复制图标到Data/Types目录"""
    target_dir = "../Data/Types"

    # 确保目标目录存在
    if os.path.exists(target_dir):
        clear_directory(target_dir)
    else:
        os.makedirs(target_dir, exist_ok=True)

    # 获取源目录中的所有文件
    if not os.path.exists(source_dir):
        print(f"源目录 {source_dir} 不存在！")
        return

    files = os.listdir(source_dir)
    total_files = len(files)
    copied = 0
    replaced = 0

    print(f"开始从 {source_dir} 处理 {total_files} 个文件...")

    for i, filename in enumerate(files, 1):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        if i % 1000 == 0:
            print(f"处理第 {i}/{total_files} 个文件: {filename}", end='')
            print()
        # 如果目标文件不存在，直接复制
        if not os.path.exists(target_path):
            shutil.copy2(source_path, target_path)
            copied += 1
            continue
        shutil.copy2(source_path, target_path)
        source_size = get_file_size(source_path)
        target_size = get_file_size(target_path)
        print(f" - 已替换 (新文件: {source_size}字节, 原文件: {target_size}字节)")
        replaced += 1

    print("\n处理完成！")
    print(f"新复制: {copied} 个文件")
    print(f"已替换: {replaced} 个文件")

def copy_icons():
    """使用默认源目录复制图标（保持向后兼容）"""
    copy_icons_from_source("icon_from_api")


if __name__ == "__main__":
    copy_icons()
    copy_icon_batch()