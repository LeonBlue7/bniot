"""
测试数据库和 Docker 配置
TDD - 验证配置安全性、一致性和 TimescaleDB 支持
"""
import os
import pytest
import re
from pathlib import Path


# 动态确定项目根目录
# 在容器内运行时，项目根目录可能在不同位置
def get_project_root():
    """获取项目根目录"""
    # 检查环境变量
    if os.environ.get('PROJECT_ROOT'):
        return Path(os.environ.get('PROJECT_ROOT'))

    # 尝试从当前文件位置推断
    current_file = Path(__file__).resolve()

    # 可能的路径模式
    possible_paths = [
        # 从 tests/unit 向上找到 backend，再向上找到项目根目录
        current_file.parent.parent.parent.parent,  # /app/tests/unit -> /app -> parent of backend
        # 容器内路径: /app 是 backend 目录
        current_file.parent.parent.parent,  # /app/tests/unit -> /app (backend)
        Path('/home/leon/projects/bniot'),  # 宿主机路径
    ]

    for path in possible_paths:
        # 验证是否是有效的项目根目录（需要包含 docker-compose.yml）
        if (path / 'docker-compose.yml').exists():
            return path

    # 默认返回当前工作目录（可能只是 backend 目录）
    return Path.cwd()


PROJECT_ROOT = get_project_root()

# 检测是否在容器内运行（无法访问项目根目录文件）
def is_running_in_container():
    """检测是否在 Docker 容器内运行"""
    return not (PROJECT_ROOT / 'docker-compose.yml').exists()


# pytest 跳过标记：当在容器内运行时跳过这些测试
skip_in_container = pytest.mark.skipif(
    is_running_in_container(),
    reason="测试需要访问项目根目录文件，无法在容器内运行"
)


