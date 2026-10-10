class Fees:
    def __init__(self, fee_id, student_id, amount, payment_date=None, status='Pending', txn_id=None):
        self.fee_id = fee_id
        self.student_id = student_id
        self.amount = amount
        self.payment_date = payment_date
        self.status = status # Paid, Pending
        self.txn_id = txn_id
