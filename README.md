# EVE SDE 数据库构造器

1. 获取官方数据库：https://developers.eveonline.com/resource
2. 解压后放在 `Data/sde`
2. 从第三方来源获取数据单位信息，如"%","+"等：https://sde.hoboleaks.space/tq/dogmaunits.json 下载后放在 `thirdparty_data_source`
3. 从第三方来源构造行星开发原始资源的采集星球：执行 `thirdparty_data_source/get_PI_source.py`
4. 开始构造数据库 `main.py`