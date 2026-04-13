/**
 * 认证示例 - 用户登录和获取信息
 *
 * 演示如何使用 BNIoT SDK 进行用户认证。
 */

const { BNIoTClient, BNIoTError } = require('../src/client');

async function main() {
  // 创建客户端
  const client = new BNIoTClient({
    baseUrl: 'https://www.jxbonner.cloud/api',
    timeout: 30000
  });

  try {
    // 登录
    console.log('正在登录...');
    const loginResult = await client.login('your_username', 'your_password');
    console.log(`登录成功! Token: ${loginResult.access_token}`);

    // 获取当前用户信息
    console.log('\n获取用户信息...');
    const user = await client.getCurrentUser();
    console.log(`用户名: ${user.username}`);
    console.log(`角色: ${user.role}`);
    console.log(`租户ID: ${user.tenant_id}`);

    // 获取 CSRF Token
    console.log('\n获取 CSRF Token...');
    const csrf = await client.getCsrfToken();
    console.log(`CSRF Token: ${csrf.csrf_token}`);

  } catch (error) {
    if (error instanceof BNIoTError) {
      console.log('登录失败!');
      console.log(`错误码: ${error.code}`);
      console.log(`错误消息: ${error.message}`);
      console.log(`HTTP状态: ${error.httpStatus}`);
      if (error.details) {
        console.log(`详情: ${JSON.stringify(error.details)}`);
      }
    } else {
      console.log(`未知错误: ${error.message}`);
    }
  }
}

main();