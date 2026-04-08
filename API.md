# 一拍和集后端 API 文档

本文档基于当前代码实现整理，覆盖项目中已暴露的全部接口。

## 1. 基础信息

- 基础路径：/api/
- 本地开发地址示例：http://127.0.0.1:8000
- 认证方式：JWT Bearer Token
- 默认权限：已登录（全局默认 IsAuthenticated），具体接口若有放开会在文档中单独标注

### 1.1 鉴权头

请求需要鉴权时，请在 Header 中携带：

Authorization: Bearer <access_token>

### 1.2 Token 刷新

- 方法：POST
- 路径：/api/token/refresh/
- 权限：公开

请求体示例：

{
  "refresh": "<refresh_token>"
}

响应示例：

{
  "access": "<new_access_token>"
}

### 1.3 文件上传

涉及图片上传的接口（如作品图片、头像等）需使用 multipart/form-data。

---

## 2. 通用枚举

### 2.1 用户角色

- student：普通学生
- creator：创作者
- admin：管理员

### 2.2 创作者申请状态

- not_applied：未申请
- pending：审核中
- approved：已通过
- rejected：已拒绝

### 2.3 需求类型 demand_type

- photo：约拍
- makeup：妆造
- retouch：修图

### 2.4 需求状态 status

- pending：待接单
- matched：已接单
- in_progress：进行中
- completed：已完成
- cancelled：已取消

### 2.5 需求报价状态

- pending：待处理
- accepted：已接受
- rejected：已拒绝

### 2.6 聊天消息类型

- private：私聊
- groupbuy：拼单群聊

### 2.7 设备信息枚举

- post_type：rent（出租）、lease（求租）
- category：camera（摄影器材）、lens（镜头）、drone（无人机）、other（其他）
- status：active（进行中）、closed（已关闭）

### 2.8 拼单状态

- recruiting：招人中
- full：已满员
- completed：已完成
- cancelled：已取消

---

## 3. 用户模块 Users

前缀：/api/users/

### 3.1 注册

- 方法：POST
- 路径：/api/users/register/
- 权限：公开

请求体：

{
  "username": "student001",
  "student_id": "20230001",
  "phone": "13800000000",
  "password": "12345678",
  "confirm_password": "12345678"
}

成功响应（201）：

{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "student001",
    "student_id": "20230001",
    "role": "student"
  },
  "tokens": {
    "access": "...",
    "refresh": "..."
  }
}

失败说明：

- 400：用户名已存在、学号已注册、两次密码不一致等

### 3.2 登录

- 方法：POST
- 路径：/api/users/login/
- 权限：公开

请求体：

{
  "username": "student001",
  "password": "12345678"
}

成功响应（200）：

{
  "message": "登录成功",
  "user": {
    "id": 1,
    "username": "student001",
    "student_id": "20230001",
    "phone": "13800000000",
    "role": "student",
    "avatar": null,
    "is_verified": false,
    "bio": null,
    "tags": [],
    "creator_application_status": "not_applied",
    "creator_applied_at": null,
    "completed_orders": 0,
    "is_active_creator": true,
    "is_creator": false,
    "display_role": "学生",
    "created_at": "2026-04-08T00:00:00Z"
  },
  "tokens": {
    "access": "...",
    "refresh": "..."
  }
}

失败说明：

- 400：用户名或密码错误

### 3.3 当前用户信息

- 方法：GET
- 路径：/api/users/profile/
- 权限：登录

成功响应：UserProfileSerializer 全字段（同登录返回中的 user 对象结构）

### 3.4 申请成为创作者

- 方法：POST
- 路径：/api/users/apply-creator/
- 权限：登录

请求体：无

成功响应（200）：

{
  "success": true,
  "message": "创作者申请已提交，请等待审核",
  "user": { "...": "更新后的用户信息" }
}

失败说明：

- 400：未完成校园认证、已经是创作者等

### 3.5 检查是否可申请创作者

- 方法：GET
- 路径：/api/users/can-apply-creator/
- 权限：登录

成功响应：

{
  "can_apply": true,
  "reason": "可以申请成为创作者"
}

