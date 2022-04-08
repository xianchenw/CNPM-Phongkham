class CustomObjectHistoryMedicalBill:
    name = ''
    ordered_date = ''
    disease_diagnostic = ''
    order_state = ''
    was_scheduled = ''

    def __int__(self):
        self.name = ''
        self.ordered_date = ''
        self.disease_diagnostic = ''
        self.order_state = ''
        self.was_scheduled = ''


class CustomObjectTimeFree:
    hour = ''        #hour mark
    minute = []         #list free time in marked hour

    def __init__(self):
        self.hour = ''
        self.minute = []


class CustomObjectReceiptHistory:
    name = ''
    created_date = ''
    doctor = ''
    symptom = ''
    disease = ''
    medicine = ''
    total = ''

    def __init__(self):
        self.name = ''
        self.created_date = ''
        self.doctor = ''
        self.symptom = ''
        self.disease = ''
        self.medicine = ''
        self.total = ''
