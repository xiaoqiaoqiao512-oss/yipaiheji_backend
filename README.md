# 一拍和集 (YiPaiHeJi) 后端 API

一个基于 Django 和 Django REST Framework 的大学生摄影交易平台的后端服务。用户可以发布摄影需求，创作者可以提供摄影服务。

## 📋 项目概述

本项目是一个完整的 REST API 后端，支持以下核心功能：
- 用户注册、登录、认证（JWT）
- 用户身份管理（普通学生/创作者/管理员）
- 创作者档案与作品集管理
- 用户需求发布与管理
- 实时消息聊天系统

---

## 🏗️ 项目结构清单

```
yipaiheji_backend/
├── manage.py                    # Django项目管理命令行工具
├── db.sqlite3                   # SQLite数据库文件（开发环境）
├── yipaiheji/                   # Django项目配置模块
│   ├── settings.py              # 项目配置文件（数据库、应用、中间件等）
│   ├── urls.py                  # 项目URL路由配置
│   ├── asgi.py                  # ASGI应用入口（异步）
│   └── wsgi.py                  # WSGI应用入口（生产部署）
│
├── users/                       # 用户模块
│   ├── models.py                # 自定义User模型（扩展了Django内置用户）
│   │   └── User: 用户基础模型，包含角色、认证状态、统计信息
│   ├── views.py                 # API视图
│   │   ├── RegisterView: 用户注册API（允许任何人访问）
│   │   ├── LoginView: 用户登录API（返回JWT token）
│   │   └── UserProfileView: 获取当前登录用户信息
│   ├── serializers.py           # 序列化器（数据验证和转换）
│   ├── urls.py                  # 用户模块URL路由
│   ├── admin.py                 # Django admin配置
│   ├── signals.py               # Django信号（钩子函数）
│   ├── tests.py                 # 单元测试
│   └── migrations/              # 数据库迁移文件
│
├── creators/                    # 创作者模块
│   ├── models.py                # 创作者相关数据模型
│   │   ├── CreatorProfile: 创作者档案（一对一关联到User）
│   │   │   └── 包含服务介绍、价格、大满视等信息
│   │   ├── Work: 创作者作品集
│   │   │   └── 包含作品图片、描述、标签、互动数据
│   │   └── Service: 创作者提供的服务
│   │       └── 包含服务类型、价格、详情等
│   ├── views.py                 # API视图
│   │   ├── CreatorProfileView: 创作者档案管理（需认证为创作者）
│   │   ├── CreatorPublicView: 公开创作者信息（任何人可访问）
│   │   ├── WorkListCreateView: 创作者作品列表和上传
│   │   └── IsCreator权限类: 限制只有已认证创作者可访问
│   ├── serializers.py           # 序列化器
│   ├── urls.py                  # 创作者模块URL路由
│   ├── admin.py                 # Django admin配置
│   ├── tests.py                 # 单元测试
│   └── migrations/              # 数据库迁移文件
│
├── demands/                     # 需求模块
│   ├── models.py                # 需求相关数据模型
│   │   ├── Demand: 用户发布的需求
│   │   │   ├── 需求类型：约拍/妆造/修图
│   │   │   ├── 状态：待接单/已接单/进行中/已完成/已取消
│   │   │   ├── 包含时间、地点、预算、人数等信息
│   │   │   └── 可与创作者匹配
│   │   └── DemandComment: 需求评论（创作者报价）
│   │       └── 用于创作者对需求进行报价和沟通
│   ├── views.py                 # API视图
│   │   ├── DemandListCreateView: 需求列表和创建
│   │   │   └── 支持按类型、地点、状态、预算过滤
│   │   ├── DemandDetailView: 需求详情、编辑、删除
│   │   │   └── 只有发布者可以修改/删除
│   │   └── DemandCommentCreateView: 需求报价发布
│   ├── serializers.py           # 序列化器
│   ├── urls.py                  # 需求模块URL路由
│   ├── admin.py                 # Django admin配置
│   ├── tests.py                 # 单元测试
│   └── migrations/              # 数据库迁移文件
│
├── chat/                        # 聊天模块（开发中）
│   ├── models.py                # 聊天数据模型（待实现）
│   ├── views.py                 # 聊天API视图（待实现）
│   ├── serializers.py           # 聊天序列化器（待实现）
│   ├── urls.py                  # 聊天模块URL路由
│   ├── admin.py                 # Django admin配置
│   ├── tests.py                 # 单元测试
│   └── migrations/              # 数据库迁移文件
│
└── media/                       # 媒体文件存储目录（开发环境）
    ├── avatars/                 # 用户头像
    ├── student_cards/           # 学生证照片
    └── works/                   # 创作者作品图片
```

---

## 📄 关键文件详解

