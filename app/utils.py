import math
from datetime import datetime, timedelta
from app import app, db, CustomObject, client, keys
from sqlalchemy.sql import func
from sqlalchemy import orm
from sqlalchemy.orm import session, query
from sqlalchemy import func, extract
from app.models import *
from flask_login import current_user
from flask import session, request, url_for
import hashlib
from fpdf import FPDF
from os import path

################### lấy thông tin từ id, phone #############


def get_medicine_by_id(medicine_id):    #lấy tên thuốc bằng id của thuốc
    return Medicine.query.get(medicine_id).name


def get_user_by_id(user_id):    #lấy thông tin user dùng cho xử lý đăng nhập
    return User.query.get(user_id)


def get_user_information():
    return get_user_by_id(current_user.id)


def get_medical_bill_by_id(medical_bill_id):
    return MedicalBill.query.get(medical_bill_id)


def get_receipt_by_id(receipt_id):
    return Receipt.query.get(receipt_id)

def get_customer_sche_information(customer_sche_id):
    return CustomerSche.query.filter(CustomerSche.id == customer_sche_id).first()


def get_schedule_information(schedule_id):
    return Schedule.query.get(schedule_id)


def see_receipt(receipt_id):
    return Receipt.query.get(receipt_id)


def get_medicine_in_medical_bill(medical_bill_id):
    return MedicalBillDetail.query.filter(MedicalBillDetail.medical_bill == medical_bill_id).all()


def tim_khach_hang(sdt, **kwargs):
    return Customer.query.filter(Customer.phone_number.__eq__(sdt)).first()


def get_medicine_by_name(name):
    return Medicine.query.filter(Medicine.name.__eq__(name)).first()


################### TRANG INDEX ###############################

def check_password(username, password):          #kiểm tra mật khẩu, tài khoản trên database
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


def check_real_information(user_id):
    user_all = User.query.all()
    for us in user_all:
        if user_id.__eq__(us.id):
            return True
    return False

def reformat_phone_number(phone_number):
    if phone_number[:1] == '84' and len(phone_number) == 11:
        return '+' + phone_number
    elif phone_number[0] == '0' and len(phone_number) == 10:
        return '+84' + phone_number[1:]
    else:
        return 0


def reformat_0_phone_number(phone_number):
    if phone_number[0] == '0' and len(phone_number) == 10:
        return phone_number
    elif phone_number[:1] == '84' and len(phone_number) == 11:
        return '0' + phone_number[2:]
    else:
        return 0


def send_messages(to_phone, content):
    to_phone = reformat_phone_number(to_phone)
    if to_phone != '' and content !='':
        message = client.messages.create(
            body=content,
            from_=keys['twilio_number'],
            to=to_phone)


def get_customer_by_phone(phone_number):
    return Customer.query.filter(Customer.phone_number.__eq__(phone_number)).order_by(Customer.id.desc()).first()


def get_accepted_customer_by_phone(phone_number): ################################
    return db.session.query(Customer).filter(Customer.phone_number == phone_number, Customer.id == Receipt.customer_id,
                                             Receipt.medical_bill == MedicalBill.id).order_by(Customer.appointment_date.
                                                                                              desc()).first()


def get_customer_by_id(customer_id):
    return Customer.query.get(customer_id)


def get_id_of_date_exist_in_schedule(in_date):
    if in_date is datetime:
        in_date = in_date.date()
    dates = db.session.query(Schedule.id).filter(Schedule.examination_date == in_date).\
        order_by(Schedule.examination_date.desc()).first()
    if dates:
        returned_id = dates.id
    if not dates:
        new_schedule = Schedule(examination_date=datetime(in_date.year, in_date.month, in_date.day, 0))
        db.session.add(new_schedule)
        db.session.commit()
        returned_id = new_schedule.id

    return returned_id


def add_new_order(first_name, last_name, birthday, phone_number, gender_id, appointment_date, note):
    # #new Schedule or not
    # schedule_id = get_id_of_date_exist_in_schedule(ordered_date.date())
    c = tim_khach_hang(phone_number)
    if c:
        c.appointment_date = appointment_date
        c.was_scheduled = False
        db.session.add(c)
    else:
        #order in Customer
        customer = Customer(first_name=first_name, last_name=last_name, birthday=birthday, phone_number=phone_number,
                            gender_id=gender_id, appointment_date=appointment_date, note=note)
        db.session.add(customer)
    db.session.commit()

    #customer schedule
    # customer_sche = CustomerSche(schedule_id=schedule_id, customer_id=customer.id, timer=time(ordered_date.hour,
    #                                                                                           ordered_date.minute,
    #                                                                                           ordered_date.second))
    # db.session.add(customer_sche)
    # db.session.commit()


def get_order_history(phone_number):
    return db.session.query(Customer).filter(Customer.phone_number == phone_number).all()


def get_bill_history(phone_number):
    return_value = []
    joined_order_customer = db.session.query(MedicalBill.id).filter(Customer.phone_number == phone_number, Customer.id
                                                                    == Receipt.customer_id, Receipt.medical_bill ==
                                                                    MedicalBill.id).all()
    if joined_order_customer:
        for obj in range(len(joined_order_customer)):
            return_value.append(joined_order_customer[obj][0])   #[bill_id_1, bill_id_2, bill_id_3]

    return return_value

def get_customer_phone_list():
    customers = db.session.query(Customer.phone_number).group_by(Customer.phone_number).all()
    list_cutted_phone_number = []
    for customer in customers:
        list_cutted_phone_number.append(str(customer)[-7:-3])
    return list_cutted_phone_number

