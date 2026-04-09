# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

空调节能管理系统物联网项目（BNIoT）- 用于智能空调设备的远程监控、能耗管理和节能控制。

核心业务逻辑由嵌入式程序实现（温度控制、定时开关等节能策略），UI端主要实现参数调整、数据查看、数据分析统计、远程操控设置。

## 开发工作流

严格遵循 **everything-claude-code** 工作流进行开发：
- 使用 `/everything-claude-code:plan` 进行实现规划
- 使用 `/everything-claude-code:tdd` 进行测试驱动开发
- 使用 `/everything-claude-code:code-review` 进行代码审查
- 使用 `/everything-claude-code:e2e` 进行端到端测试
- 使用 `/everything-claude-code:verify` 进行验证
- 使用 `/everything-claude-code:update-docs` 提交前同步更新相关技术文档

## 文档同步机制

为确保代码与技术文档保持同步，项目采用三层文档同步机制：

### 1. Git Hooks（推荐）

每次 `git commit` 前自动检查文档同步状态：

```bash
# 安装 Git Hooks
./scripts/install-hooks.sh
```

安装后，每次提交会自动检查以下内容：
- `.env.example` → `docs/ENV.md`
- `frontend/package.json` → `docs/CONTRIBUTING.md`
- `backend/app/*` → `docs/CODEMAPS/backend.md`
- `frontend/src/*` → `docs/CODEMAPS/frontend.md`
- `docker-compose.yml` → `docs/RUNBOOK.md`

### 2. Claude Code Hooks

在 Claude Code 配置文件 `~/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "PreCommit": [
      {
        "command": "/everything-claude-code:update-docs",
        "description": "提交前自动更新文档"
      }
    ]
  }
}
```

### 3. 手动更新

当文档检查失败时，执行：

```bash
# 或通过 Claude Code 命令
claude /everything-claude-code:update-docs
```

### 文档目录结构

```
docs/
├── ARCHITECTURE_PLAN.md   # 技术架构规划
├── CONTRIBUTING.md         # 贡献指南
├── ENV.md                  # 环境变量文档
├── RUNBOOK.md              # 运行手册
└── CODEMAPS/
    ├── backend.md          # 后端代码结构
    └── frontend.md         # 前端代码结构
```

### 文档更新规则

- **自动更新**：从源代码生成，使用 `<!-- AUTO-GENERATED -->` 标记
- **手动维护**：技术决策、架构说明等人工编写内容
- **更新触发**：源文件修改时间 > 文档修改时间时触发更新提示

## UI 设计规范

前端界面（管理后台和小程序）必须使用 **frontend-design** 插件进行设计：
- 使用 `/frontend-design:frontend-design` 命令
- 避免 AI 生成的千篇一律的 UI 设计
- 注重用户体验和视觉差异化

## Docker 开发环境

项目开发和生产环境统一使用 Docker：
- 所有服务必须在 Docker 容器中运行
- 避免"我本地能跑"的环境差异问题
- 确保 Docker 配置与生产环境一致
- 本地开发使用 `docker-compose`，生产使用对应部署配置

## 服务器与域名配置

- **生产服务器**：腾讯云轻量级应用服务器，Ubuntu 22.04 LTS
- **域名**：www.jxbonner.cloud（已备案）
- **小程序域名**：
  - request合法域名：`https://jxbonner.cloud`、`https://jxbonner.cloud:5000`
  - socket合法域名：`wss://www.jxbonner.cloud:8084`
- **SSL证书**：存放在项目根目录 `ssl/` 文件夹下

## MQTT 设备认证

设备端嵌入式程序已硬编码认证信息，无法修改：
- `MQTT_USERNAME=test1`
- `MQTT_PASSWORD=test123`

## 通信协议版本

设备端有两个协议版本，需区分解析：

### V10 参数集合
- 101-106：联动模式、温度设置参数
- 201-204：时间段设置
- 301-306：空调参数
- 401-405：告警参数
- 501：上送周期

### V20 新增参数
- 104：夏天空调关机温度
- 107：冬天空调关机温度
- 108：冬天开始月份
- 109：冬天结束月份
- 110：空调关机间隔

### 版本识别策略（主动探测 + 特征参数检测）

设备上线消息无版本字段，采用以下策略：

