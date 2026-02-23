# creators/tag_choices.py
# 预设标签常量定义文件

# 标签分类常量
CATEGORY_SCENE = 'scene'       # 拍摄场景
CATEGORY_SKILL = 'skill'       # 设备与技能
CATEGORY_SPECIAL = 'special'   # 特别需求
CATEGORY_POST = 'post'         # 后期服务

# 标签列表
# 每个元素格式: (id, name, category)
# 分类ID范围:
#   scene    : 1~99
#   skill    : 101~199
#   special  : 201~299
#   post     : 301~399

TAGS = [
    # ========== 拍摄场景（必选，需求方只能选一项，创作者可多选） ==========
    (1, '毕业照', CATEGORY_SCENE),
    (2, '情侣写真', CATEGORY_SCENE),
    (3, '个人写真', CATEGORY_SCENE),
    (4, '友谊纪念照', CATEGORY_SCENE),
    (5, '社团活动', CATEGORY_SCENE),
    (6, '班级合影', CATEGORY_SCENE),
    (7, '演出跟拍', CATEGORY_SCENE),
    (8, '证件照', CATEGORY_SCENE),
    (9, '生活照', CATEGORY_SCENE),
    # 预留后续扩展场景标签 ID 10~99

    # ========== 设备与技能（双方必选，可多选） ==========
    (101, '无人机航拍', CATEGORY_SKILL),
    (102, '拍立得', CATEGORY_SKILL),
    (103, '胶片相机', CATEGORY_SKILL),
    (104, 'ccd相机', CATEGORY_SKILL),
    (105, '单反', CATEGORY_SKILL),
    (106, '微单', CATEGORY_SKILL),
    (107, '运动相机', CATEGORY_SKILL),
    # 注意：文档中的“其他（自定义）”为自定义输入，不在此预设列表中
    # 预留后续扩展设备标签 ID 108~199

    # ========== 特别需求（可选，双方可多选） ==========
    (201, '校外拍摄', CATEGORY_SPECIAL),
    (202, '提供妆造服装', CATEGORY_SPECIAL),
    (203, '夜间可拍', CATEGORY_SPECIAL),
    (204, '可议价', CATEGORY_SPECIAL),
    (205, '一口价', CATEGORY_SPECIAL),
    (206, '加急单', CATEGORY_SPECIAL),
    # 预留后续扩展特别需求 ID 207~299

    # ========== 后期服务（可选，双方可多选） ==========
    (301, '图片精修', CATEGORY_POST),
    (302, '视频剪辑', CATEGORY_POST),
    (303, '无后期', CATEGORY_POST),
    # 预留后续扩展后期服务 ID 304~399
]

def get_tags_by_category(category):
    """返回指定分类的所有标签列表 [(id, name, category), ...]"""
    return [tag for tag in TAGS if tag[2] == category]

def is_valid_tag_id(tag_id):
    """判断给定的ID是否为有效的预设标签ID"""
    return any(tag_id == tag[0] for tag in TAGS)

def get_tag_name(tag_id):
    """根据标签ID返回标签名称，若不存在返回None"""
    for tid, name, _ in TAGS:
        if tid == tag_id:
            return name
    return None

def get_tag_category(tag_id):
    """根据标签ID返回标签分类，若不存在返回None"""
    for tid, _, category in TAGS:
        if tid == tag_id:
            return category
    return None