def get_history_look_up(phone_number):
    orders_history = []
    main_info = get_order_history(phone_number)
    if main_info:
        orders = main_info[0].receipts
        if orders:
            for order in orders:
                new_obj = CustomObject.CustomObjectHistoryMedicalBill()
                new_obj.name = main_info[0].first_name + ' ' + main_info[0].last_name
                new_obj.ordered_date = get_medical_bill_by_id(order.medical_bill).symptom
                new_obj.disease_diagnostic = get_medical_bill_by_id(order.medical_bill).diagnostic_disease
                new_obj.order_state = True
                new_obj.was_scheduled = main_info[0].was_scheduled

                orders_history.append(new_obj)
    return orders_history

def rounded_time(date_time): #10 minutes for each order time
    hour = date_time.hour
    minute = date_time.minute
    if minute < 55:
        math_minute = minute % 10
        if math_minute < 5:
            minute -= math_minute
        else:
            minute += 10 - math_minute
    else:
        return date_time + timedelta(hours=+1, minutes=-minute)

    return date_time.replace(hour=hour, minute=minute)


def get_sat_in_date(date):
    if date is datetime:
        date = date.date()
    return_value = []
    list_order = db.session.query(CustomerSche.timer).filter(CustomerSche.schedule_id == Schedule.id).\
        filter(extract('day', Schedule.examination_date) == date.day, extract('month', Schedule.examination_date) ==
               date.month, extract('year', Schedule.examination_date) == date.year).order_by(CustomerSche.timer)\
        .all()
    if list_order:
        for item in list_order:
            return_value.append(item[0])
    return return_value      #[time1, time2, time3,...] in the same date


def get_date_from_to(from_date, to_date):
    if from_date is datetime:
        from_date = from_date.date()
    if to_date is datetime:
        to_date = to_date.date()
    if from_date >= to_date:
        return from_date

    list_date = []
    while from_date != to_date:
        list_date.append(from_date)
        from_date = from_date + timedelta(days=+1)
    return list_date


def get_not_free_order_time():
    #js checked khung ngày giờ còn trống trong khoảng 1.5 ngày tính từ (now + 1/24) ngày, không đăng ký vào break time
    #min (+ 1.5) ||||||| max (36 -) (hours)
    #check in 37 hours for time loss reservation
    current_date_time_seconds = datetime.now().timestamp()
    from_date_time = datetime.fromtimestamp(current_date_time_seconds + 1.5 * 60 ** 2)          #current + 1.5 hours
    to_date_time = datetime.fromtimestamp(current_date_time_seconds + 37 * 60 ** 2)             #current + 37 hours

    #date need to check
    from_date = from_date_time.date()
    to_date = to_date_time.date()
    list_date_need_to_check = get_date_from_to(from_date, to_date)

    #list free oder time (order sat)
    list_free_order_time = {}
    for date_check in list_date_need_to_check:

        list_date_not_free = get_sat_in_date(date_check.date())

        list_not_free = []

        count = 0
        list_length = len(list_date_not_free)
        while count in range(count, list_length):
            count_j = count + 1
            new_obj = CustomObject.CustomObjectTimeFree()
            new_obj.hour = list_date_not_free[count].hour
            new_obj.minute.append(list_date_not_free[count].minute)
            while count_j in range(count_j, list_length):
                if new_obj.hour == list_date_not_free[count_j].hour:
                    new_obj.minute.append(list_date_not_free[count_j].minute)
                    count_j += 1
                else:
                    if count_j - count > 1:
                        count = count_j - 2
                    break
            list_not_free.append(new_obj)
            count += 1

        list_free_order_time[date_check.strftime("%Y-%m-%d")] = list_not_free

    return list_free_order_time      #{key_date : [<obj1>,<obj2>,<obj3>,<obj4>,...]}   <obj1> = {hour=x, minute=[]}


def check_exist_order_at_date_time(date_time):
    list_orders = get_sat_in_date(date_time.date())
    for order in list_orders:
        if date_time.hour == order.hour and date_time.minute == order.minute:
            return True     #exist

    return False   #not exist


def check_customer_exist_on_date(date_time, phone_number):
    if date_time is datetime:
        date_time = date_time.date()
    check_exist = db.session.query(CustomerSche.timer).filter(Customer.phone_number == phone_number, CustomerSche.
                                                              customer_id == Customer.id, Schedule.id == CustomerSche.
                                                              schedule_id, Schedule.examination_date == date_time)\
        .first()

    if check_exist:
        return True   #exist
    return False      #not_exist


def session_clear(key):
     if key in session:
         del session[key]



################### ADMIN######################################
################# admin chung ###############################

def edit_user_information(user_id, first_name, last_name, birthday, phone_number, gender):
    user = get_user_by_id(user_id)
    user.first_name = first_name
    user.last_name = last_name
    user.birthday = birthday
    user.phone_number = phone_number
    #user.gender_id = gender
    db.session.add(user)
    db.session.commit()



################### MANAGER ##################################

def revenue_stats_by_day(month, year):  #Thống kê doanh thu mỗi ngày trong tháng
    p = db.session.query(extract('day', Receipt.created_date),
                         func.sum(Receipt.total_price))\
                        .filter(extract('month', Receipt.created_date) == month,
                                extract('year', Receipt.created_date) == year)\
                        .group_by(extract('day', Receipt.created_date))\
                        .order_by(extract('day', Receipt.created_date))

    return p.all()

