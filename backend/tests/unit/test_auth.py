"""
测试认证服务
Phase 2 核心模块测试
"""
import pytest
from datetime import timedelta


class TestPasswordHashing:
    """测试密码哈希"""

    def test_password_hash_and_verify(self):
        """测试密码哈希和验证"""
        from app.services.auth import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) == True

    def test_wrong_password_fails(self):
        """测试错误密码验证失败"""
        from app.services.auth import get_password_hash, verify_password

        hashed = get_password_hash("correct_password")

        assert verify_password("wrong_password", hashed) == False

    def test_different_passwords_different_hashes(self):
        """测试相同密码生成不同哈希"""
        from app.services.auth import get_password_hash

        hash1 = get_password_hash("password")
        hash2 = get_password_hash("password")

        # bcrypt 每次生成不同的哈希（因为有盐值）
        assert hash1 != hash2


class TestJWTToken:
    """测试 JWT 令牌"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        from app.services.auth import create_access_token

        data = {"sub": "testuser", "tenant_id": 1}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_expiry(self):
        """测试创建带过期时间的令牌"""
        from app.services.auth import create_access_token
        from jose import jwt
        from app.core.config import settings

        data = {"sub": "testuser"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in payload

    def test_token_contains_user_data(self):
        """测试令牌包含用户数据"""
        from app.services.auth import create_access_token
        from jose import jwt
        from app.core.config import settings

        data = {"sub": "admin", "tenant_id": 1}
        token = create_access_token(data)

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

        assert payload["sub"] == "admin"
        assert payload["tenant_id"] == 1


class TestCheckAdminRole:
    """测试管理员角色检查"""

    def test_admin_role_check(self):
        """测试管理员角色检查"""
        from app.services.auth import check_admin_role
        from app.models import User

        user = User(
            id=1,
            tenant_id=1,
            username="admin",
            password_hash="hash",
            role="admin"
        )

        assert check_admin_role(user) == True

    def test_non_admin_role_check(self):
        """测试非管理员角色检查"""
        from app.services.auth import check_admin_role
        from app.models import User

        user = User(
            id=1,
            tenant_id=1,
            username="viewer",
            password_hash="hash",
            role="viewer"
        )

        assert check_admin_role(user) == False

    def test_operator_role_check(self):
        """测试操作员角色检查"""
        from app.services.auth import check_admin_role
        from app.models import User

        user = User(
            id=1,
            tenant_id=1,
            username="operator",
            password_hash="hash",
            role="operator"
        )

        assert check_admin_role(user) == False