-- BNIoT 数据库初始化脚本
-- 创建时间: 2026-04-08
-- 更新时间: 2026-04-09
-- PostgreSQL 15 + TimescaleDB

-- ============ TimescaleDB 扩展 ============
-- 必须在创建 hypertable 之前启用
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

COMMENT ON EXTENSION timescaledb IS 'TimescaleDB 时序数据库扩展';

-- ============ 租户表 ============
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tenants IS '租户表 - 多租户隔离';

-- ============ 用户表 ============
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE users IS '用户表 - 多租户用户';
COMMENT ON COLUMN users.role IS '用户角色: admin(管理员), operator(操作员), viewer(观察者)';

-- 用户索引
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============ 分区表 ============
CREATE TABLE IF NOT EXISTS zones (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    parent_id INT REFERENCES zones(id) ON DELETE SET NULL,
    description TEXT,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE zones IS '分区表 - 空调物理空间分区';

-- 分区索引
CREATE INDEX idx_zones_tenant_id ON zones(tenant_id);
CREATE INDEX idx_zones_parent_id ON zones(parent_id);

-- ============ 设备表 ============
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    zone_id INT REFERENCES zones(id) ON DELETE SET NULL,
    device_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    protocol_version VARCHAR(10) DEFAULT 'V10',
    sim_card VARCHAR(30),
    firmware_version VARCHAR(20),
    is_online BOOLEAN DEFAULT false,
    last_seen_at TIMESTAMPTZ,
    settings JSONB DEFAULT '{}',
    -- 使用 extra_data 替代 metadata（与 SQLAlchemy 模型保持一致）
    extra_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE devices IS '设备表 - 空调设备信息';
COMMENT ON COLUMN devices.device_id IS '4G模组IMEI号，MQTT主题标识';
COMMENT ON COLUMN devices.protocol_version IS '协议版本: V10, V20, V30...';
COMMENT ON COLUMN devices.extra_data IS '设备扩展数据，存储非标准字段';

-- 设备索引
CREATE INDEX idx_devices_tenant_id ON devices(tenant_id);
CREATE INDEX idx_devices_zone_id ON devices(zone_id);
CREATE INDEX idx_devices_device_id ON devices(device_id);
CREATE INDEX idx_devices_is_online ON devices(is_online);
CREATE INDEX idx_devices_last_seen ON devices(last_seen_at DESC);

-- ============ 设备时序数据表 ============
CREATE TABLE IF NOT EXISTS device_data (
    id BIGSERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id VARCHAR(20) NOT NULL,
    tenant_id INT NOT NULL,
    temp FLOAT,
    humi FLOAT,
    airstate INT,
    current FLOAT,
    csq FLOAT,
    air_err INT,
    alarmtemp INT,
    alarmhumi INT
);

COMMENT ON TABLE device_data IS '设备时序数据 - 使用 TimescaleDB hypertable';

-- 时序数据索引
CREATE INDEX idx_device_data_time ON device_data(time DESC);
CREATE INDEX idx_device_data_device_id ON device_data(device_id, time DESC);
CREATE INDEX idx_device_data_tenant_id ON device_data(tenant_id, time DESC);

-- ============ TimescaleDB Hypertable 配置 ============
-- 将 device_data 转换为 hypertable 以支持时序数据高效查询
SELECT create_hypertable(
    'device_data',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- 压缩配置 - 7天前的数据压缩
ALTER TABLE device_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id, tenant_id'
);

-- 添加压缩策略 - 自动压缩 7 天前的数据
SELECT add_compression_policy(
    'device_data',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- 添加保留策略 - 自动删除 365 天前的数据（可按需调整）
SELECT add_retention_policy(
    'device_data',
    INTERVAL '365 days',
    if_not_exists => TRUE
);

COMMENT ON TABLE device_data IS '设备时序数据 - TimescaleDB hypertable (压缩:7天, 保留:365天)';

-- ============ 告警表 ============
CREATE TABLE IF NOT EXISTS alarms (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    device_id VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    message TEXT,
    details JSONB DEFAULT '{}',
    is_resolved BOOLEAN DEFAULT false,
    occurred_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE alarms IS '告警表 - 设备告警记录';
COMMENT ON COLUMN alarms.type IS '告警类型: offline(离线), illegal_on(非法开启), temp_alarm(温度告警)';
COMMENT ON COLUMN alarms.severity IS '严重级别: high(高), medium(中), low(低)';

-- 告警索引
CREATE INDEX idx_alarms_tenant_id ON alarms(tenant_id);
CREATE INDEX idx_alarms_device_id ON alarms(device_id);
CREATE INDEX idx_alarms_type ON alarms(type);
CREATE INDEX idx_alarms_occurred_at ON alarms(occurred_at DESC);
CREATE INDEX idx_alarms_unresolved ON alarms(is_resolved) WHERE is_resolved = false;

-- ============ 操作日志表 ============
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    device_id VARCHAR(20) NOT NULL,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE operation_logs IS '操作日志表 - 用户操作记录';

-- 日志索引
CREATE INDEX idx_operation_logs_tenant_id ON operation_logs(tenant_id);
CREATE INDEX idx_operation_logs_device_id ON operation_logs(device_id);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at DESC);

-- ============ 协议版本注册表 ============
CREATE TABLE IF NOT EXISTS protocol_versions (
    id SERIAL PRIMARY KEY,
    version_code VARCHAR(10) NOT NULL UNIQUE,
    version_number INT NOT NULL,
    feature_params JSONB DEFAULT '{}',
    param_mappings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE protocol_versions IS '协议版本注册表 - 多版本支持';

-- ============ Row Level Security (RLS) 配置 ============
-- 多租户隔离策略

-- 创建租户上下文设置函数
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id_param INT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('SET LOCAL app.current_tenant_id = %L', tenant_id_param);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION set_tenant_context IS '设置当前请求的租户上下文';

-- 创建获取当前租户 ID 的函数
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS INT AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::INT;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION current_tenant_id IS '获取当前租户 ID，用于 RLS 策略';

-- 启用 RLS 策略（生产环境启用）
-- 注意：开发阶段可能需要临时禁用，生产环境必须启用

-- 用户表 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

-- 分区表 RLS
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_zones ON zones
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

-- 设备表 RLS
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_devices ON devices
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

-- 设备数据表 RLS
ALTER TABLE device_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_device_data ON device_data
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

-- 告警表 RLS
ALTER TABLE alarms ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_alarms ON alarms
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

-- 操作日志表 RLS
ALTER TABLE operation_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_operation_logs ON operation_logs
    USING (tenant_id = current_tenant_id() OR current_tenant_id() IS NULL);

COMMENT ON POLICY tenant_isolation_users IS '用户表租户隔离策略';
COMMENT ON POLICY tenant_isolation_zones IS '分区表租户隔离策略';
COMMENT ON POLICY tenant_isolation_devices IS '设备表租户隔离策略';
COMMENT ON POLICY tenant_isolation_device_data IS '设备数据表租户隔离策略';
COMMENT ON POLICY tenant_isolation_alarms IS '告警表租户隔离策略';
COMMENT ON POLICY tenant_isolation_operation_logs IS '操作日志表租户隔离策略';

-- ============ 初始数据 ============
INSERT INTO tenants (name, code, settings) VALUES
('默认租户', 'default', '{"timezone": "Asia/Shanghai"}');

-- 默认管理员用户（密码: admin123）
INSERT INTO users (tenant_id, username, password_hash, role, is_active) VALUES
(1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G.4d.Z5h8K8KA6', 'admin', true);

-- ============ 协议版本初始化 ============
INSERT INTO protocol_versions (version_code, version_number, feature_params, param_mappings, description) VALUES
('V10', 10,
 '{"min": 101, "max": 501}',
 '{"101": {"name": "联动模式", "type": "int", "range": "0-1"},
   "102": {"name": "夏天空调允许开机温度", "type": "float"},
   "103": {"name": "夏天空调设置温度", "type": "float"},
   "104": {"name": "冬天空调允许开机温度", "type": "float"},
   "105": {"name": "冬天空调设置温度", "type": "float"},
   "106": {"name": "是否启用设置温度", "type": "int", "range": "0-1"},
   "201": {"name": "上班时间段", "type": "string"},
   "202": {"name": "加班时间段1", "type": "string"},
   "203": {"name": "加班时间段2", "type": "string"},
   "204": {"name": "加班时间段3", "type": "string"},
   "301": {"name": "空调代码", "type": "int"},
   "302": {"name": "空调模式", "type": "int", "range": "0-4"},
   "303": {"name": "风速", "type": "int", "range": "0-3"},
   "304": {"name": "风向", "type": "int", "range": "0-1"},
   "305": {"name": "空调灯", "type": "int", "range": "0-1"},
   "306": {"name": "最小电流判断", "type": "int"},
   "401": {"name": "告警判断开关", "type": "int", "range": "0-1"},
   "402": {"name": "温度上限", "type": "int"},
   "403": {"name": "温度下限", "type": "int"},
   "404": {"name": "湿度上限", "type": "int"},
   "405": {"name": "湿度下限", "type": "int"},
   "501": {"name": "上送周期", "type": "int"}}',
 'V10 基础协议版本');

INSERT INTO protocol_versions (version_code, version_number, feature_params, param_mappings, description) VALUES
('V20', 20,
 '{"exclusive": ["108", "109", "110"], "min": 101, "max": 501}',
 '{"101": {"name": "联动模式", "type": "int", "range": "0-1"},
   "102": {"name": "夏天空调允许开机温度", "type": "float"},
   "103": {"name": "夏天空调设置温度", "type": "float"},
   "104": {"name": "夏天空调关机温度", "type": "float"},
   "105": {"name": "冬天空调允许开机温度", "type": "float"},
   "106": {"name": "冬天空调设置温度", "type": "float"},
   "107": {"name": "冬天空调关机温度", "type": "float"},
   "108": {"name": "冬天开始月份", "type": "int"},
   "109": {"name": "冬天结束月份", "type": "int"},
   "110": {"name": "空调关机间隔", "type": "int"},
   "201": {"name": "上班时间段", "type": "string"},
   "202": {"name": "加班时间段1", "type": "string"},
   "203": {"name": "加班时间段2", "type": "string"},
   "204": {"name": "加班时间段3", "type": "string"},
   "301": {"name": "空调代码", "type": "int"},
   "302": {"name": "空调模式", "type": "int", "range": "0-4"},
   "303": {"name": "风速", "type": "int", "range": "0-3"},
   "304": {"name": "风向", "type": "int", "range": "0-1"},
   "305": {"name": "空调灯", "type": "int", "range": "0-1"},
   "306": {"name": "最小电流判断", "type": "int"},
   "401": {"name": "告警判断开关", "type": "int", "range": "0-1"},
   "402": {"name": "温度上限", "type": "int"},
   "403": {"name": "温度下限", "type": "int"},
   "404": {"name": "湿度上限", "type": "int"},
   "405": {"name": "湿度下限", "type": "int"},
   "501": {"name": "上送周期", "type": "int"}}',
 'V20 新增冬夏关机温度和月份参数');

-- ============ 触发器 ============
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zones_updated_at BEFORE UPDATE ON zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_protocol_versions_updated_at BEFORE UPDATE ON protocol_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============ 数据库应用用户创建（生产环境使用） ============
-- 注意：以下脚本在生产部署时需要手动执行，创建只读应用用户
-- CREATE USER bniot_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE bniot TO bniot_app;
-- GRANT USAGE ON SCHEMA public TO bniot_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bniot_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bniot_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO bniot_app;