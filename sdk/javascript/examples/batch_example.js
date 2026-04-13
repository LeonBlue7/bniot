/**
 * 批量操作示例 - 设备批量控制和删除
 *
 * 演示如何使用 BNIoT SDK 进行批量操作。
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
    const devices = await client.getDevices({ limit: 100 });
    if (devices.length < 3) {
      console.log('设备数量不足，跳过批量操作演示');
      return;
    }

    const deviceIds = devices.slice(0, 3).map(d => d.id);
    console.log(`选定设备: ${JSON.stringify(deviceIds)}`);

    // 批量开机
    console.log('\n批量开机...');
    const result = await client.batchControl(deviceIds, { airstate: 1 });
    console.log(`成功: ${result.success_count}`);
    console.log(`失败: ${result.failed_count}`);
    if (result.failed_details.length > 0) {
      console.log(`失败详情: ${JSON.stringify(result.failed_details)}`);
    }

    // 批量关机
    console.log('\n批量关机...');
    const result2 = await client.batchControl(deviceIds, { airstate: 0 });
    console.log(`成功: ${result2.success_count}`);

    // 批量迁移分区（示例）
    console.log('\n批量迁移分区（仅演示）...');
    // const moveResult = await client.batchMoveZone(deviceIds, 2);
    // console.log(`迁移结果: ${JSON.stringify(moveResult)}`);

    // 批量删除（危险操作，仅演示）
    console.log('\n批量删除（不实际执行）...');
    // const deleteResult = await client.batchDelete([testDeviceId]);
    // console.log(`删除结果: ${JSON.stringify(deleteResult)}`);

  } catch (error) {
    if (error instanceof BNIoTError) {
      console.log(`批量操作失败: [${error.code}] ${error.message}`);
    } else {
      console.log(`未知错误: ${error.message}`);
    }
  }
}

main();