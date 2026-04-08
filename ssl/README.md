# SSL 证书配置说明

## 证书文件

将以下文件放置在此目录：

1. **fullchain.pem** - 完整证书链（包含域名证书 + 中间证书）
2. **privkey.pem** - 私钥文件

## 获取证书

### 方式1：Let's Encrypt 免费证书

```bash
# 安装 certbot
sudo apt install certbot

# 申请证书（先确保域名已解析到服务器）
sudo certbot certonly --standalone -d jxbonner.cloud -d www.jxbonner.cloud

# 证书位置
# /etc/letsencrypt/live/jxbonner.cloud/fullchain.pem
# /etc/letsencrypt/live/jxbonner.cloud/privkey.pem

# 复制到项目目录
sudo cp /etc/letsencrypt/live/jxbonner.cloud/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/jxbonner.cloud/privkey.pem ./ssl/
sudo chown $USER:$USER ./ssl/*.pem
```

### 方式2：腾讯云 SSL 证书

1. 登录腾讯云控制台
2. 申请免费 SSL 证书
3. 下载 Nginx 格式证书
4. 解压后将文件复制到此目录

## 自动续期

Let's Encrypt 证书有效期 90 天，需要定期续期：

```bash
# 测试续期
sudo certbot renew --dry-run

# 添加自动续期定时任务
sudo crontab -e

# 每周一凌晨5点检查并续期
0 5 * * 1 certbot renew --quiet && cp /etc/letsencrypt/live/jxbonner.cloud/*.pem /path/to/bniot/ssl/
```

## 文件权限

```bash
# 设置证书文件权限
chmod 644 ./ssl/fullchain.pem
chmod 600 ./ssl/privkey.pem  # 私钥文件需要更严格的权限
```

## 注意事项

- **不要将私钥文件提交到 Git**
- `.gitignore` 已配置忽略 `ssl/*.pem` 和 `ssl/*.key`
- 生产环境部署时确保证书文件已正确放置