---

## 4. 创作者模块 Creators

前缀：/api/creators/

### 4.1 当前创作者档案

#### GET /api/creators/profile/

- 权限：创作者（已登录且 is_creator=true）
- 返回：CreatorProfileSerializer

#### PUT /api/creators/profile/

- 权限：创作者
- 说明：部分更新（后端使用 partial=True）
- 可更新字段：
  - service_intro
  - base_price
  - price_range
  - is_negotiable
  - camera_model
  - can_provide_makeup
  - can_provide_costume

### 4.2 创作者公开信息

- 方法：GET
- 路径：/api/creators/public/{id}/
- 权限：公开
- 返回：CreatorPublicSerializer，包含：
  - 基础公开信息
  - work_count（公开作品数量）
  - recent_works（最近 3 个公开作品）
  - services（服务列表）

### 4.3 作品管理

#### GET /api/creators/works/

- 权限：创作者
- 说明：仅返回当前登录创作者自己的作品

#### POST /api/creators/works/

- 权限：创作者
- Content-Type：multipart/form-data
- 必填字段：image
- 常用字段：title、description、tags、shooting_location、is_public
- 限制：每位创作者最多 20 个作品

成功响应：WorkSerializer

#### GET /api/creators/works/{pk}/

- 权限：创作者
- 说明：仅可访问自己的作品

#### PUT/PATCH /api/creators/works/{pk}/

- 权限：创作者
- Content-Type：multipart/form-data

#### DELETE /api/creators/works/{pk}/

- 权限：创作者

### 4.4 作品排序

#### PUT /api/creators/works/reorder/

- 权限：创作者
- 请求体：

{
  "order": [
    { "id": 12, "display_order": 0 },
    { "id": 8, "display_order": 1 }
  ]
}

成功响应：

{
  "message": "作品顺序已更新",
  "count": 2
}

- 注意：当前代码中排序逻辑依赖 display_order 字段，请确保数据库与模型已包含该字段后再启用此能力。

#### PATCH /api/creators/works/{pk}/order/

- 权限：创作者
- 请求体：

{
  "display_order": 3
}

### 4.5 服务项目管理

#### GET /api/creators/services/

- 权限：创作者
- 说明：仅返回当前用户自己的服务

#### POST /api/creators/services/

- 权限：创作者
- 请求体示例：

{
  "name": "毕业照约拍",
  "description": "包含前期沟通与精修",
  "base_price": "299.00",
  "price_range": "299-599",
  "estimated_time": "2小时",
  "is_negotiable": true,
  "is_available": true,
  "tags": ["人像", "毕业照"]
}

#### GET /api/creators/services/{pk}/

#### PUT/PATCH /api/creators/services/{pk}/

#### DELETE /api/creators/services/{pk}/

- 上述三个接口权限均为创作者，且仅可操作自己的服务

### 4.6 公开作品墙

- 方法：GET
- 路径：/api/creators/public-works/
- 权限：公开
- 说明：返回 is_public=true 的作品，按创建时间倒序

---

## 5. 需求模块 Demands

前缀：/api/demands/

### 5.1 需求列表与创建

#### GET /api/demands/

- 权限：公开
- 查询参数：
  - type：需求类型（photo/makeup/retouch）
  - location：地点模糊匹配
  - status：需求状态
  - min_budget：最小预算
  - max_budget：最大预算
- 默认行为：如果未传 status，仅返回 pending 状态需求
- 返回：DemandListSerializer 列表

#### POST /api/demands/

- 权限：登录
- 请求体示例：

{
  "title": "毕业照约拍",
  "demand_type": "photo",
  "description": "需要 1 小时校园拍摄",
  "shooting_time": "2026-05-10T09:00:00Z",
  "location": "武汉大学",
  "campus_location": "樱顶",
  "budget": "300.00",
  "min_budget": "200.00",
  "max_budget": "400.00",
  "people_count": 1,
  "tags": ["毕业照", "人像"],
  "special_topic": "毕业季",
  "reference_images": ["https://example.com/1.jpg"]
}

### 5.2 需求详情、修改、删除

