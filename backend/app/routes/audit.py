from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.audit_log import AuditLog
from app.models.user import User
from datetime import datetime


audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('all'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Query parameters
    user_filter = request.args.get('user_id', type=int)
    action = request.args.get('action')
    resource_type = request.args.get('resource_type')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = AuditLog.query
    
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    if action:
        query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    }), 200

@audit_bp.route('/logs/my', methods=['GET'])
@jwt_required()
def get_my_audit_logs():
    current_user_id = int(get_jwt_identity())
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    logs = AuditLog.query.filter_by(user_id=current_user_id).order_by(
        AuditLog.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    }), 200

@audit_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_audit_stats():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('all'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get statistics
    total_logs = AuditLog.query.count()
    today_logs = AuditLog.query.filter(
        db.func.date(AuditLog.timestamp) == db.func.current_date()
    ).count()
    
    # Most active users
    active_users = db.session.query(
        User.username,
        db.func.count(AuditLog.id).label('action_count')
    ).join(AuditLog).group_by(User.id).order_by(db.desc('action_count')).limit(10).all()
    
    # Action distribution
    action_counts = db.session.query(
        AuditLog.action,
        db.func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(db.desc('count')).limit(10).all()
    
    return jsonify({
        'total_logs': total_logs,
        'today_logs': today_logs,
        'active_users': [{'username': u[0], 'count': u[1]} for u in active_users],
        'action_distribution': [{'action': a[0], 'count': a[1]} for a in action_counts]
    }), 200
