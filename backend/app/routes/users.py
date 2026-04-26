from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog

users_bp = Blueprint('users', __name__)

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

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('all'):
        log_action(current_user_id, 'view_users', 'user', None, 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    users = User.query.all()
    
    log_action(current_user_id, 'view_users', 'user', None, 'Viewed user list')
    
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all') and current_user_id != user_id:
        log_action(current_user_id, 'view_user', 'user', str(user_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    log_action(current_user_id, 'view_user', 'user', str(user_id), f'Viewed user {user.username}')
    
    return jsonify({'user': user.to_dict()}), 200

@users_bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        log_action(current_user_id, 'create_user', 'user', None, 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Required fields
    required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=data['role'],
        department=data.get('department'),
        phone=data.get('phone')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    log_action(current_user_id, 'create_user', 'user', str(user.id), f'Created user {user.username}')
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all') and current_user_id != user_id:
        log_action(current_user_id, 'update_user', 'user', str(user_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        if User.query.filter(User.id != user_id, User.email == data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        user.email = data['email']
    if 'department' in data:
        user.department = data['department']
    if 'phone' in data:
        user.phone = data['phone']
    if 'is_active' in data and current_user.has_permission('all'):
        user.is_active = data['is_active']
    if 'role' in data and current_user.has_permission('all'):
        user.role = data['role']
    
    db.session.commit()
    
    log_action(current_user_id, 'update_user', 'user', str(user_id), f'Updated user {user.username}')
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if not current_user.has_permission('all'):
        log_action(current_user_id, 'delete_user', 'user', str(user_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    if current_user_id == user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = False
    db.session.commit()
    
    log_action(current_user_id, 'delete_user', 'user', str(user_id), f'Deactivated user {user.username}')
    
    return jsonify({'message': 'User deactivated successfully'}), 200
