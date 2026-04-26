from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog

auth_bp = Blueprint('auth', __name__)

def log_action(user_id, action, resource_type=None, resource_id=None, details=None, success=True):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=success
    )
    db.session.add(log)
    db.session.commit()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        log_action(None, 'login', 'user', username, 'Failed login attempt', False)
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        log_action(user.id, 'login', 'user', str(user.id), 'Login attempt for inactive account', False)
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create access token (identity must be a string for JWT subject)
    access_token = create_access_token(identity=str(user.id))
    
    # Log successful login
    log_action(user.id, 'login', 'user', str(user.id), 'Successful login')
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = int(get_jwt_identity())
    log_action(current_user_id, 'logout', 'user', str(current_user_id), 'User logged out')
    return jsonify({'message': 'Successfully logged out'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    if not user.check_password(current_password):
        log_action(user.id, 'change_password', 'user', str(user.id), 'Failed password change - incorrect current password', False)
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    user.set_password(new_password)
    db.session.commit()
    
    log_action(user.id, 'change_password', 'user', str(user.id), 'Password changed successfully')
    
    return jsonify({'message': 'Password changed successfully'}), 200
