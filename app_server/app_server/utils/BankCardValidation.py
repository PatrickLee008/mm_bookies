import re

# Case 19: account number is digits only; user name is English/Myanmar letters and spaces only.
# Myanmar digits (U+1040-U+1049) are excluded from the name charset.
_ACC_NUMBER_RE = re.compile(r'^[0-9]{6,20}$')
_ACC_NAME_RE = re.compile(r'^[A-Za-z\u1000-\u103F\u104A-\u109F ]{2,50}$')


def validate_acc_number(value):
    value = str(value).strip() if value is not None else ''
    if not value:
        return 'Account number is required'
    if not _ACC_NUMBER_RE.match(value):
        return 'Account number must be 6-20 digits (numbers only)'
    return None


def validate_acc_name(value):
    value = str(value).strip() if value is not None else ''
    if not value:
        return 'User name is required'
    if not _ACC_NAME_RE.match(value):
        return 'User name must be 2-50 letters (English or Myanmar) and spaces only'
    return None