def doanhthu(month, year):
    kq = 0
    hoadon = Receipt.query.filter(extract('month', Receipt.created_date) == month,
                                  extract('year', Receipt.created_date) == year).all()
    for h in hoadon:
        kq += h.total_price

    return kq

def revenue_stats(month, year, doanhthu):
    p = db.session.query(extract('day', Receipt.created_date), func.count(Customer.id),
                         func.sum(Receipt.total_price), (func.sum(Receipt.total_price)/doanhthu)*100)\
                        .join(Customer, Receipt.customer_id.__eq__(Customer.id))\
                        .filter(extract('month', Receipt.created_date) == month, extract('year', Receipt.created_date) == year)\
                        .group_by(extract('day', Receipt.created_date))\
                        .order_by(extract('day', Receipt.created_date))
    return p.all()


def create_list_of_months(present_month):     #lập danh sách những (6) tháng liền kề
    months = 6   #số tháng được tính
    list_of_months = []
    if present_month >= 6:  #những trường hợp tháng hiện tại qua tháng 6
        for mm in range(present_month, present_month-months, -1):
            list_of_months.append(mm)
    else:                    #những trường hợp tháng hiện tại chưa qua tháng 6
        for mm in range(present_month, 0, -1):
            list_of_months.append(mm)
        for mm in range(12, 12 - months + len(list_of_months), -1):
            list_of_months.append(mm)
    return list_of_months


def all_revenue_stats(month, year):    #Thống kê doanh thu tất cả trong tháng trong năm
    revenue_values = revenue_stats_by_day(month, year)
    amount = 0
    for value in revenue_values:
        amount += value[1]
    return amount


def get_all_amount_of_medicine():         #lấy số lượng thuốc đang tồn kho
    list_medicine = Medicine.query.all()
    amount = 0
    for medicine in list_medicine:
        amount += medicine.quantity
    return amount



def get_last_reg():
    all_reg = Regulation.query.all()
    for reg in all_reg[::-1]:
        return reg.id


def get_regulation():
    value = []
    primary = Regulation.query.get(get_last_reg()) #primary đang sử dụng
    value.append(primary.customer_quantity)
    value.append(primary.examination_price)
    return value


def get_present_regulation():
    return Regulation.query.get(get_last_reg())

def get_amount_orders_in_date(date):
    all_in_date = get_auth_orders(date)
    count = 0
    for order in all_in_date:
        count += 1
    return count


def medine_stock_percent_over_5():             #lấy danh sách phần trăm thuốc trong tổng dưới dạng [id, percent, ..., 'OTHER', percent]
    list_medicine = db.session.query(Medicine.id, Medicine.quantity)\
            .order_by(-Medicine.quantity).all()
    max_quantity = get_all_amount_of_medicine()
    list_off = []
    count = 0
    for medicine in list_medicine:        #tính toán đưa ra những giá trị hơn 5% và ghi vào list
        if medicine.quantity / max_quantity * 100 >= 5:
            list_off.append(medicine.id)
            list_off.append(medicine.quantity)
            count += medicine.quantity
    list_off.append('OTHER')
    list_off.append(max_quantity - count)
    return list_off


def examination_stats(month, year):
    p = db.session.query(extract('day', Schedule.examination_date), func.count(CustomerSche.customer_id))\
                        .join(Customer, CustomerSche.customer_id.__eq__(Customer.id))\
                        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
                        .filter(CustomerSche.examined == True, extract('month', Schedule.examination_date) == month,
                                extract('year', Schedule.examination_date) == year)\
                        .group_by(extract('day', Schedule.examination_date))\
                        .order_by(extract('day', Schedule.examination_date))
    return p.all()


def medicine_stats(month,year):
    return Medicine.query.join(MedicalBillDetail, MedicalBillDetail.medicine.__eq__(Medicine.id))\
        .join(MedicalBill, MedicalBillDetail.medical_bill.__eq__(MedicalBill.id))\
        .join(Receipt, Receipt.medical_bill.__eq__(MedicalBill.id))\
        .filter(extract('month', Receipt.created_date) == month, extract('year', Receipt.created_date) == year)\
        .add_columns(func.sum(MedicalBillDetail.quantity)).add_columns(func.count(MedicalBillDetail.medicine))\
        .order_by(Medicine.id).group_by(Medicine.id).all()


def medicine_fill():
    return Medicine.query.filter(Medicine.quantity>0, Medicine.quantity<10).all()


def medicine_out_of_stock():
    return Medicine.query.filter(Medicine.quantity==0)


def medicine_in_stock():
    medicines = Medicine.query.all()
    q = 0
    for m in medicines:
        q += m.quantity
    return q


def used_medicine():
    medicals = MedicalBillDetail.query.all()
    q = 0
    for m in medicals:
        q += m.quantity
    return q

def thuoc_bo_sung():
    return Medicine.query.filter(Medicine.quantity > 0, Medicine.quantity < 10).all()


def thuoc_het_sl():
    return Medicine.query.filter(Medicine.quantity == 0)


def thuoc_ton_kho():
    medicines = Medicine.query.all()
    q = 0
    for m in medicines:
        q += m.quantity
    return q


def thuoc_da_dung():
    medicals = MedicalBillDetail.query.all()
    q = 0
    for m in medicals:
        q += m.quantity
    return q


