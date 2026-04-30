/**
 * 设备卡片组件
 * 显示设备基本信息、状态、温湿度数据
 */

Component({
  /**
   * 组件属性
   */
  properties: {
    // 设备数据对象
    device: {
      type: Object,
      value: {}
    },
    // 是否显示详情按钮
    showDetail: {
      type: Boolean,
      value: true
    }
  },

  /**
   * 组件数据
   */
  data: {
    // 格式化后的数据
    formatted: {
      temp: '--',
      humi: '--',
      statusText: '离线',
      statusClass: 'status-offline',
      lastSeen: '--'
    }
  },

  /**
   * 数据监听器
   */
  observers: {
    'device': function(device) {
      if (device) {
        this.setData({
          formatted: {
            temp: this.formatTemp(device.temp),
            humi: this.formatHumi(device.humi),
            statusText: device.is_online ? '在线' : '离线',
            statusClass: device.is_online ? 'status-online' : 'status-offline',
            lastSeen: this.formatLastSeen(device.last_seen_at)
          }
        })
      }
    }
  },

  /**
   * 组件方法
   */
  methods: {
    /**
     * 格式化温度
     */
    formatTemp(temp) {
      if (temp === null || temp === undefined) return '--'
      return Number(temp).toFixed(1) + '°C'
    },

    /**
     * 格式化湿度
     */
    formatHumi(humi) {
      if (humi === null || humi === undefined) return '--'
      return Number(humi).toFixed(1) + '%'
    },

    /**
     * 格式化最后在线时间
     */
    formatLastSeen(timestamp) {
      if (!timestamp) return '--'

      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date

      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      if (hours < 24) return `${hours}小时前`
      if (days < 7) return `${days}天前`

      // 超过7天显示具体日期
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },

    /**
     * 点击卡片
     */
    onTap() {
      this.triggerEvent('tap', { device: this.properties.device })
    },

    /**
     * 点击详情按钮
     */
    onDetail() {
      this.triggerEvent('detail', { device: this.properties.device })
    }
  }
})