/**
 * 设备管理示例 - 设备 CRUD 操作
 *
 * 演示如何使用 BNIoT SDK 进行设备管理。
 */

const { BNIoTClient, BNIoTError } = require('../src/client');

async function main() {
  // 创建并登录
  const client = new BNIoTClient({
    baseUrl: 'https://www.jxbonner.cloud/api'
  });

  await client.login('your_username', 'your_password');

  try {
    // 获取设备列表
    console.log('获取设备列表...');
    const devices = await client.getDevices({ limit: 10 });
    console.log(`找到 ${devices.length} 台设备`);

    devices.slice(0, 3).forEach(device => {
      console.log(`  - ID: ${device.id}, 名称: ${device.name}, 在线: ${device.is_online}`);
    });

    // 搜索设备
    console.log('\n搜索设备...');
    const searchResult = await client.getDevices({ keyword: '会议室' });
    console.log(`搜索结果: ${searchResult.length} 台`);

    // 获取单个设备详情
    if (devices.length > 0) {
      const deviceId = devices[0].id;
      console.log(`\n获取设备 ${deviceId} 详情...`);
      const device = await client.getDevice(deviceId);
      console.log(`设备名称: ${device.name}`);
      console.log(`设备ID: ${device.device_id}`);
      console.log(`协议版本: ${device.protocol_version}`);

      // 获取设备历史数据
      console.log(`\n获取设备 ${deviceId} 最近24小时数据...`);
      const data = await client.getDeviceData(deviceId, 24);
      if (data.length > 0) {
        const latest = data[0];
        console.log(`温度: ${latest.temp}C`);
        console.log(`湿度: ${latest.humi}%`);
        console.log(`空调状态: ${latest.airstate}`);
      }
    }

    // 创建新设备（示例）
    console.log('\n创建新设备（仅演示，实际不执行）...');
    // const newDevice = await client.createDevice({
    //   device_id: 'IMEI12345678',
    //   name: '测试空调',
    //   zone_id: 1
    // });
    // console.log(`创建成功: ${JSON.stringify(newDevice)}`);

    // 获取仪表盘统计
    console.log('\n获取仪表盘统计...');
    const stats = await client.getDashboardStats();
    console.log(`总设备数: ${stats.total_devices}`);
    console.log(`在线设备: ${stats.online_devices}`);
    console.log(`离线设备: ${stats.offline_devices}`);
    console.log(`未处理告警: ${stats.unresolved_alarms}`);

  } catch (error) {
    if (error instanceof BNIoTError) {
      console.log(`操作失败: [${error.code}] ${error.message}`);
    } else {
      console.log(`未知错误: ${error.message}`);
    }
  }
}

main();