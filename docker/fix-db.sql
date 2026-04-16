-- BNIoT 数据库修复脚本
-- 用于修复生产环境缺失的表和表结构问题
-- 执行时间: 2026-04-16

-- ============ 创建 alarms 表 ============
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
CREATE INDEX IF NOT EXISTS idx_alarms_tenant_id ON alarms(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alarms_device_id ON alarms(device_id);
CREATE INDEX IF NOT EXISTS idx_alarms_type ON alarms(type);
CREATE INDEX IF NOT EXISTS idx_alarms_occurred_at ON alarms(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_alarms_unresolved ON alarms(is_resolved) WHERE is_resolved = false;

-- ============ 创建 operation_logs 表（修复版，与 models.py 一致） ============
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE operation_logs IS '操作日志表 - 用户操作审计记录';
COMMENT ON COLUMN operation_logs.action IS '操作类型: create_device, update_device, delete_device, etc.';
COMMENT ON COLUMN operation_logs.resource_type IS '资源类型: device, zone, user, etc.';
COMMENT ON COLUMN operation_logs.resource_id IS '资源标识符（如设备ID）';

-- 日志索引
CREATE INDEX IF NOT EXISTS idx_operation_logs_tenant_id ON operation_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_action ON operation_logs(action);
CREATE INDEX IF NOT EXISTS idx_operation_logs_resource ON operation_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs(created_at DESC);

-- ============ 创建 protocol_versions 表 ============
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

-- 插入默认协议版本数据
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
 'V10 基础协议版本')
ON CONFLICT (version_code) DO NOTHING;

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
 'V20 新增冬夏关机温度和月份参数')
ON CONFLICT (version_code) DO NOTHING;

-- ============ 创建 notification_rules 表 ============
CREATE TABLE IF NOT EXISTS notification_rules (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    alarm_types JSONB DEFAULT '[]',
    severities JSONB DEFAULT '[]',
    channels JSONB DEFAULT '[]',
    recipients JSONB DEFAULT '[]',
    is_enabled BOOLEAN DEFAULT true,
    cooldown_minutes INT DEFAULT 30,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE notification_rules IS '通知规则表 - 告警通知配置';

CREATE INDEX IF NOT EXISTS idx_notification_rules_tenant_id ON notification_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notification_rules_enabled ON notification_rules(is_enabled);

-- ============ 创建 notification_records 表 ============
CREATE TABLE IF NOT EXISTS notification_records (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    alarm_id INT REFERENCES alarms(id) ON DELETE SET NULL,
    rule_id INT REFERENCES notification_rules(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE notification_records IS '通知记录表 - 通知发送历史';
COMMENT ON COLUMN notification_records.status IS '状态: pending, sent, failed, rate_limited';

CREATE INDEX IF NOT EXISTS idx_notification_records_tenant_id ON notification_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notification_records_alarm_id ON notification_records(alarm_id);
CREATE INDEX IF NOT EXISTS idx_notification_records_status ON notification_records(status);
CREATE INDEX IF NOT EXISTS idx_notification_records_created_at ON notification_records(created_at DESC);

-- ============ 创建 backup_records 表 ============
CREATE TABLE IF NOT EXISTS backup_records (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id) ON DELETE SET NULL,
    backup_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size INT,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE backup_records IS '备份记录表 - 数据备份历史';
COMMENT ON COLUMN backup_records.backup_type IS '备份类型: manual, scheduled, auto';
COMMENT ON COLUMN backup_records.status IS '状态: pending, in_progress, completed, failed';

CREATE INDEX IF NOT EXISTS idx_backup_records_tenant_id ON backup_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_backup_records_status ON backup_records(status);
CREATE INDEX IF NOT EXISTS idx_backup_records_backup_type ON backup_records(backup_type);
CREATE INDEX IF NOT EXISTS idx_backup_records_created_at ON backup_records(created_at DESC);

-- ============ 创建 restore_records 表 ============
CREATE TABLE IF NOT EXISTS restore_records (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    backup_id INT REFERENCES backup_records(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress INT DEFAULT 0,
    error_message TEXT,
    safety_backup_id INT REFERENCES backup_records(id),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE restore_records IS '恢复记录表 - 数据恢复历史';
COMMENT ON COLUMN restore_records.status IS '状态: pending, in_progress, completed, failed, rolled_back';

CREATE INDEX IF NOT EXISTS idx_restore_records_tenant_id ON restore_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_restore_records_status ON restore_records(status);
CREATE INDEX IF NOT EXISTS idx_restore_records_backup_id ON restore_records(backup_id);
CREATE INDEX IF NOT EXISTS idx_restore_records_created_at ON restore_records(created_at DESC);

-- ============ 创建触发器 ============
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER IF NOT EXISTS update_protocol_versions_updated_at BEFORE UPDATE ON protocol_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER IF NOT EXISTS update_notification_rules_updated_at BEFORE UPDATE ON notification_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 完成提示
SELECT '数据库修复完成！' AS message;