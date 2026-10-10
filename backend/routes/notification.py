from flask import Blueprint, request, jsonify, session
from backend.services.notification_service import NotificationService
from backend.utils.authentication import require_role

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/chatbot', methods=['POST'])
@require_role(['admin', 'teacher', 'student'])
def chatbot_assistant():
    data = request.get_json() or {}
    message = data.get('message', '')
    
    # Identify who is asking — role matters for response context
    user_session = session.get('user', {})
    role = user_session.get('role', 'student')
    user_name = user_session.get('name', '')
    # reference_id is the student/faculty ID; admins may not have one
    reference_id = user_session.get('reference_id') or ''
    
    if not message:
        if role == 'admin':
            return jsonify({"reply": "Hello Admin! I can give you system-wide stats on students, attendance, fees, and more. What would you like to know?"})
        return jsonify({"reply": "Hello! I am your AI Virtual Academic Assistant. How can I help you today?"})
        
    reply = NotificationService.get_chatbot_reply(
        reference_id=reference_id,
        message=message,
        role=role,
        user_name=user_name
    )
    return jsonify({"reply": reply})