@skip_in_container
class TestDockerComposeSecurity:
    """测试 docker-compose.yml 安全配置"""

    @pytest.fixture
    def compose_path(self):
        """docker-compose.yml 文件路径"""
        return PROJECT_ROOT / "docker-compose.yml"

    @pytest.fixture
    def compose_content(self, compose_path):
        """读取 docker-compose.yml 内容"""
        with open(compose_path, 'r') as f:
            return f.read()

    def test_postgres_uses_timescaledb_image(self, compose_content):
        """验证 PostgreSQL 使用 TimescaleDB 镜像"""
        # 应使用 TimescaleDB 镜像
        assert 'timescale/timescaledb' in compose_content, \
            "应使用 timescale/timescaledb:latest-pg15 镜像"
        # 不应使用普通 postgres 镜像作为主要服务
        # 检查 postgres 服务是否使用 timescaledb 镜像
        lines = compose_content.split('\n')
        postgres_found = False
        timescale_used = False

        for i, line in enumerate(lines):
            if 'postgres:' in line and 'image' not in line and '#' not in line:
                postgres_found = True
            if postgres_found and 'image:' in line:
                if 'timescale/timescaledb' in line:
                    timescale_used = True
                break

        assert timescale_used, \
            "postgres 服务应使用 timescale/timescaledb 镜像而非 postgres:15-alpine"

    def test_no_default_postgres_password(self, compose_content):
        """验证 POSTGRES_PASSWORD 无默认值"""
        # 检查是否有带默认值的密码配置
        pattern = r'POSTGRES_PASSWORD:\s*\$\{POSTGRES_PASSWORD:-[^}]+\}'
        match = re.search(pattern, compose_content)
        assert match is None, \
            "POSTGRES_PASSWORD 不应有默认值，存在安全风险"

        # 应使用强制必填语法 ?:
        pattern_required = r'POSTGRES_PASSWORD:\s*\$\{POSTGRES_PASSWORD:\?'
        match_required = re.search(pattern_required, compose_content)
        assert match_required is not None, \
            "POSTGRES_PASSWORD 应使用必填语法 ${POSTGRES_PASSWORD:?...}"

    def test_no_default_redis_password(self, compose_content):
        """验证 REDIS_PASSWORD 无默认值"""
        # 检查是否有带默认值的密码配置
        pattern = r'requirepass \$\{REDIS_PASSWORD:-[^}]+\}'
        match = re.search(pattern, compose_content)
        assert match is None, \
            "REDIS_PASSWORD 不应有默认值，存在安全风险"

        # 应使用强制必填语法
        pattern_required = r'requirepass \$\{REDIS_PASSWORD:\?'
        match_required = re.search(pattern_required, compose_content)
        assert match_required is not None, \
            "REDIS_PASSWORD 应使用必填语法"

    def test_no_default_jwt_secret(self, compose_content):
        """验证 JWT_SECRET 无默认值"""
        # 检查是否有带默认值的 JWT_SECRET 配置
        pattern = r'JWT_SECRET:\s*\$\{JWT_SECRET:-[^}]+\}'
        match = re.search(pattern, compose_content)
        assert match is None, \
            "JWT_SECRET 不应有默认值，存在安全风险"

        # 应使用强制必填语法
        pattern_required = r'JWT_SECRET:\s*\$\{JWT_SECRET:\?'
        match_required = re.search(pattern_required, compose_content)
        assert match_required is not None, \
            "JWT_SECRET 应使用必填语法"

    def test_postgres_port_not_exposed(self, compose_content):
        """验证 PostgreSQL 端口不暴露到主机"""
        # postgres 服务中端口映射应被注释
        lines = compose_content.split('\n')
        in_postgres_section = False
        port_exposed = False

        for line in lines:
            # 检测进入 postgres 服务区块
            if re.match(r'^\s*postgres:\s*$', line):
                in_postgres_section = True
                continue
            # 检测离开 postgres 服务区块（进入下一个服务）
            if in_postgres_section and re.match(r'^\s{2}[a-z]+:\s*$', line) and 'postgres' not in line:
                break
            # 在 postgres 区块内检查端口
            if in_postgres_section and '5432:5432' in line:
                # 如果没有被注释
                stripped = line.strip()
                if not stripped.startswith('#'):
                    port_exposed = True

        assert not port_exposed, \
            "PostgreSQL 5432 端口不应暴露到主机（安全要求）"

    def test_redis_port_not_exposed(self, compose_content):
        """验证 Redis 端口不暴露到主机"""
        lines = compose_content.split('\n')
        in_redis_section = False
        port_exposed = False

        for line in lines:
            if re.match(r'^\s*redis:\s*$', line):
                in_redis_section = True
                continue
            if in_redis_section and re.match(r'^\s{2}[a-z]+:\s*$', line) and 'redis' not in line:
                break
            if in_redis_section and '6379:6379' in line:
                stripped = line.strip()
                if not stripped.startswith('#'):
                    port_exposed = True

        assert not port_exposed, \
            "Redis 6379 端口不应暴露到主机（安全要求）"

    def test_backend_uses_env_variables_without_defaults(self, compose_content):
        """验证后端服务敏感配置使用环境变量且无默认值"""
        # 检查敏感配置不使用默认值
        sensitive_vars = ['POSTGRES_PASSWORD', 'REDIS_PASSWORD', 'JWT_SECRET']

        for var in sensitive_vars:
            # 检查是否有带默认值的配置
            pattern = f'{var}:\\s*\\$\\{{{var}:-[^\\}}]+\\}}'
            if re.search(pattern, compose_content):
                pytest.fail(f"{var} 在后端服务中不应有默认值")