def luot_kham(date):
    customers = [0, 0, 0]
    #Số lượt khám tối đa
    customers[0] = Regulation.query.filter(extract('day', Regulation.created_date).__le__(date)).all()[-1].customer_quantity
    # Số lượt khám đã hẹn
    customers[1] = len(CustomerSche.query.join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
                                .filter(Schedule.examination_date.__eq__(date)).all())
    #Số lượt khám còn lại
    customers[2] = (customers[0] - customers[1])
    return customers


####################### DOCTOR #############################


def KiemTraRole(user):
    return str(user.user_role)


def LichHenNgay(date):
    return Customer.query.join(CustomerSche, CustomerSche.customer_id.__eq__(Customer.id))\
        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
        .filter(Schedule.examination_date.__eq__(date)).order_by(CustomerSche.timer)\
        .add_columns(CustomerSche.timer).all()


def BenhNhanHienTai(date):
    return Customer.query.join(CustomerSche, CustomerSche.customer_id.__eq__(Customer.id)) \
        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id)) \
        .filter(Schedule.examination_date.__eq__(date), CustomerSche.examined == False)\
        .add_columns(CustomerSche.timer).order_by(CustomerSche.timer).first()


def ThongKeBenhNhan(date):
    customers = [0, 0, 0]
    # Số bênh nhân
    customers[0] = len(CustomerSche.query.join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
                       .filter(Schedule.examination_date.__eq__(date)).all())
    # Số bênh nhân đã khám
    customers[1] = len(CustomerSche.query.join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
                       .filter(Schedule.examination_date.__eq__(date), CustomerSche.examined == True).all())
    # Số bệnh nhân chưa khám
    customers[2] = (customers[0] - customers[1])
    return customers


def DanhSachBenhNhan(date):
    return Customer.query.join(CustomerSche, CustomerSche.customer_id.__eq__(Customer.id))\
        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
        .filter(Schedule.examination_date.__eq__(date)).add_columns(Schedule.examination_date)\
        .order_by(CustomerSche.timer).all()


def ThongKeLichHen(date):
    customers = [0, 0, 0]
    # Số khách hàng
    customers[0] = len(CustomerSche.query.join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
                       .filter(Schedule.examination_date.__eq__(date)).all())
    # Số bênh nhân đã được xác nhận lịch hẹn
    customers[1] = len(Customer.query.join(Schedule, Customer.id.__eq__(Schedule.id))\
                       .filter(Schedule.examination_date.__eq__(date), Customer.was_scheduled == True).all())
    # Số bệnh nhân chưa được xác nhận
    customers[2] = (customers[0] - customers[1])
    return customers

def lich_su_kham(customer_id, medical_id=None):
    if medical_id:
        return MedicalBill.query.join(CustomerSche, MedicalBill.customer_sche.__eq__(CustomerSche.id))\
            .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id)).add_columns(Schedule.examination_date)\
            .join(Customer, CustomerSche.customer_id.__eq__(Customer.id))\
            .filter(MedicalBill.id.__eq__(medical_id)).add_columns(Customer.first_name)\
            .add_columns(Customer.last_name).add_columns(extract('year', Customer.birthday)).all()
    else:
        return MedicalBill.query.join(CustomerSche, MedicalBill.customer_sche.__eq__(CustomerSche.id)).\
            join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id)).add_columns(Schedule.examination_date)\
            .join(Customer, CustomerSche.customer_id.__eq__(Customer.id))\
            .filter(CustomerSche.customer_id.__eq__(customer_id)).add_columns(Customer.first_name)\
            .add_columns(Customer.last_name).add_columns(extract('year', Customer.birthday)).group_by(MedicalBill.id)\
            .order_by(MedicalBill.id).all()


def add_medical_bill(cs, medicalinfo, medicinebilldetails):
    medicalbill = MedicalBill(user=current_user, symptom=medicalinfo['trieuchung'],
                              diagnostic_disease=medicalinfo['benhchuandoan'], customer_sche=cs.id)
    db.session.add(medicalbill)
    db.session.commit()
    for m in medicinebilldetails.values():
        mbd = MedicalBillDetail(medicalbill=medicalbill, medicine=m['id'], quantity=m['quantity'],
                                how_to_use=m['how_to_use'], unit_price=int(m['quantity'])*int(m['price']))
        db.session.add(mbd)
    db.session.commit()
    update_medicine(medicalbill.id)
    return update_customersche(medicalbill.id)

def update_customersche(id):
    c = CustomerSche.query.join(MedicalBill, MedicalBill.customer_sche.__eq__(CustomerSche.id)) \
        .filter(MedicalBill.id.__eq__(id)).first()
    c.examined = True
    db.session.add(c)
    db.session.commit()
    return c

def update_medicine(id):
    medical_bill = MedicalBill.query.get(id)
    for m in medical_bill.details:
        me = Medicine.query.get(m.medicine)
        me.quantity = me.quantity - m.quantity
        db.session.add(me)
    db.session.commit()


def get_customersche(customer_id, date):
    return CustomerSche.query.join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
        .filter(Schedule.examination_date == date, CustomerSche.customer_id.__eq__(customer_id)).first()

def cancel_medicalbill(customer_id, date):
    c = CustomerSche.query.join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
        .filter(CustomerSche.customer_id.__eq__(customer_id), Schedule.examination_date.__eq__(date)).first()
    c.examined = True
    db.session.add(c)
    db.session.commit()
    return c

##################### NURSE ###############################

