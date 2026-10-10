class Notification:
    def __init__(self, notification_id, title, message, date, role_target='student'):
        self.notification_id = notification_id
        self.title = title
        self.message = message
        self.date = date
        self.role_target = role_target
