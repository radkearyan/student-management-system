import random
from datetime import datetime
import backend.config.db_adapter as db_adapter

class FeeService:
    @staticmethod
    def get_fees(student_id='', search='', status=''):
        return db_adapter.get_fees(student_id=student_id, search=search, status=status)

    @staticmethod
    def add_fee(student_id, amount, status='Pending'):
        return db_adapter.add_fee(student_id, amount, status)

    @staticmethod
    def collect_fee(fee_id, payment_method='Cash / Offline'):
        txn_id = f"OFF-{random.randint(100000, 999999)}"
        pay_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return db_adapter.collect_fee_by_id(fee_id, pay_date, txn_id)

    @staticmethod
    def pay_fees(student_id, amount, card_number):
        try:
            fee_rec = db_adapter.get_fee_record_by_student(student_id)
            if not fee_rec:
                return False, "Fee record not found for student."
                
            if fee_rec.get('status') == 'Paid':
                return False, "Fees already paid."
                
            txn_id = f"TXN{random.randint(100000, 999999)}"
            pay_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            success, err = db_adapter.pay_fees(student_id, pay_date, txn_id)
            if not success:
                return False, err
                
            return True, txn_id
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_fee(fee_id):
        return db_adapter.delete_fee(fee_id)

    @staticmethod
    def bulk_add_fees(department, amount, status='Pending'):
        return db_adapter.bulk_add_fees(department, amount, status)

    @staticmethod
    def get_fee_receipt(fee_id):
        receipt = db_adapter.get_fee_receipt(fee_id)
        if not receipt:
            return None
            
        return {
            "receipt_no": f"REC-{receipt['fee_id']}-{datetime.now().year}",
            "fee_id": receipt['fee_id'],
            "student_id": receipt['student_id'],
            "name": receipt.get('name', ''),
            "department": receipt.get('department', ''),
            "course": receipt.get('course', ''),
            "semester": receipt.get('current_semester', 1),
            "amount": receipt['amount'],
            "payment_date": receipt['payment_date'],
            "status": receipt['status'],
            "txn_id": receipt['txn_id'],
            "college": "Student Management System",
            "motto": "",
            "account_head": "Tuition Fee A/C",
            "payment_method": "Online NetBanking / Card Gateway"
        }
