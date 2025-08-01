
world_map_layout = "https://evemaps.dotlan.net/svg/New_Eden.svg"


"""
调整脚本，我们计划做一个地图生成器
首先，我们有一个全局地图：world_map_layout
我们首先需要请求其内容

为了方便后续设计，我把下载好的内容放在本地了
然后我们需要做这几件事
1. 我们将此New_Eden.svg下载到 maps 目录，然后根据此svg内容，获取所有href，找到所有格式为：http://evemaps.dotlan.net/map/xxx 的星域地图链接，同时获取其星域名
2. 使用30个并发获取所有星域地图svg放在maps目录
3. 根据New_Eden.svg的内容，再获取所有星域的中心坐标<g id="sysuse">和连线关系（<g id="jumps"><line id="j-10000001-10000001"）
4. 获取到所有星域名称后，我们做一些格式化：将星域名的下划线删除，以便在 Data/sde/universe/eve 目录找到对应的星域的region.yaml文件
5. 将上述内容输出到json文件，我希望记录各星域id，坐标，连接关系，势力id（没有则写0）
"""