### 1. **yipaiheji/settings.py** - 项目配置文件

**主要配置项：**
- `SECRET_KEY`: Django密钥（生产环境需修改）
- `DEBUG`: 调试模式开关（生产环境必须改为False）
- `ALLOWED_HOSTS`: 允许的主机列表（生产环境需配置）
- `INSTALLED_APPS`: 注册的应用列表
  - Django内置应用：admin、auth、contenttypes等
  - 自定义应用：users、creators、demands、chat
  - 第三方应用：rest_framework、rest_framework_simplejwt（JWT认证）
- `DATABASES`: 数据库配置（默认SQLite，生产推荐PostgreSQL）
- `REST_FRAMEWORK`: DRF配置
  - 默认认证方式为JWT
  - 默认权限为IsAuthenticated（需要认证）
- `SIMPLE_JWT`: JWT令牌配置
  - ACCESS_TOKEN_LIFETIME: 访问令牌7天有效期
  - REFRESH_TOKEN_LIFETIME: 刷新令牌30天有效期
- `MEDIA_URL` 和 `MEDIA_ROOT`: 媒体文件配置

### 2. **yipaiheji/urls.py** - 项目URL路由配置

**URL映射关系：**
```
/admin/                          → Django Admin后台
/api/users/                      → 用户API（注册、登录、个人信息）
/api/creators/                   → 创作者API（档案、作品、服务）
/api/demands/                    → 需求API（发布、搜索、报价）
/api/token/refresh/              → JWT令牌刷新接口
/media/                          → 媒体文件访问（开发环境）
```

### 3. **users/models.py** - 用户模型

**User 模型字段：**
- **基础信息**
  - `username`: 用户名（继承自AbstractUser）
  - `email`: 邮箱（继承自AbstractUser）
  - `first_name`, `last_name`: 名和姓
  - `student_id`: 学号（便于校园认证）
  - `phone`: 手机号
  - `avatar`: 用户头像图片

- **角色和认证**
  - `role`: 用户角色（student/creator/admin）
  - `is_verified`: 是否通过校园认证
  - `student_card_img`: 学生证照片（用于认证）
  - `creator_application_status`: 创作者申请状态（not_applied/pending/approved/rejected）
  - `creator_applied_at`: 创作者申请时间

- **个人简介**
  - `bio`: 个人简介文本
  - `tags`: 标签列表（JSON格式，如["人像","夜景"]）

- **统计**
  - `completed_orders`: 完成订单数
  - `is_active_creator`: 是否活跃创作者

- **时间戳**
  - `created_at`: 创建时间
  - `updated_at`: 更新时间

**内置方法：**
- `is_creator` 属性: 判断是否为已认证创作者
- `display_role` 属性: 返回显示的角色名称

### 4. **creators/models.py** - 创作者相关模型

**CreatorProfile 模型（创作者档案）：**
- 与User一对一关联（删除用户时档案也删除）
- **服务信息**: 服务介绍、基础价格、价格区间、是否议价
- **设备信息**: 相机型号、化妆/服装提供能力
- **统计信息**: 完成订单数、平均评分、被查看次数

**Work 模型（创作者作品）：**
- 与User多对一关联（一个创作者多个作品）
- **作品内容**: 标题、图片、描述
- **作品信息**: 标签、拍摄时间、拍摄地点
- **互动数据**: 点赞数、浏览数、公开状态
- 最多可上传20个作品

**Service 模型（创作者服务）：**
- 创作者提供的具体服务（如约拍、修图等）
- 包含服务名称、价格、详细描述

### 5. **demands/models.py** - 需求模型

**Demand 模型（用户发布的需求）：**
- **基础信息**: 标题、类型、详细描述
- **需求类型**: 约拍(photo)/妆造(makeup)/修图(retouch)
- **时间地点**: 拍摄时间、拍摄地点、校内地点
- **预算**: 预算金额、最低预算、最高预算、人数
- **状态管理**: pending(待)/matched(已接)/in_progress(进中)/completed(已完)/cancelled(已取)
- **标签和专题**: 标签列表、特色专题（如"樱花季"）
- **参考图**: 参考图片列表（JSON格式）
- **匹配信息**: 可与创作者匹配，记录匹配的创作者
- **统计**: 浏览数、评论数

**DemandComment 模型（需求评论/报价）：**
- 创作者对需求的报价和评论
- 用于需求发布者和创作者沟通

### 6. **chat/models.py** - 聊天模块（待实现）

目前为空，计划支持：
- 实时消息功能
- 用户之间的私信
- 可能需要WebSocket支持

---

## 🔧 必要的配置文件和环境变量

### 1. **requirements.txt** - 项目依赖

建议包含以下核心包：
```
Django>=6.0
djangorestframework
djangorestframework-simplejwt
django-cors-headers
python-decouple  # 用于加载环境变量
Pillow           # 图片处理
psycopg2-binary  # PostgreSQL驱动（可选）
```

