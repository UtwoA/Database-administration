from fastapi import Header, HTTPException, status


ROLE_PERMISSIONS = {
    "guest": {"read_products"},
    "user": {"read_products", "manage_own_cart", "create_order", "read_own_orders"},
    "manager": {
        "read_products",
        "manage_products",
        "read_orders",
        "update_order_status",
        "read_analytics",
    },
    "admin": {"*"},
}


def get_role(x_role: str = Header(default="guest", alias="X-Role")) -> str:
    role = x_role.lower().strip()
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unknown role '{x_role}'. Use guest, user, manager, or admin.",
        )
    return role


def require_permission(permission: str):
    def dependency(x_role: str = Header(default="guest", alias="X-Role")) -> str:
        role = get_role(x_role)
        permissions = ROLE_PERMISSIONS[role]
        if "*" not in permissions and permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not allowed to perform this action.",
            )
        return role

    return dependency