def get_auth_orders(date):
    return db.session.query(Schedule.id).filter(extract('year', Schedule.examination_date) == date.year,
                                                extract('month', Schedule.examination_date) == date.month,
                                                extract('day', Schedule.examination_date) == date.day).all()

#tra cứu khách hàng bác sĩ và nurse
def load_customers(name=None, phone=None, codeMedicalBill=None, address=None):
    kq = {}
    if name:
        for p in Customer.query.all():
            if p.first_name.strip().__eq__(name.strip()):
                return p
    if phone:
        for p in Customer.query.all():
            if p.phone_number.strip().__eq__(phone.strip()):
                return p
    if codeMedicalBill:
        for p in MedicalBill.query.all():
            if p.id.strip().__eq__(codeMedicalBill.strip()):
                return p
    if address:
        for p in Customer.query.all():
            if p.address_id.strip().__eq__(address.strip()):
                return p


#lịch hẹn hiện tại
def customersche_now(date):
    return Customer.query.join(CustomerSche, CustomerSche.customer_id.__eq__(Customer.id))\
        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id))\
        .filter(CustomerSche.timer.__ge__(date.time()), Schedule.examination_date.__eq__(date.date()))\
        .add_column(Schedule.examination_date).add_column(CustomerSche.timer).first()

def load_sche(date):
    return Customer.query.join(CustomerSche, Customer.id.__eq__(CustomerSche.customer_id)) \
        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id)).filter(Schedule.examination_date.__eq__(date))\
        .order_by(CustomerSche.timer).all()


#danh sách khách đã được xác nhận lịch hẹn-y tá
def list_cus_was_sche(check_date):
    if check_date is datetime:
        check_date = date.date()
    return db.session.query(Schedule.examination_date, Customer).filter(Schedule.examination_date == check_date,
                                                                        Schedule.id == CustomerSche.schedule_id,
                                                                        CustomerSche.customer_id == Customer.id,
                                                                        Customer.was_scheduled.__eq__(True)).all()



#danh sách khách chưa được xác nhận lịch hẹn-y tá
def list_cus_wasnt_axam(date):
    return Customer.query.filter(extract('year', Customer.appointment_date) == date.year,
                                 extract('month', Customer.appointment_date) == date.month,
                                 extract('day', Customer.appointment_date) == date.day,
                                 Customer.was_scheduled == False)\
        .order_by(Customer.appointment_date).all()


#tìm khách hàng chưa dc xác nhận lịch hẹn
def search_customer_not_sche(date, phone_number):
    return Customer.query.join(CustomerSche, CustomerSche.customer_id.__eq__(Customer.id))\
        .filter(Customer.phone_number.__eq__(phone_number), Customer.was_scheduled == False,
                extract('year', Customer.appointment_date) == date.year,
                extract('month', Customer.appointment_date) == date.month,
                extract('day', Customer.appointment_date) == date.day).first()


def confirm_sche():
    confirm = Customer.was_scheduled('True')
    cus_sche = db.session.query(CustomerSche).filter(CustomerSche.customer_id == Customer.id).first()
    sche = str((get_schedule_information(cus_sche.schedule_id)).examination_date)
    timer = str(cus_sche.timer)
    #############send_messages(Customer.phone_number, "Lịch đặt hẹn khám của quý khách đã được xác nhận. Quý khách xin vui
    #lòng đến khám vào lúc " + sche + ' ' + timer)
    db.session.add(confirm)
    db.session.commit()


def add_customer_sche(customer_id,schedule_id, timer):
    c = CustomerSche(customer_id=customer_id, schedule_id=schedule_id, timer=timer)
    db.session.add(c)
    Customer.query.get(customer_id).was_scheduled=True
    db.session.commit()
    return c

def get_schedule_by_date(date):
    return Schedule.query.filter(Schedule.examination_date.__eq__(date)).first()

def add_schedule(date):
    s = Schedule(examination_date=date)
    db.session.add(s)
    db.session.commit()
    return s

def cancel_customersche(id):
    date = Customer.query.get(id).appointment_date
    Customer.query.get(id).appointment_date = datetime(date.year, date.month, date.day+1, 0)
    db.session.commit()
    return Customer.query.get(id)


#Tạo lịch hẹn mới trên gd y tá
def add_new_appointment(first_name, last_name, birthday, phone_number, gender_id, appointment_date, note):
    c = tim_khach_hang(phone_number)
    if c:
        c.appointment_date = appointment_date
        c.was_scheduled = False
        db.session.add(c)
    else:
        customer = Customer(first_name=first_name, last_name=last_name, birthday=birthday, phone_number=phone_number,
                            gender_id=gender_id, appointment_date=appointment_date, note=note)
        db.session.add(customer)
    db.session.commit()

#Hàm sắp xêp lịch hẹn khách hàng
def sorted_schedule(date):
    return Customer.query.join(CustomerSche, Customer.id.__eq__(CustomerSche.customer_id))\
        .join(Schedule, CustomerSche.schedule_id.__eq__(Schedule.id)) \
        .add_column(CustomerSche.timer)\
        .filter(Schedule.examination_date.__eq__(date)).order_by(CustomerSche.timer).all()


#lấy sô lượng đơn hẹn chưa xác nhận
def get_count_cus_wasnt_exam(date):
    all_in_date = list_cus_wasnt_axam(date)
    count = 0
    for order in all_in_date:
        count += 1
    return count

