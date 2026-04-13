/**
 * BNIoT JavaScript SDK 客户端
 *
 * 提供完整的 API 调用封装，支持认证、设备管理、告警处理等功能。
 */

/**
 * BNIoT API 错误类
 */
class BNIoTError extends Error {
  constructor(code, message, httpStatus, details = null) {
    super(`[${code}] ${message}`);
    this.code = code;
    this.message = message;
    this.httpStatus = httpStatus;
    this.details = details;
    this.name = 'BNIoTError';
  }
}

/**
 * BNIoT SDK 客户端
 *
 * 使用方法:
 *   const client = new BNIoTClient({ baseUrl: 'https://www.jxbonner.cloud/api' });
 *   await client.login('username', 'password');
 *   const devices = await client.getDevices();
 */
class BNIoTClient {
  /**
   * 初始化客户端
   * @param {Object} options - 配置选项
   * @param {string} options.baseUrl - API 基础 URL
   * @param {number} options.timeout - 请求超时时间（毫秒）
   * @param {number} options.retryCount - 失败重试次数
   */
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || 'http://localhost:5000/api';
    this.timeout = options.timeout || 30000;
    this.retryCount = options.retryCount || 3;
    this.token = null;
    this.ws = null;

    // WebSocket 回调
    this.onDeviceUpdate = null;
    this.onAlarm = null;
    this.onConnect = null;
    this.onDisconnect = null;
  }

  /**
   * 发送 HTTP 请求
   * @private
   */
  async _request(method, path, data = null, params = null, requireAuth = true) {
    const url = new URL(path, this.baseUrl);

    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
          url.searchParams.append(key, params[key]);
        }
      });
    }

    const headers = {
      'Content-Type': 'application/json',
    };

    if (requireAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    let lastError = null;

    for (let attempt = 0; attempt < this.retryCount; attempt++) {
      try {
        const response = await fetch(url.toString(), {
          method,
          headers,
          body: data ? JSON.stringify(data) : null,
        });

        if (!response.ok) {
          let errorData = {};
          try {
            errorData = await response.json();
          } catch (e) {
            errorData = { detail: await response.text() };
          }

          throw new BNIoTError(
            errorData.code || 'SYSTEM_001',
            errorData.message || errorData.detail || '请求失败',
            response.status,
            errorData.details
          );
        }

        return await response.json();

      } catch (error) {
        lastError = error;
        if (attempt < this.retryCount - 1 && !(error instanceof BNIoTError)) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }

    if (lastError instanceof BNIoTError) {
      throw lastError;
    }

    throw new BNIoTError('SYSTEM_001', `网络请求失败: ${lastError.message}`, 500);
  }

  // ============ 认证 ============

  /**
   * 用户登录
   * @param {string} username - 用户名
   * @param {string} password - 密码
   * @returns {Promise<Object>} 包含 token 的响应
   */
  async login(username, password) {
    const response = await this._request(
      'POST',
      '/auth/login',
      { username, password },
      null,
      false
    );
    this.token = response.access_token;
    return response;
  }

  /**
   * 获取当前用户信息
   * @returns {Promise<Object>} 用户信息
   */
  async getCurrentUser() {
    return this._request('GET', '/auth/me');
  }

  /**
   * 获取 CSRF Token
   * @returns {Promise<Object>} 包含 csrf_token 的响应
   */
  async getCsrfToken() {
    return this._request('GET', '/auth/csrf-token', null, null, false);
  }

  // ============ 设备管理 ============

  /**
   * 获取设备列表
   * @param {Object} options - 查询选项
   * @param {number} options.zoneId - 分区 ID 过滤
   * @param {boolean} options.isOnline - 是否在线过滤
   * @param {string} options.keyword - 关键词搜索
   * @param {number} options.skip - 跳过数量
   * @param {number} options.limit - 返回数量限制
   * @returns {Promise<Array>} 设备列表
   */
  async getDevices(options = {}) {
    const params = {
      zone_id: options.zoneId,
      is_online: options.isOnline,
      keyword: options.keyword,
      skip: options.skip || 0,
      limit: options.limit || 20,
    };
    return this._request('GET', '/devices', null, params);
  }

  /**
   * 获取设备详情
   * @param {number} deviceId - 设备 ID
   * @returns {Promise<Object>} 设备详情
   */
  async getDevice(deviceId) {
    return this._request('GET', `/devices/${deviceId}`);
  }

  /**
   * 获取设备历史数据
   * @param {number} deviceId - 设备 ID
   * @param {number} hours - 查询最近 N 小时数据
   * @returns {Promise<Array>} 历史数据列表
   */
  async getDeviceData(deviceId, hours = 24) {
    return this._request('GET', `/devices/${deviceId}/data`, null, { hours });
  }

  /**
   * 创建设备
   * @param {Object} data - 设备数据
   * @returns {Promise<Object>} 创建的设备信息
   */
  async createDevice(data) {
    return this._request('POST', '/devices', data);
  }

  /**
   * 更新设备
   * @param {number} deviceId - 设备 ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的设备信息
   */
  async updateDevice(deviceId, data) {
    return this._request('PUT', `/devices/${deviceId}`, data);
  }

  /**
   * 删除设备
   * @param {number} deviceId - 设备 ID
   * @returns {Promise<Object>} 操作结果
   */
  async deleteDevice(deviceId) {
    return this._request('DELETE', `/devices/${deviceId}`);
  }

  /**
   * 远程控制设备
   * @param {number} deviceId - 设备 ID
   * @param {Object} options - 控制选项
   * @param {number} options.airstate - 控制状态（0关机，1开机）
   * @returns {Promise<Object>} 操作结果
   */
  async controlDevice(deviceId, options) {
    return this._request(
      'POST',
      `/devices/${deviceId}/control`,
      null,
      { airstate: options.airstate }
    );
  }

  // ============ 批量操作 ============

  /**
   * 批量控制设备
   * @param {Array<number>} deviceIds - 设备 ID 列表
   * @param {Object} options - 控制选项
   * @param {number} options.airstate - 控制状态（0关机，1开机）
   * @returns {Promise<Object>} 批量操作结果
   */
  async batchControl(deviceIds, options) {
    return this._request(
      'POST',
      '/devices/batch/control',
      { device_ids: deviceIds, airstate: options.airstate }
    );
  }

  /**
   * 批量删除设备
   * @param {Array<number>} deviceIds - 设备 ID 列表
   * @returns {Promise<Object>} 批量操作结果
   */
  async batchDelete(deviceIds) {
    return this._request(
      'POST',
      '/devices/batch/delete',
      { device_ids: deviceIds }
    );
  }

  /**
   * 批量迁移设备分区
   * @param {Array<number>} deviceIds - 设备 ID 列表
   * @param {number|null} zoneId - 目标分区 ID（null 表示移出分区）
   * @returns {Promise<Object>} 批量操作结果
   */
  async batchMoveZone(deviceIds, zoneId) {
    return this._request(
      'POST',
      '/devices/batch/move-zone',
      { device_ids: deviceIds, zone_id: zoneId }
    );
  }

  // ============ 告警管理 ============

  /**
   * 获取告警列表
   * @param {Object} options - 查询选项
   * @param {boolean} options.isResolved - 是否已处理过滤
   * @param {number} options.skip - 跳过数量
   * @param {number} options.limit - 返回数量限制
   * @returns {Promise<Array>} 告警列表
   */
  async getAlarms(options = {}) {
    const params = {
      is_resolved: options.isResolved,
      skip: options.skip || 0,
      limit: options.limit || 20,
    };
    return this._request('GET', '/alarms', null, params);
  }

  /**
   * 处理告警
   * @param {number} alarmId - 告警 ID
   * @returns {Promise<Object>} 操作结果
   */
  async resolveAlarm(alarmId) {
    return this._request(
      'PUT',
      `/alarms/${alarmId}`,
      { is_resolved: true }
    );
  }

  // ============ 分区管理 ============

  /**
   * 获取分区列表
   * @returns {Promise<Array>} 分区列表
   */
  async getZones() {
    return this._request('GET', '/zones');
  }

  /**
   * 创建分区
   * @param {Object} data - 分区数据
   * @returns {Promise<Object>} 创建的分区信息
   */
  async createZone(data) {
    return this._request('POST', '/zones', data);
  }

  // ============ 统计数据 ============

  /**
   * 获取仪表盘统计数据
   * @returns {Promise<Object>} 统计数据
   */
  async getDashboardStats() {
    return this._request('GET', '/devices/stats');
  }

  // ============ WebSocket ============

  /**
   * 连接 WebSocket 实时推送
   */
  connectWebSocket() {
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws';

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      if (this.token) {
        this.ws.send(JSON.stringify({ type: 'auth', token: this.token }));
      }
      if (this.onConnect) {
        this.onConnect();
      }
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const msgType = data.type;

      if (msgType === 'device_update' && this.onDeviceUpdate) {
        this.onDeviceUpdate(data);
      } else if (msgType === 'alarm' && this.onAlarm) {
        this.onAlarm(data);
      }
    };

    this.ws.onclose = () => {
      if (this.onDisconnect) {
        this.onDisconnect();
      }
    };
  }

  /**
   * 断开 WebSocket 连接
   */
  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// 导出
module.exports = { BNIoTClient, BNIoTError };