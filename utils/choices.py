OTP='OTP'
PROMO='Promo'
NOTIFICATION='Notification'
TRANSACTION='Transaction'
ACCOUNT = 'Account'
OTHER='Other'

SMS_TYPE_CHOICES = [
    (OTP, 'One Time Password'),
    (PROMO, 'Promotional'),
    (NOTIFICATION, 'Notification'),
    (TRANSACTION, 'Transactional'),
    (ACCOUNT, 'Account Credential'),
    (OTHER, 'Other'),
]

QUEUE='Queue'
SENT='Sent'
FAILED='Failed'
CANCELLED='Canceled'

STATUS_CHOICES = [
    (QUEUE, 'Queue'),
    (SENT, 'Sent'),
    (FAILED, 'Failed'),
    (CANCELLED, 'Canceled'),
]

# Cache Key
ROLE_CACHE = "role_cache"
ROLE_CACHE_TIMEOUT = 60 * 60 * 24 * 5  # 5 days