#lấy sô lượng đơn hẹn đã xác nhận
def get_count_cus_was_exam(date):
    count_sche = list_cus_was_sche(date)
    count = 0
    for order in count_sche:
        count += 1
    return count

def display_address(list):
    s = []
    for l in list:
        s.append(str(Address.query.get(Customer.query.get(l[0].id).address_id)))

    return s

def KiemTra(sche):
    return CustomerSche.query.filter(CustomerSche.schedule_id.__eq__(sche.id)).count()

def get_info_next_customer_in_orders():       #return the next customer will examine
    #just be in present date
    present_date = datetime.now().date()
    un_completed_order = db.session.query(CustomerSche).filter(CustomerSche.schedule_id == Schedule.id,
                                                               Schedule.examination_date == present_date,
                                                               CustomerSche.examined.__eq__(False)).first()
    if un_completed_order:
        return un_completed_order
    return None


def get_orders_list_in_date(check_date):         #return list orders in a date by [(customer_id, date, time)]
    if check_date is datetime:
        check_date = check_date.date()
    return db.session.query(Customer.id, Schedule.examination_date, CustomerSche.timer).\
        filter(Schedule.examination_date == check_date, Schedule.id == CustomerSche.schedule_id,
               Customer.id == CustomerSche.customer_id).all()


def get_orders_need_to_checkout(): #if customers pass their turns, was_schedule from True to False
    list_orders = db.session.query(Customer.id, MedicalBill.id).filter(Customer.id == CustomerSche.customer_id,
                                                       CustomerSche.schedule_id == Schedule.id,
                                                    CustomerSche.examined .__eq__(True),
                                                    Customer.was_scheduled.__eq__(True),
                                                       MedicalBill.customer_sche == CustomerSche.id).all()

    need_list = []

    if list_orders:
        for order in list_orders:
            if not db.session.query(Receipt).filter(order[0] == Receipt.customer_id, order[1] == Receipt.medical_bill)\
                    .all():
                need_list.append(order)

    return need_list


def add_new_receipt(regulation_id, medical_bill_id, customer_id):
    new_receipt = Receipt(total_price=get_total_price_in_receipt(medical_bill_id)[0], regulation=regulation_id,
                          medical_bill=medical_bill_id, customer_id=
                          customer_id, user_id=current_user.id)
    db.session.add(new_receipt)
    db.session.commit()
    return True


################################ XUẤT PDF ###########################


def get_total_price_in_receipt(medical_bill_id):
    price = []

    info = get_medicine_in_medical_bill(medical_bill_id)
    regulation = get_present_regulation()

    medical_price = regulation.examination_price
    medicine_price = 0
    tax_and_fee = 0

    for inf in info:
        medicine_price += inf.quantity * inf.unit_price

    total_price = medical_price + medicine_price
    tax_and_fee = 0.1 * total_price
    total_price += tax_and_fee

    price.append(total_price)
    price.append(medical_price)
    price.append(medicine_price)
    price.append(tax_and_fee)

    return price #[total_price, medical_price, medicine_price, tax_and_fee]


def format_currency_vi(list_cur):
    if list_cur:
        list_temp = []
        for value in list_cur:
            value = format(int(value), ',')
            list_temp.append(value)
    return list_temp


def get_receipt_history(phone_number):
    customers = Customer.query.filter(Customer.phone_number == phone_number).all()   #tên
    list_re = []
    if customers:
        for customer in customers:
            new_obj = CustomObject.CustomObjectReceiptHistory()

            #họ tên
            new_obj.name = customer.first_name + ' ' + customer.last_name

            #ngày, tiền
            receipt = db.session.query(Receipt).filter(Receipt.customer_id == customer.id).first()
            if receipt:
                new_obj.created_date = receipt.created_date
                new_obj.total = receipt.total_price
            else:
                return None

            #bác sĩ là ai, triệu chứng, chẩn đoán
            medical_bill = get_medical_bill_by_id(receipt.medical_bill)
            doctor = get_user_by_id(medical_bill.user_id)
            new_obj.doctor = doctor.first_name + ' ' + doctor.last_name
            new_obj.disease = medical_bill.diagnostic_disease
            new_obj.symptom = medical_bill.symptom

            #thuốc gì
            medicine_string = ''
            medicines = get_medicine_in_medical_bill(medical_bill.id)
            if medicines:
                for med in medicines:
                    medicine_string += get_medicine_by_id(med.medicine) + " SL: " + str(med.quantity) + ' '
            else:
                medicine_string = "Trống"
            new_obj.medicine = medicine_string

            list_re.append(new_obj)
    return list_re


