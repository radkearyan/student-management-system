from functools import wraps
from flask import session, jsonify

def require_role(roles):
    """
    Decorator to restrict route access to users with specified roles.
    roles can be a string or a list of strings.
    """
    if isinstance(roles, str):
        roles = [roles]
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({"success": False, "message": "Unauthorized. Please log in."}), 401
            
            user_role = session['user'].get('role')
            if user_role not in roles:
                return jsonify({"success": False, "message": "Access denied. Insufficient permissions."}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