### 2. **.env** - 环境变量配置文件（示例）

生产环境应创建此文件，包含敏感信息：
```env
# Django配置
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 数据库配置
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=yipaiheji_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# JWT配置
JWT_SECRET=your-jwt-secret

# 邮件配置（可选）
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# 媒体文件配置
MEDIA_ROOT=/path/to/media
MEDIA_URL=/media/
```

### 3. **.gitignore** - Git忽略文件

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Django
*.sqlite3
db.sqlite3
/media/
/static/

# IDE
.vscode/
.idea/
*.swp

# 环境变量
.env
.env.local

# OS
.DS_Store
Thumbs.db
```

### 4. **manage.py** - Django管理命令

常用命令：
```bash
# 创建数据库表
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 运行开发服务器
python manage.py runserver

# 创建新应用
python manage.py startapp chat

# 生成迁移文件
python manage.py makemigrations

# 查看SQL语句
python manage.py sqlmigrate app_name 0001
```

---

## 🚀 快速开始

### 环境设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd yipaiheji_backend

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 执行数据库迁移
python manage.py migrate

# 6. 创建超级用户
python manage.py createsuperuser

# 7. 运行开发服务器
python manage.py runserver
```

访问 http://localhost:8000/admin 进入Django后台管理。

---

## 📚 API 使用示例

### 用户注册
```bash
POST /api/users/register/
Content-Type: application/json

{
  "username": "student001",
  "password": "secure_password",
  "email": "student@example.com",
  "student_id": "202301001"
}

响应:
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "student001",
    "student_id": "202301001",
    "role": "student"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### 发布需求
```bash
POST /api/demands/
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "title": "毕业照约拍",
  "demand_type": "photo",
  "description": "寻找专业摄影师拍摄毕业照",
  "shooting_time": "2024-06-01T10:00:00Z",
  "location": "校园内",
  "budget": 300,
  "people_count": 1,
  "tags": ["毕业照", "人像"]
}
```

### 获取创作者公开信息
```bash
GET /api/creators/profiles/<creator_id>/
```

---

## 🔐 权限设置说明

| 端点 | 权限要求 | 说明 |
|------|---------|------|
| 用户注册 | AllowAny | 任何人可以注册 |
| 用户登录 | AllowAny | 任何人可以登录 |
| 需求列表 | IsAuthenticatedOrReadOnly | 已认证可发布，任何人可查看 |
| 创建需求 | IsAuthenticated | 需要认证 |
| 创作者档案 | IsCreator | 只有已认证创作者可访问 |
| 上传作品 | IsCreator | 只有已认证创作者可上传 |
| 获取创作者信息 | AllowAny | 任何人可查看 |

---

## 📦 主要依赖包说明

| 包名 | 版本 | 用途 |
|-----|------|------|
| Django | >=6.0 | Web框架 |
| djangorestframework | - | REST API框架 |
| djangorestframework-simplejwt | - | JWT认证 |
| Pillow | - | 图片处理 |
| django-cors-headers | - | 跨域资源共享(CORS) |
| python-decouple | - | 环境变量管理 |

---

## 🗄️ 数据库设计

### 表关系图
```
User (用户表)
├── 1对1 → CreatorProfile (创作者档案)
├── 1对N → Work (作品)
├── 1对N → Demand (发布的需求)
├── 1对N → DemandComment (评论/报价)
└── 1对N → Message (消息)

Demand (需求表)
├── N对1 → User (发布者)
├── N对1 → User (匹配的创作者)
└── 1对N → DemandComment (评论)

CreatorProfile (创作者档案)
├── 1对1 → User
├── 1对N → Service (提供的服务)
└── 1对N → Work (作品)
```

---

## ⚠️ 生产环境部署前检查清单

- [ ] `DEBUG = False` 已设置
- [ ] `SECRET_KEY` 已更改为强密钥
- [ ] `ALLOWED_HOSTS` 已配置
- [ ] 数据库已迁移到PostgreSQL（或其他生产数据库）
- [ ] `.env` 文件已创建且不在Git中
- [ ] 静态文件已收集 (`python manage.py collectstatic`)
- [ ] CORS设置已配置
- [ ] HTTPS已启用
- [ ] 日志记录已配置
- [ ] 备份策略已制定

---

## 🤝 贡献指南

1. 创建新分支: `git checkout -b feature/your-feature`
2. 提交更改: `git commit -m 'Add your feature'`
3. 推送分支: `git push origin feature/your-feature`
4. 提交Pull Request

---

## 📝 许可证

此项目采用 MIT 许可证。

---

## 👥 联系方式

如有问题或建议，请提交Issue或Pull Request。