def pdf_create_receipt(medical_bill_id):
    #data
    customer = db.session.query(Customer, Schedule, CustomerSche).filter(CustomerSche.customer_id == Customer.id,
                                                                         CustomerSche.id == MedicalBill.customer_sche,
                                                                         MedicalBill.id == medical_bill_id,
                                                                         Schedule.id == CustomerSche.schedule_id)\
        .first()
    this_customer_name = customer[0].first_name + ' ' + customer[0].last_name
    this_schedule_time = str(customer[1].examination_date) + ' ' + str(customer[2].timer)

    amount_money = format_currency_vi(get_total_price_in_receipt(medical_bill_id))
    total = amount_money[0]
    medical_price = amount_money[1]
    medicine_price = amount_money[2]

    data = [
        "HÓA ĐƠN THANH TOÁN",
        "Họ tên: ", "Ngày khám: ",
        "Tiền khám ", "Tiền thuốc: ",
        "Tổng tiền: "
    ]

    col = [47.5, 47.5, 47.5, 47.5]
    # coding: utf8

    pdf = FPDF(orientation='landscape', format='A5')
    pdf.add_page()
    pdf.add_font("Arial", "", "c:\\Windows\\fonts\\arial.ttf", uni=True)
    pdf.set_font("Arial", size=13)
    line_height = pdf.font_size * 2.5
    pdf.cell(col[0] + col[1] + col[2] + col[3], line_height, data[0], ln=True, border=1, align="C")
    pdf.cell(col[0] + col[1], line_height, data[1] + this_customer_name, border=1, align="L")
    pdf.cell(col[2] + col[3], line_height, data[2] + this_schedule_time, border=1, align="L")
    pdf.ln(line_height)
    pdf.cell(col[0] + col[1], line_height, data[3] + medical_price, border=1, align="L")
    pdf.cell(col[2] + col[3], line_height,  data[4] + medicine_price, border=1, align="L")
    pdf.ln(line_height)
    pdf.cell(col[0] + col[1] + col[2] + col[3], line_height, data[5] + total, border=1, align="L")
    pdf.output(path.dirname(path.abspath(__file__)) +
               url_for('static', filename='export/receipt.pdf'))


def pdf_create_examine_list_in_date(date_check):        #danh sách khám bệnh
    if date_check is datetime:
        date_check = date_check.date()
    #data
    data_list = []     #[ [hoten, gioitinh, namsinh, diachi] ,    ]


    data = [
        "DANH SÁCH KHÁM BỆNH",
        "Ngày khám: ",
        "STT: ", "Họ tên", "Giới tính", "Năm sinh", "Địa chỉ"
    ]

    col = [11.875, 71.25, 35.625, 35.625, 35.625]
    # coding: utf8

    pdf = FPDF(orientation='landscape', format='A5')
    pdf.add_page()
    pdf.add_font("Arial", "", "c:\\Windows\\fonts\\arial.ttf", uni=True)
    pdf.set_font("Arial", size=13)
    line_height = pdf.font_size * 2.5
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[0], ln=True, border=1, align="C")
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[1], ln=True, border=1, align="C")
    pdf.cell(col[0], line_height, data[2], border=1, align="C")
    pdf.cell(col[1], line_height, data[3], border=1, align="C")
    pdf.cell(col[2], line_height, data[4], border=1, align="C")
    pdf.cell(col[3], line_height, data[5], border=1, align="C")
    pdf.cell(col[4], line_height, data[6], border=1, align="C")
    pdf.ln(line_height)
    count = 0
    if data_list:
        for customer in data_list:
            count += 1
            pdf.cell(col[0], line_height, str(count), border=1, align="C")
            pdf.cell(col[1], line_height, str(customer[0]), border=1, align="L")
            pdf.cell(col[2], line_height, str(customer[1]), border=1, align="C")
            pdf.cell(col[3], line_height, str(customer[2]), border=1, align="C")
            pdf.cell(col[4], line_height, str(customer[3]), border=1, align="L")
            pdf.ln(line_height)

    pdf.output(path.dirname(path.abspath(__file__)) +
               url_for('static', filename='export/examination_list.pdf'))


def pdf_create_medical_bill(medical_bill_id):
    medical_bill = get_medical_bill_by_id(medical_bill_id)
    customer_sche = db.session.query(CustomerSche).filter(medical_bill.customer_sche == CustomerSche.id).first()
    schedule = db.session.query(Schedule).filter(customer_sche.schedule_id == Schedule.id).first()
    customer = db.session.query(Customer).filter(customer_sche.customer_id == Customer.id).first()

    # [(thuốc, đơn vị, số lượng, cách dùng), (thuốc, đơn vị, số lượng, cách dùng), ...]
    medicines = db.session.query(Medicine.name, Medicine.unit, MedicalBillDetail.quantity, MedicalBillDetail.how_to_use)\
        .filter(MedicalBillDetail.medical_bill == medical_bill_id, MedicalBillDetail.medicine == Medicine.id).all()

    this_customer_name = customer.first_name + " " + customer.last_name
    this_customer_schedule = str(schedule.examination_date) + ' ' + str(customer_sche.timer)


    data = [
        "PHIẾU KHÁM BỆNH",
        "Họ tên: ", "Ngày khám: ",
        "Triệu chứng: ", "Dự đoán loại bệnh: "
        "STT: ", "Thuốc", "Đơn vị", "Số lượng", "Cách dùng"
    ]

    col = [11.875, 71.25, 35.625, 35.625, 35.625]
    # coding: utf8

    pdf = FPDF(orientation='landscape', format='A5')
    pdf.add_page()
    pdf.add_font("Arial", "", "c:\\Windows\\fonts\\arial.ttf", uni=True)
    pdf.set_font("Arial", size=13)
    line_height = pdf.font_size * 2.5
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[0], ln=True, border=1, align="C")
    pdf.cell(95, line_height, data[1] + this_customer_name, border=1, align="L")
    pdf.cell(95, line_height, data[2] + this_customer_schedule, border=1, align="L")
    pdf.ln(line_height)
    pdf.cell(95, line_height, data[3] + medical_bill.symptom, border=1, align="L")
    pdf.cell(95, line_height, data[4] + medical_bill.diagnostic_disease, border=1, align="L")
    pdf.ln(line_height)

    count = 0
    if medicines:
        for medicine in medicines:
            count += 1
            pdf.cell(col[0], line_height, str(count), border=1, align="C")
            pdf.cell(col[1], line_height, str(medicine[0]), border=1, align="L")
            pdf.cell(col[2], line_height, str(medicine[1]), border=1, align="C")
            pdf.cell(col[3], line_height, str(medicine[2]), border=1, align="C")
            pdf.cell(col[4], line_height, str(medicine[3]), border=1, align="L")
            pdf.ln(line_height)

    pdf.output(path.dirname(path.abspath(__file__)) +
               url_for('static', filename='export/medical_bill.pdf'))


