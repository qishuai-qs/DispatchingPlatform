# QS Service - 全自动平台服务

一个基于  FastAPI 构建的全自动化平台服务，具备用户管理、任务调度、配置管理等核心功能。

## 功能特性

### 核心功能
- **用户认证系统**：JWT Token认证、用户注册/登录、密码加密
- **任务调度引擎**：支持定时任务、一次性任务、周期性任务执行
- **配置中心**：YAML配置文件 + 环境变量，支持多环境部署
- **健康监控**：系统健康检查端点，运行状态监控
- **日志系统**：基于 Loguru 的结构化日志，支持文件轮转

### 技术特性
- **异步支持**：完整的 async/await 异步编程模型
- **数据库**：SQLAlchemy 2.0 + SQLite/PostgreSQL
- **API规范**：遵循 RESTful API 设计规范
- **类型安全**：完整的 Pydantic 类型注解
- **自动文档**：自动生成 OpenAPI/Swagger 文档

## 快速开始

### 环境要求
- Python >= 3.10
- Poetry (推荐) 或 pip

### 安装依赖

```bash
# 使用 Poetry
poetry install

# 或使用 pip
pip install -r requirements.txt
```

### 配置

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置必要参数：
```env
# JWT密钥（生产环境必须修改）
JWT_SECRET_KEY=your-secret-key-change-in-production

# 数据库URL（默认使用SQLite）
DB_URL=sqlite+aiosqlite:///./app.db

# 运行环境
ENV=development
```

### 启动服务

```bash
# 直接运行
python main.py

# 或使用 uvicorn
uvicorn main:app --reload

# 使用 Poetry
poetry run python main.py
```

服务启动后将监听 `http://localhost:8000`

## API文档

启动服务后，可以访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API端点

### 认证相关
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/refresh` | 刷新Token |

### 用户相关
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/users/me` | 获取当前用户信息 |
| PUT | `/api/v1/users/me` | 更新当前用户信息 |
| POST | `/api/v1/users/me/password` | 修改密码 |

### 任务相关
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/tasks` | 获取任务列表 |
| POST | `/api/v1/tasks` | 创建任务 |
| GET | `/api/v1/tasks/{id}` | 获取任务详情 |
| PUT | `/api/v1/tasks/{id}` | 更新任务 |
| DELETE | `/api/v1/tasks/{id}` | 删除任务 |
| POST | `/api/v1/tasks/{id}/execute` | 执行任务 |
| GET | `/api/v1/tasks/{id}/logs` | 获取任务日志 |
| GET | `/api/v1/tasks/statistics` | 任务统计 |

### 系统相关
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 应用信息 |
| GET | `/health` | 健康检查 |
| GET | `/api/v1/system/info` | 系统信息 |
| GET | `/api/v1/system/health` | 详细健康检查 |
| GET | `/api/v1/system/config` | 获取配置 |

## 项目结构

```
qs_service/
├── app/                    # 应用主目录
│   ├── api/               # API路由
│   │   ├── deps.py        # 依赖注入
│   │   ├── api.py         # 路由聚合
│   │   └── v1/            # API v1版本
│   │       ├── auth.py    # 认证路由
│   │       ├── users.py   # 用户路由
│   │       ├── tasks.py   # 任务路由
│   │       └── system.py  # 系统路由
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── security.py    # 安全工具
│   │   └── exceptions.py  # 异常定义
│   ├── crud/              # CRUD操作
│   │   ├── base.py        # CRUD基类
│   │   ├── user.py        # 用户CRUD
│   │   └── task.py        # 任务CRUD
│   ├── db/                # 数据库
│   │   └── session.py     # 会话管理
│   ├── models/            # 数据模型
│   │   ├── base.py        # 模型基类
│   │   ├── user.py        # 用户模型
│   │   └── task.py        # 任务模型
│   ├── schemas/           # Pydantic Schema
│   │   ├── common.py      # 通用Schema
│   │   ├── user.py        # 用户Schema
│   │   └── task.py        # 任务Schema
│   ├── services/          # 业务逻辑层
│   │   ├── scheduler.py   # 调度服务
│   │   ├── user_service.py # 用户服务
│   │   └── task_service.py # 任务服务
│   └── utils/             # 工具模块
│       ├── logger.py      # 日志工具
│       └── response.py    # 响应封装
├── config/                # 配置文件
│   └── app.yaml           # 应用配置
├── tests/                 # 测试目录
│   ├── conftest.py        # 测试配置
│   ├── test_auth.py       # 认证测试
│   └── test_api.py        # API测试
├── .env                   # 环境变量
├── .env.example           # 环境变量示例
├── main.py                # 入口文件
├── pyproject.toml         # 依赖管理
└── README.md              # 项目说明
```

## 任务类型

### 一次性任务 (one_time)
创建后立即执行或指定时间执行的任务

### 定时任务 (scheduled)
使用 Cron 表达式定义执行时间的周期性任务

```json
{
  "name": "每日备份",
  "task_type": "scheduled",
  "cron_expression": "0 2 * * *",
  "command": "python backup.py"
}
```

### 周期性任务 (recurring)
按固定时间间隔重复执行的任务

### 工作流任务 (workflow)
包含多个步骤的复杂任务链

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 带覆盖率报告
pytest --cov=app tests/

# 使用 Poetry
poetry run pytest
```

### 代码格式化

```bash
# 使用 Black 格式化代码
black .

# 使用 isort 排序导入
isort .

# 类型检查
mypy app/
```

## 生产部署

### 环境变量配置

```env
ENV=production
DEBUG=false
JWT_SECRET_KEY=your-secure-random-secret-key
DB_URL=postgresql+asyncpg://user:pass@host:port/dbname
```

### 使用 Gunicorn

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 8000

CMD ["python", "main.py"]
```

## 许可证

MIT License

## 作者

qishuai (shuai7868@gmail.com)