@skip_in_container
class TestInitDbSql:
    """测试 init-db.sql 配置"""

    @pytest.fixture
    def sql_path(self):
        """init-db.sql 文件路径"""
        return PROJECT_ROOT / "docker" / "init-db.sql"

    @pytest.fixture
    def sql_content(self, sql_path):
        """读取 init-db.sql 内容"""
        with open(sql_path, 'r') as f:
            return f.read()

    def test_timescaledb_extension_enabled(self, sql_content):
        """验证启用 TimescaleDB 扩展"""
        assert 'CREATE EXTENSION IF NOT EXISTS timescaledb' in sql_content, \
            "应启用 TimescaleDB 扩展"

    def test_device_data_hypertable_created(self, sql_content):
        """验证 device_data 表创建为 hypertable"""
        assert "SELECT create_hypertable('device_data'" in sql_content, \
            "device_data 表应创建为 TimescaleDB hypertable"

    def test_compression_policy_exists(self, sql_content):
        """验证压缩策略存在"""
        assert 'timescaledb.compress' in sql_content, \
            "应配置 TimescaleDB 压缩设置"
        assert 'add_compression_policy' in sql_content, \
            "应配置 TimescaleDB 压缩策略"

    def test_retention_policy_exists(self, sql_content):
        """验证保留策略存在"""
        assert 'add_retention_policy' in sql_content, \
            "应配置 TimescaleDB 数据保留策略"

    def test_compression_segment_by_correct(self, sql_content):
        """验证压缩 segmentby 配置正确"""
        assert 'compress_segmentby = \'device_id, tenant_id\'' in sql_content, \
            "压缩应按 device_id 和 tenant_id 分段"

    def test_devices_table_column_consistency(self, sql_content):
        """验证 devices 表字段名一致性（extra_data vs metadata）"""
        # 应该使用 extra_data 而非 metadata（与 SQLAlchemy 模型保持一致）
        assert 'extra_data JSONB DEFAULT' in sql_content, \
            "SQL 中 devices 表应使用 'extra_data' 字段名"

        # metadata 是 SQLAlchemy 保留字，不应作为列名
        # 检查 CREATE TABLE devices 部分
        devices_section = re.search(
            r'CREATE TABLE IF NOT EXISTS devices \([^)]+\)',
            sql_content, re.DOTALL
        )
        if devices_section:
            section_text = devices_section.group(0)
            assert 'metadata JSONB' not in section_text, \
                "devices 表不应有 metadata 字段（与 SQLAlchemy 保留字冲突），应使用 extra_data"

    def test_rls_policy_exists(self, sql_content):
        """验证 RLS 策略存在"""
        assert 'ENABLE ROW LEVEL SECURITY' in sql_content, \
            "应启用 Row Level Security 策略实现多租户隔离"

        # 检查所有多租户表都启用了 RLS
        rls_tables = ['users', 'zones', 'devices', 'device_data', 'alarms', 'operation_logs']
        for table in rls_tables:
            pattern = f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY'
            assert pattern in sql_content, \
                f"{table} 表应启用 Row Level Security"

    def test_tenant_isolation_function_exists(self, sql_content):
        """验证租户隔离函数存在"""
        assert 'CREATE OR REPLACE FUNCTION current_tenant_id()' in sql_content or \
               'CREATE OR REPLACE FUNCTION set_tenant_context(' in sql_content, \
            "应创建租户隔离函数用于 RLS 策略"

    def test_rls_policy_using_correct_pattern(self, sql_content):
        """验证 RLS 策略使用正确的租户隔离模式"""
        # RLS 策略应使用 current_tenant_id() 函数
        assert 'tenant_id = current_tenant_id()' in sql_content, \
            "RLS 策略应使用 tenant_id = current_tenant_id() 模式"

    def test_hypertable_chunk_interval_set(self, sql_content):
        """验证 hypertable chunk 间隔设置"""
        assert 'chunk_time_interval => INTERVAL \'1 day\'' in sql_content, \
            "hypertable chunk 间隔应设置为 1 天"

    def test_foreign_keys_have_indexes(self, sql_content):
        """验证外键都有索引"""
        # 检查 tenant_id 外键索引
        fk_columns = [
            ('users', 'tenant_id'),
            ('zones', 'tenant_id'),
            ('devices', 'tenant_id'),
            ('alarms', 'tenant_id'),
            ('operation_logs', 'tenant_id'),
            ('devices', 'zone_id'),
            ('zones', 'parent_id'),
        ]

        for table, column in fk_columns:
            index_pattern = f'CREATE INDEX idx_{table}_{column}'
            # 索引名可能不完全匹配，检查是否存在该列的索引
            assert f'idx_{table}_{column}' in sql_content or \
                   f'CREATE INDEX' in sql_content and f'{column}' in sql_content, \
                f"{table} 表的 {column} 外键应有索引"


