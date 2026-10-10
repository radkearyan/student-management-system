from flask import Blueprint, request, jsonify, session, send_file
from backend.services.fee_service import FeeService
from backend.utils.authentication import require_role
from backend.utils.pdf_generator import PDFGenerator

fees_bp = Blueprint('fees', __name__)

@fees_bp.route('', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_fees():
    student_id = request.args.get('student_id', '')
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Students can only check their own fee statements
    if session['user']['role'] == 'student':
        student_id = session['user']['reference_id']
        
    records = FeeService.get_fees(student_id=student_id, search=search, status=status)
    return jsonify(records)

@fees_bp.route('/add', methods=['POST'])
@require_role(['admin'])
def add_fee():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    amount = data.get('amount')
    status = data.get('status', 'Pending')
    
    if not student_id or not amount:
        return jsonify({"success": False, "message": "Student ID and fee amount are required."}), 400
        
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid amount format."}), 400
        
    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
        
    success, msg = FeeService.add_fee(student_id, amount, status)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@fees_bp.route('/collect/<fee_id>', methods=['POST'])
@require_role(['admin', 'teacher'])
def collect_fee(fee_id):
    data = request.get_json() or {}
    payment_method = data.get('payment_method', 'Cash / Offline')
    
    success, msg = FeeService.collect_fee(fee_id, payment_method)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@fees_bp.route('/pay', methods=['POST'])
@require_role(['student', 'admin', 'teacher'])
def pay_fees():
    data = request.get_json() or {}
    student_id = data.get('student_id') or (session['user'].get('reference_id') if session['user']['role'] == 'student' else '')
    amount = data.get('amount')
    card_number = data.get('card_number')
    
    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required."}), 400
    if not card_number or not amount:
        return jsonify({"success": False, "message": "Invalid payment details."}), 400
        
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid amount format."}), 400
        
    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
        
    success, result = FeeService.pay_fees(student_id, amount, card_number)
    
    if success:
        return jsonify({"success": True, "message": "Payment processed successfully.", "txn_id": result})
    return jsonify({"success": False, "message": result}), 400

@fees_bp.route('/receipt/<fee_id>', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def get_fee_receipt(fee_id):
    receipt = FeeService.get_fee_receipt(fee_id)
    
    if not receipt:
        return jsonify({"success": False, "message": "Fee record not found"}), 404
        
    # Check permissions
    if session['user']['role'] == 'student' and session['user']['reference_id'] != receipt['student_id']:
        return jsonify({"success": False, "message": "Unauthorized access to receipt"}), 403
        
    return jsonify({"success": True, "receipt": receipt})

@fees_bp.route('/receipt/<fee_id>/pdf', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def export_fee_receipt_pdf(fee_id):
    receipt = FeeService.get_fee_receipt(fee_id)
    
    if not receipt:
        return jsonify({"success": False, "message": "Fee record not found"}), 404
        
    # Check permissions: students can only access their own receipt
    if session['user']['role'] == 'student' and session['user']['reference_id'] != receipt['student_id']:
        return jsonify({"success": False, "message": "Unauthorized access to receipt"}), 403

    pdf_buffer = PDFGenerator.generate_fee_receipt_pdf(receipt)
    rec_num = str(receipt.get('receipt_no', f"REC-{fee_id}")).replace('/', '_').replace(' ', '_').lower()
    filename = f"fee_receipt_{rec_num}.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@fees_bp.route('/<int:fee_id>', methods=['DELETE'])
@require_role(['admin'])
def delete_fee_route(fee_id):
    success, msg = FeeService.delete_fee(fee_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400

@fees_bp.route('/bulk-add', methods=['POST'])
@require_role(['admin'])
def bulk_add_fees():
    data = request.get_json() or {}
    department = data.get('department', 'All')
    amount = data.get('amount')
    status = data.get('status', 'Pending')
    
    if not amount:
        return jsonify({"success": False, "message": "Fee amount is required."}), 400
        
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid amount format."}), 400
        
    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero."}), 400
        
    success, msg = FeeService.bulk_add_fees(department, amount, status)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400
