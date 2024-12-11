# EVE SDE 数据库构造器

1. 获取官方数据库：https://developers.eveonline.com/resource
2. 解压后放在 `Data/sde`
2. 从第三方来源获取数据单位信息，如"%","+"等：https://sde.hoboleaks.space/tq/dogmaunits.json 下载后放在 `thirdparty_data_source`
3. 开始构造数据库 `main.py`

# 更新图标

1. 如果需要更新图标，则单独执行 `thirdparty_data_source/sync_icon.py`
2. 下载好图标后，执行 `thirdparty_data_source/replace_icon.py` 与 `Data/Types` 合并

# 制作app图标

1. 做一个 png 图标，然后在预览中导出，选择png格式，并选择去除alpha通道
2. 访问 https://makeappicon.com/ 制作各种尺寸的图标