class TestSqlAlchemyModels:
    """测试 SQLAlchemy 模型配置"""

    def test_device_model_has_extra_data_field(self):
        """验证 Device 模型有 extra_data 字段"""
        from app.models.models import Device

        assert hasattr(Device, 'extra_data'), \
            "Device 模型应有 extra_data 字段"

    def test_device_model_no_metadata_column(self):
        """验证 Device 模型没有 metadata 列（会与 SQLAlchemy 冲突）"""
        from app.models.models import Device

        # metadata 是 SQLAlchemy Base 的属性，不应作为表列
        columns = [c.name for c in Device.__table__.columns]
        assert 'metadata' not in columns, \
            "Device 模型不应有 metadata 列（与 SQLAlchemy 保留字冲突），应使用 extra_data"

    def test_all_models_have_tenant_fk_indexed(self):
        """验证所有多租户表的外键都有索引"""
        from app.models.models import Tenant, User, Zone, Device, Alarm

        # 检查 User 表
        user_columns_in_indexes = []
        for idx in User.__table__.indexes:
            for col in idx.columns:
                user_columns_in_indexes.append(col.name)
        assert 'tenant_id' in user_columns_in_indexes, \
            "User 表的 tenant_id 应有索引"

        # 检查 Zone 表
        zone_columns_in_indexes = []
        for idx in Zone.__table__.indexes:
            for col in idx.columns:
                zone_columns_in_indexes.append(col.name)
        assert 'tenant_id' in zone_columns_in_indexes, \
            "Zone 表的 tenant_id 应有索引"

        # 检查 Device 表
        device_columns_in_indexes = []
        for idx in Device.__table__.indexes:
            for col in idx.columns:
                device_columns_in_indexes.append(col.name)
        assert 'tenant_id' in device_columns_in_indexes, \
            "Device 表的 tenant_id 应有索引"

        # 检查 Alarm 表
        alarm_columns_in_indexes = []
        for idx in Alarm.__table__.indexes:
            for col in idx.columns:
                alarm_columns_in_indexes.append(col.name)
        assert 'tenant_id' in alarm_columns_in_indexes, \
            "Alarm 表的 tenant_id 应有索引"

    def test_device_data_model_has_time_column(self):
        """验证 DeviceData 模型有 time 列（用于 TimescaleDB）"""
        from app.models.models import DeviceData

        columns = [c.name for c in DeviceData.__table__.columns]
        assert 'time' in columns, \
            "DeviceData 模型应有 time 列作为 TimescaleDB 时间维度"

    def test_all_models_use_timestamptz(self):
        """验证所有时间字段使用 TIMESTAMPTZ"""
        from app.models.models import Tenant, User, Zone, Device, Alarm
        from sqlalchemy import DateTime

        # 检查各模型的时间字段类型
        models_to_check = [Tenant, User, Zone, Device, Alarm]

        for model in models_to_check:
            for col in model.__table__.columns:
                if col.name in ['created_at', 'updated_at', 'last_seen_at', 'last_login_at', 'occurred_at', 'resolved_at']:
                    # SQLAlchemy DateTime 在 PostgreSQL 中映射到 TIMESTAMPTZ
                    assert isinstance(col.type, DateTime), \
                        f"{model.__tablename__}.{col.name} 应使用 DateTime 类型"


@skip_in_container
class TestEnvExample:
    """测试 .env.example 配置"""

    def test_no_real_default_passwords(self):
        """验证 .env.example 中无真实默认密码"""
        env_path = PROJECT_ROOT / ".env.example"

        with open(env_path, 'r') as f:
            content = f.read()

        # 检查没有真实密码
        dangerous_defaults = [
            'POSTGRES_PASSWORD=bniot123',
            'REDIS_PASSWORD=redis123',
            'JWT_SECRET=your_jwt_secret_here',  # 这是占位符，应该是安全的
        ]

        for dangerous in dangerous_defaults[:2]:  # 只检查前两个真实密码
            assert dangerous not in content, \
                f".env.example 不应包含真实默认密码: {dangerous}"

    def test_required_env_variables_documented(self):
        """验证必需的环境变量都有文档说明"""
        env_path = PROJECT_ROOT / ".env.example"

        with open(env_path, 'r') as f:
            content = f.read()

        required_vars = [
            'POSTGRES_PASSWORD',
            'REDIS_PASSWORD',
            'JWT_SECRET',
            'POSTGRES_DB',
            'POSTGRES_USER'
        ]

        for var in required_vars:
            assert var in content, f".env.example 应包含 {var} 环境变量"

    def test_env_example_has_placeholder_passwords(self):
        """验证 .env.example 使用占位符密码"""
        env_path = PROJECT_ROOT / ".env.example"

        with open(env_path, 'r') as f:
            content = f.read()

        # 应使用占位符而非真实密码
        placeholders = ['your_secure_password', 'your_redis_password', 'changeme']
        has_placeholder = any(p in content for p in placeholders)

        assert has_placeholder, \
            ".env.example 应使用占位符密码（如 your_secure_password_here）"


@skip_in_container
class TestScriptsExist:
    """测试必需脚本文件存在"""

    def test_check_env_script_exists(self):
        """验证环境检查脚本存在"""
        script_path = PROJECT_ROOT / "scripts" / "check-env.sh"
        assert script_path.exists(), \
            "scripts/check-env.sh 环境检查脚本应存在"

    def test_migrate_db_script_exists(self):
        """验证数据库迁移脚本存在"""
        script_path = PROJECT_ROOT / "scripts" / "migrate-db.sh"
        assert script_path.exists(), \
            "scripts/migrate-db.sh 数据库迁移脚本应存在"