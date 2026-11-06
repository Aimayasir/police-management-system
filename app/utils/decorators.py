from functools import wraps
from flask import flash, redirect, url_for, abort, request, session
from flask_login import current_user

def role_required(*allowed_roles):
    """
    Decorator to restrict route access to specific roles using session role.
    Admins are always granted access.
    Unauthorized access returns an HTTP 403 Forbidden page.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check role from session first, then fallback to current_user.role
            user_role = session.get('role')
            if not user_role and current_user.role:
                user_role = current_user.role.name
                session['role'] = user_role

            # Admin role has superuser override
            if user_role == 'Admin':
                return f(*args, **kwargs)

            if user_role not in allowed_roles:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(perm_code):
    """Decorator to restrict route access by granular permission code."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_permission(perm_code):
                flash('Access denied: You do not have permission to perform this action.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
