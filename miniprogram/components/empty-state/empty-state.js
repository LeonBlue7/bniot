/**
 * 空状态组件
 * 用于列表无数据时的提示
 */

Component({
  properties: {
    // 提示文本
    text: {
      type: String,
      value: '暂无数据'
    },
    // 图标类型
    icon: {
      type: String,
      value: 'empty'  // empty, search, error
    }
  },

  data: {
    iconEmoji: '📭'
  },

  observers: {
    'icon': function(icon) {
      const map = {
        'empty': '📭',
        'search': '🔍',
        'error': '❌',
        'device': '📱',
        'alarm': '🔔',
        'zone': '🏢'
      }
      this.setData({
        iconEmoji: map[icon] || '📭'
      })
    }
  },

  methods: {
    // 无方法
  }
})