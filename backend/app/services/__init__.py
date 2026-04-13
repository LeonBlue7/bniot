"""
Services package
"""
from app.services.csrf import (
    CSRF_EXEMPT_PATHS,
    CSRF_EXPIRE_SECONDS,
    CSRF_SAFE_METHODS,
    create_csrf_token_for_user,
    generate_csrf_token,
    is_csrf_exempt,
    requires_csrf,
    store_csrf_token,
    verify_csrf_token,
)
from app.services.operation_log import (
    ActionType,
    OperationLogService,
    ResourceType,
    log_operation,
)
from app.services.permissions import (
    Permission,
    PermissionChecker,
    ROLE_PERMISSIONS,
    can_manage_user,
    check_role_permission,
    check_tenant_access,
    get_user_permissions,
    require_permission,
)
from app.services.protocol_parser import ProtocolParser, ProtocolParserRegistry, V10Parser, V20Parser
from app.services.rate_limiter import RateLimiter, check_rate_limit
from app.services.version_detector import VersionDetector, get_version_detector, init_version_detector
from app.services.websocket_manager import ConnectionManager, get_connection_manager

__all__ = [
    "ActionType",
    "CSRF_EXEMPT_PATHS",
    "CSRF_EXPIRE_SECONDS",
    "CSRF_SAFE_METHODS",
    "ConnectionManager",
    "OperationLogService",
    "Permission",
    "PermissionChecker",
    "ProtocolParser",
    "ProtocolParserRegistry",
    "RateLimiter",
    "ROLE_PERMISSIONS",
    "ResourceType",
    "V10Parser",
    "V20Parser",
    "VersionDetector",
    "can_manage_user",
    "check_rate_limit",
    "check_role_permission",
    "check_tenant_access",
    "create_csrf_token_for_user",
    "generate_csrf_token",
    "get_connection_manager",
    "get_user_permissions",
    "get_version_detector",
    "init_version_detector",
    "is_csrf_exempt",
    "log_operation",
    "require_permission",
    "requires_csrf",
    "store_csrf_token",
    "verify_csrf_token",
]