#### 主动探测流程
1. 收到设备 `/login` 消息后，平台**立即主动发送** `/getparam` 命令
2. 等待设备返回 `/getparam_reply`
3. 解析参数数据，检测版本特征参数
4. 缓存版本信息到 Redis，同时更新数据库设备表

#### 特征参数检测
V20 独有参数（V10 不存在）：
- `108`：冬天开始月份
- `109`：冬天结束月份
- `110`：空调关机间隔

判断逻辑：若参数数据包含 `108`、`109` 或 `110` 任一参数，则为 V20，否则为 V10。

**注意**：不能用 `104`、`107` 区分版本，因为 V10 和 V20 中这些参数含义完全不同：
- V10 `104` = 冬天空调允许开机温度
- V20 `104` = 夏天空调关机温度

#### 缓存策略
- Redis 存储：`device_version:{device_id}`，过期时间 7 天
- 设备重连时重新主动探测确认版本
- 设备换版本烧录固件时，缓存自动过期更新

#### 无需区分版本的消息
`/datas` 和 `/getdatas_reply` 消息体 V10/V20 相同，无需版本判断。

### 多版本演进规划

由于当前版本不支持固件远程升级，未来会有 V30、V40 等新版本。采用版本注册表 + 协议解析器模式，实现可扩展架构：

#### 版本编号规范
建议设备端 `Ver` 字段使用标准版本号：
- V10 → Ver=10
- V20 → Ver=20
- V30 → Ver=30

**优先级**：Ver字段 > 特征参数检测 > 默认版本

#### 版本注册表（数据库）
```sql
CREATE TABLE protocol_versions (
    version_code VARCHAR(10),      -- 'V10', 'V20'
    version_number INT,            -- 10, 20（对应Ver字段）
    feature_params JSONB,          -- 特征参数定义
    param_mappings JSONB,          -- 参数编号→含义映射
    is_active BOOLEAN
);
```

#### 协议解析器架构（策略模式）
```python
class ProtocolParser:
    parsers = {}  # 版本→解析器映射
    
    @classmethod
    def get_parser(cls, device_id, data):
        version = VersionDetector.detect(device_id, data)
        return cls.parsers.get(version, DefaultParser())

# 新版本接入：注册新解析器即可，无需修改核心逻辑
ProtocolParser.register('V30', V30Parser())
```

#### 新版本接入流程
1. 数据库添加版本注册记录
2. 编写新版本 Parser 类
3. 注册到 ProtocolParser
4. 无需修改版本识别/分发核心逻辑

## MQTT 主题格式

所有主题使用 `/up/{deviceID}/xxx`（设备上报）和 `/down/{deviceID}/xxx`（平台下发）格式：
- `/login` / `/login_reply`：设备上线
- `/datas` / `/datas_reply`：数据上送
- `/getdatas` / `/getdatas_reply`：平台刷新数据
- `/parameter` / `/parameter_reply`：设置参数上送
- `/getparam` / `/getparam_reply`：平台刷新参数
- `/ctr` / `/ctr_reply`：远程控制（开机/关机/复位）
- `/set` / `/set_reply`：设置参数
- `/ntp` / `/ntp_reply`：远程校时

deviceID 为 4G 模组的 IMEI 号。

## 系统功能需求

### 多租户
不同用户登录只显示本用户权限下的数据。

### 分区功能
按空调物理空间位置进行分区管理。

### 仪表盘
- 空调总数、开机状态数量
- 告警数量（MQTT设备离线告警、空调非法开启告警）
- 非法开启：不在温度设定内开启、不在正常上班时间开启

### 设备管理
- 单台/批量增删改查
- 模糊查询、批量设置参数、批量操作
- 开启/关闭空调功能
- 显示：MQTT设备ID、空调名称、温湿度

### 设备详情页
点击设备进入详情页，展示完整数据（参考通信协议）。

### 用户管理
仅系统管理员可见。

### 报表查询分析
数据统计与分析功能。

## 小程序配置

小程序已备案，后续迭代开发：
- `WECHAT_APPID=wx9fcb70ddbcf43ecd`
- `WECHAT_SECRET=fe7f8f3aa2b838ea2cc0fbb4ad4a6c38`

## 开发优先级

先完成后端与管理后台开发，小程序和固件远程升级后续迭代。

## 交互语言

全程使用中文与用户交互。
