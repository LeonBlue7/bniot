/**
 * 告警条目组件
 * 显示告警信息、状态、处理操作
 */

Component({
  /**
   * 组件属性
   */
  properties: {
    // 告警数据对象
    alarm: {
      type: Object,
      value: {}
    },
    // 是否显示处理按钮
    showHandle: {
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
      severityText: '警告',
      severityClass: 'severity-warning',
      occurredTime: '--',
      isResolved: false,
      resolvedText: '未处理'
    }
  },

  /**
   * 数据监听器
   */
  observers: {
    'alarm': function(alarm) {
      if (alarm) {
        this.setData({
          formatted: {
            severityText: this.getSeverityText(alarm.severity),
            severityClass: this.getSeverityClass(alarm.severity),
            occurredTime: this.formatTime(alarm.occurred_at),
            isResolved: alarm.is_resolved,
            resolvedText: alarm.is_resolved ? '已处理' : '未处理'
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
     * 获取严重程度文本
     */
    getSeverityText(severity) {
      const map = {
        'critical': '严重',
        'warning': '警告',
        'info': '提示'
      }
      return map[severity] || severity || '警告'
    },

    /**
     * 获取严重程度样式类名
     */
    getSeverityClass(severity) {
      const map = {
        'critical': 'severity-critical',
        'warning': 'severity-warning',
        'info': 'severity-info'
      }
      return map[severity] || 'severity-warning'
    },

    /**
     * 格式化时间
     */
    formatTime(timestamp) {
      if (!timestamp) return '--'

      const date = new Date(timestamp)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')

      return `${year}-${month}-${day} ${hours}:${minutes}`
    },

    /**
     * 点击告警条目
     */
    onTap() {
      this.triggerEvent('tap', { alarm: this.properties.alarm })
    },

    /**
     * 点击处理按钮
     */
    onHandle() {
      this.triggerEvent('handle', { alarm: this.properties.alarm })
    }
  }
})