def pdf_month_revenue(year, month, data_list): # data_list = [('ngày', 'số bệnh nhân', 'int||float:Doanh thu', 'Tỷ lệ')]
    data = [
        "BÁO CÁO DOANH THU THEO THÁNG",
        "Tháng: ",
        "STT", "Ngày", "Số bệnh nhân", "Doanh thu", "Tỷ lệ",
        "Tổng doanh thu: "
    ]

    col = [11.875, 71.25, 35.625, 35.625, 35.625]
    # coding: utf8

    pdf = FPDF(orientation='landscape', format='A5')
    pdf.add_page()
    pdf.add_font("Arial", "", "c:\\Windows\\fonts\\arial.ttf", uni=True)
    pdf.set_font("Arial", size=13)
    line_height = pdf.font_size * 2.5
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[0], ln=True, border=1, align="C")
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[1] + str(year) + '/' + str(month),
             ln=True, border=1, align="C")
    pdf.cell(col[0], line_height, data[2], border=1, align="C")
    pdf.cell(col[1], line_height, data[3], border=1, align="C")
    pdf.cell(col[2], line_height, data[4], border=1, align="C")
    pdf.cell(col[3], line_height, data[5], border=1, align="C")
    pdf.cell(col[4], line_height, data[6], border=1, align="C")
    pdf.ln(line_height)

    count = 0
    doanh_thu = 0
    if data_list:
        for data_child in data_list:
            count += 1
            pdf.cell(col[0], line_height, str(count), border=1, align="C")
            pdf.cell(col[1], line_height, str(data_child[0]), border=1, align="C")
            pdf.cell(col[2], line_height, str(data_child[1]), border=1, align="C")
            doanh_thu += data_child[2]
            pdf.cell(col[3], line_height, str(data_child[2]), border=1, align="C")
            pdf.cell(col[4], line_height, str(data_child[3]), border=1, align="C")
            pdf.ln(line_height)

    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[7] + str(doanh_thu), ln=True, border=1,
             align="L")
    pdf.output(path.dirname(path.abspath(__file__)) +
               url_for('static', filename='export/revenue_statistics.pdf'))


def get_medicine_usage_in_month(year, month):
    return db.session.query(Medicine.name, Medicine.unit, func.sum(MedicalBillDetail.quantity), func.count(
        MedicalBillDetail.medical_bill)).filter(Medicine.id == MedicalBillDetail.medicine,
                                                 MedicalBillDetail.medical_bill == MedicalBill.id,
                                                 MedicalBill.customer_sche == CustomerSche.id,
                                                 CustomerSche.schedule_id == Schedule.id,
                                                 extract('month', Schedule.examination_date) == month,
                                                 extract('year', Schedule.examination_date) == year)\
        .group_by(MedicalBillDetail.medicine).all()


def pdf_create_medicine_usage(year, month, data_list): #data_list = [(Thuoc, đơn vị tính, số lượng, số lần dùng), ...]
    data = [
        "BÁO CÁO SỬ DỤNG THUỐC",
        "Tháng: ",
        "STT", "Thuốc", "Đơn vị tính", "Số lượng", "Số lần dùng",
        "Tổng doanh thu: "
    ]

    col = [11.875, 71.25, 35.625, 35.625, 35.625]
    # coding: utf8

    pdf = FPDF(orientation='landscape', format='A5')
    pdf.add_page()
    pdf.add_font("Arial", "", "c:\\Windows\\fonts\\arial.ttf", uni=True)
    pdf.set_font("Arial", size=13)
    line_height = pdf.font_size * 2.5
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[0], ln=True, border=1, align="C")
    pdf.cell(col[0] + col[1] + col[2] + col[3] + col[4], line_height, data[1] + str(year) + '/' + str(month),
             ln=True, border=1, align="C")
    pdf.cell(col[0], line_height, data[2], border=1, align="C")
    pdf.cell(col[1], line_height, data[3], border=1, align="C")
    pdf.cell(col[2], line_height, data[4], border=1, align="C")
    pdf.cell(col[3], line_height, data[5], border=1, align="C")
    pdf.cell(col[4], line_height, data[6], border=1, align="C")
    pdf.ln(line_height)

    count = 0
    doanh_thu = 0
    if data_list:
        for data_child in data_list:
            count += 1
            pdf.cell(col[0], line_height, str(count), border=1, align="C")
            pdf.cell(col[1], line_height, str(data_child[0]), border=1, align="C")
            pdf.cell(col[2], line_height, str(data_child[1]), border=1, align="C")
            doanh_thu += data_child[2]
            pdf.cell(col[3], line_height, str(data_child[2]), border=1, align="C")
            pdf.cell(col[4], line_height, str(data_child[3]), border=1, align="C")
            pdf.ln(line_height)

    pdf.output(path.dirname(path.abspath(__file__)) +
               url_for('static', filename='export/medicine_usage.pdf'))





##############new #########################