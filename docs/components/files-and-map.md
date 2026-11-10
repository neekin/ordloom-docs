# 文件、视频与地图

## 图片与文件

普通 `ImageField` 与 `FileField` 可直接接入：

```python
from django.db import models

cover = models.ImageField("封面", upload_to="projects/covers/", blank=True)
attachment = models.FileField("附件", upload_to="projects/files/", blank=True)
```

上传先写入实际字段的 storage 与 upload_to，再将返回地址交给表单保存。上传、回填及再次保存会处理存储名、URL 编码、绝对/CDN 地址和签名查询。

| 项目 | 默认 / 配置 |
| --- | --- |
| 图片大小 | 默认 10 MB，字段可配置 |
| 普通文件大小 | 默认 50 MB，字段可配置 |
| 服务端总上限 | `ORDLOOM_MAX_UPLOAD_SIZE_MB`，默认 50 MB |
| 编辑器图片 | 默认上限 10 MB，检查所属字段与主从记录 |
| 格式提示 | `accept`，例如 `.pdf,.txt` |

图片支持 PNG、JPEG、GIF、WebP、AVIF、BMP 等常见位图，服务端验证实际内容而非只相信扩展名。只读或无写入权限的记录不能上传。

上传独立于数据库事务。取消表单不会自动删除已上传文件；项目可按自己的业务引用关系设计清理任务。

## 视频

`VideoField` 存储视频 URL，界面提供地址输入与浏览器播放器。它不是视频转码或托管服务；实际可播放的格式由浏览器和资源服务决定。

## 地图

`MapField` 保存 `经度,纬度` 字符串，例如 `120.155100,30.274100`。可以点击地图、拖动标记或填写坐标。

```python
ordloom_fields = {
    "position": {
        "tile_url": "/tiles/{z}/{x}/{y}.png",
        "tile_attribution": "项目地图服务",
    }
}
```

默认使用 Leaflet 与 OpenStreetMap 瓦片；也可使用项目自己的合规底图。底图不可达时仍可输入坐标。当前功能是坐标选择，不提供 POI 搜索。

核心静态资源随发行包提供，不代表所有业务图片、视频和地图瓦片都能离线使用。