#### GET /api/demands/{pk}/

- 权限：公开
- 返回：DemandDetailSerializer（包含 comments）

#### PUT/PATCH /api/demands/{pk}/

- 权限：登录
- 限制：仅需求发布者可修改

#### DELETE /api/demands/{pk}/

- 权限：登录
- 限制：仅需求发布者可删除

### 5.3 需求评论（报价）

#### GET /api/demands/{demand_id}/comments/

- 权限：公开
- 说明：按 created_at 正序返回报价列表

#### POST /api/demands/comments/create/

- 权限：登录
- 请求体示例：

{
  "demand": 10,
  "bid_price": "288.00",
  "message": "可提供拍摄+精修"
}

- 限制：同一用户对同一需求只能报价一次

#### POST /api/demands/comments/{comment_id}/accept/

- 权限：登录
- 限制：仅需求发布者可接受报价
- 成功后行为：
  - 当前报价状态改为 accepted
  - 需求状态改为 matched
  - matched_creator 设为该报价创作者
  - 同需求其他 pending 报价会批量改为 rejected

### 5.4 我的需求/我的报价

#### GET /api/demands/my-demands/

- 权限：登录
- 说明：当前用户发布的需求，按创建时间倒序

#### GET /api/demands/my-bids/

- 权限：登录
- 说明：当前用户提交的报价，按创建时间倒序

---

## 6. 聊天模块 Chat

前缀：/api/chat/

### 6.1 通用发送消息

- 方法：POST
- 路径：/api/chat/send/
- 权限：登录
- 请求体示例（私聊）：

{
  "message_type": "private",
  "receiver": 3,
  "content": "你好，方便沟通吗？"
}

- 请求体示例（拼单群聊）：

{
  "message_type": "groupbuy",
  "groupbuy": 5,
  "content": "我可以周末参与"
}

- 规则：
  - private 必须传 receiver
  - groupbuy 必须传 groupbuy
  - 群聊发送时会校验当前用户必须是该拼单成员（发起者或成员）

### 6.2 私聊会话

#### GET /api/chat/conversation/{user_id}/

- 权限：登录
- 说明：获取与指定用户的私聊消息，按时间正序；查看后自动将对方发来的未读消息标记为已读

#### POST /api/chat/conversation/{user_id}/

- 权限：登录
- 请求体示例：

{
  "content": "你好"
}

- 注意：若你需要稳定的私聊发送能力，建议优先使用 /api/chat/send/，其私聊参数校验更完整。

### 6.3 收件箱/发件箱/未读统计

#### GET /api/chat/inbox/

- 权限：登录
- 说明：当前用户收到的私聊，按创建时间倒序

#### GET /api/chat/sent/

- 权限：登录
- 说明：当前用户发出的私聊，按创建时间倒序

#### GET /api/chat/unread-count/

- 权限：登录
- 响应：

{
  "unread_count": 12
}

### 6.4 标记已读

- 方法：POST
- 路径：/api/chat/mark-read/{user_id}/
- 权限：登录
- 说明：将与指定用户的未读私聊批量标记为已读

响应：

{
  "status": "messages marked as read"
}

### 6.5 拼单群聊消息

#### GET /api/chat/groupbuy/{groupbuy_id}/

- 权限：登录
- 说明：获取指定拼单群聊消息，按 created_at 正序

#### POST /api/chat/groupbuy/{groupbuy_id}/

- 权限：登录
- 请求体示例：

{
  "content": "我这周六可到"
}

- 说明：仅拼单成员可发送

---

## 7. 设备租赁模块 Equipment

前缀：/api/equipment/

### 7.1 设备信息列表

#### GET /api/equipment/posts/

- 权限：公开
- 说明：返回 status=active 的设备信息，按创建时间倒序
- 查询参数：
  - post_type：rent/lease
  - category：camera/lens/drone/other
- 返回重点字段：
  - thumbnail：设备缩略图（首张图片）
  - device_model：设备型号
  - rent_per_day：日租金
  - publisher_username：发布者昵称
  - publisher_is_verified：发布者认证标识
  - publisher_creator_profile_id：可跳转创作者主页的 id（无则为 null）

