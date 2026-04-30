"""
微信小程序服务
提供微信 API 调用功能
"""
import httpx
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_wechat_openid(code: str) -> dict | None:
    """
    通过微信 code 获取 openid

    Args:
        code: 小程序 wx.login() 获取的 code

    Returns:
        dict: 包含 openid 和 session_key 的字典，失败返回 None
    """
    if not code:
        return None

    # 微信小程序登录 API
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)

            if response.status_code != 200:
                logger.error(f"WeChat API HTTP error: {response.status_code}")
                return None

            data = response.json()

            # 检查是否有错误码
            if "errcode" in data and data["errcode"] != 0:
                logger.error(f"WeChat API error: {data.get('errcode')} - {data.get('errmsg')}")
                return None

            # 返回 openid 和 session_key
            if "openid" in data:
                return {
                    "openid": data["openid"],
                    "session_key": data.get("session_key", "")
                }

            return None

    except httpx.TimeoutException:
        logger.error("WeChat API timeout")
        return None
    except Exception as e:
        logger.error(f"WeChat API request failed: {e}")
        return None


async def get_wechat_openid_async(code: str) -> dict | None:
    """
    通过微信 code 获取 openid（异步版本）

    Args:
        code: 小程序 wx.login() 获取的 code

    Returns:
        dict: 包含 openid 和 session_key 的字典，失败返回 None
    """
    if not code:
        return None

    # 微信小程序登录 API
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)

            if response.status_code != 200:
                logger.error(f"WeChat API HTTP error: {response.status_code}")
                return None

            data = response.json()

            # 检查是否有错误码
            if "errcode" in data and data["errcode"] != 0:
                logger.error(f"WeChat API error: {data.get('errcode')} - {data.get('errmsg')}")
                return None

            # 返回 openid 和 session_key
            if "openid" in data:
                return {
                    "openid": data["openid"],
                    "session_key": data.get("session_key", "")
                }

            return None

    except httpx.TimeoutException:
        logger.error("WeChat API timeout")
        return None
    except Exception as e:
        logger.error(f"WeChat API request failed: {e}")
        return None