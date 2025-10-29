CASH = 'cash'
CARD = 'card'
BKASH = 'bkash'
ROCKET = 'rocket'
NAGAD = 'nagad'

PAYMENT_METHOD_CHOICES = [
    (CASH, 'Cash'),
    (CARD, 'Card'),
    (BKASH, 'bKash'),
    (ROCKET, 'Rocket'),
    (NAGAD, 'Nagad'),
]

PAYMENT_STATUS_PENDING = 'pending'
PAYMENT_STATUS_PAID = 'paid'
PAYMENT_STATUS_FAILED = 'failed'
PAYMENT_STATUS_CANCELLED = 'cancelled'
PAYMENT_STATUS_REFUNDED = 'refunded'
    
PAYMENT_STATUS_CHOICES = [
    (PAYMENT_STATUS_PENDING, 'Pending'),
    (PAYMENT_STATUS_PAID, 'Paid'),
    (PAYMENT_STATUS_FAILED, 'Failed'),
    (PAYMENT_STATUS_CANCELLED, 'Cancelled'),
    (PAYMENT_STATUS_REFUNDED, 'Refunded'),
]