### 7.2 发布设备信息

#### POST /api/equipment/posts/

- 权限：登录
- Content-Type：multipart/form-data（推荐）
- 表单字段：
  - post_type：rent/lease（必填）
  - category：camera/lens/drone/other（必填）
  - device_model：设备型号（必填）
  - rent_per_day：日租金（必填）
  - deposit：押金（可选）
  - description：设备描述（可选）
  - upload_images：设备图片数组（可选，最多 3 张）
- JSON 请求示例（不含图片）：

{
  "post_type": "rent",
  "category": "camera",
  "device_model": "Canon R6",
  "rent_per_day": "120.00",
  "deposit": "1000.00", 
  "description": "支持校内当面验机"
}

- 说明：
  - publisher 自动绑定当前用户
  - status 初始为 active
  - 当 upload_images 超过 3 张时，返回 400 校验错误

### 7.3 设备详情

#### GET /api/equipment/posts/{pk}/

- 权限：公开
- 说明：返回指定设备详情（仅 active），包含 images 图片列表用于轮播

### 7.4 联系发布者

#### POST /api/equipment/posts/{pk}/contact/

- 权限：登录
- 说明：
  - 复用私信系统，自动向设备发布者发送私聊消息
  - 不允许联系自己发布的设备
  - 可选传入 content，自定义咨询内容；不传则生成默认咨询文案
- 请求体示例：

{
  "content": "你好，我想周末租这台设备，可以校内当面验机吗？"
}

- 成功响应示例（201）：

{
  "message": "已向发布者发送私信",
  "equipment_id": 12,
  "receiver_id": 8,
  "chat_message_id": 156
}

### 7.5 风险提示

- 方法：GET
- 路径：/api/equipment/risk-tips/
- 权限：公开

响应示例：

{
  "risk_notice": "平台仅提供信息发布，交易风险由双方线下协商承担",
  "recommended_process": [
    "线下验机",
    "签订借条",
    "押金通过第三方保管"
  ]
}

---

## 8. 拼单模块 GroupBuy

前缀：/api/groupbuy/

### 8.1 拼单列表与发布

#### GET /api/groupbuy/

- 权限：公开
- 说明：返回 status=recruiting 的拼单，按创建时间倒序
- 查询参数：
  - max_cost：每人费用上限

#### POST /api/groupbuy/

- 权限：登录
- 请求体示例：

{
  "title": "毕业季团拍拼单",
  "description": "还差 2 人，可分摊摄影师费用",
  "target_people_count": 3,
  "cost_per_person": "199.00"
}

- 说明：initiator 自动绑定当前用户

### 8.2 拼单详情与修改

#### GET /api/groupbuy/{pk}/

- 权限：公开
- 返回：GroupBuySerializer（含成员列表 members）

#### PUT/PATCH /api/groupbuy/{pk}/

- 权限：需为发起者（非发起者会返回 403）

### 8.3 加入拼单

- 方法：POST
- 路径：/api/groupbuy/{pk}/join/
- 权限：登录

失败场景：

- 拼单已满员
- 已加入该拼单
- 不能加入自己发起的拼单

成功响应（201）：

{
  "message": "加入成功"
}

### 8.4 退出拼单

- 方法：POST
- 路径：/api/groupbuy/{pk}/leave/
- 权限：登录

失败场景：

- 发起者不能退出拼单
- 当前用户未加入该拼单

成功响应：

{
  "message": "已退出拼单"
}

---

## 9. 错误响应约定

本项目当前未完全统一错误响应结构，不同接口可能返回：

- {"error": "错误信息"}
- 字段级校验错误对象（如 {"username": ["用户名已存在"]}）
- DRF 默认权限错误（detail 字段）

建议前端统一兼容以下场景：

- error
- detail
- 字段数组错误

---

## 10. 对接建议

- 先完成注册或登录，保存 access 与 refresh。
- access 过期后调用 /api/token/refresh/ 获取新 access。
- 涉及图片上传统一使用 multipart/form-data。
- 需求列表默认只返回 pending，如需全部状态请显式传 status。
