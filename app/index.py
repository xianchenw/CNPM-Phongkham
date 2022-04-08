import cloudinary.uploader
import random
import flask
from app import CustomObject
from app import app, db, login, client, keys
from flask import render_template, url_for, request, redirect, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from datetime import date, time


######### load dùng user chung cả client và nhân viên ############
@login.user_loader
def user_load(user_id):
    user = utils.get_user_by_id(user_id=user_id)
    try:
        if user.user_role:
            return user
        else:
            return utils.get_customer_by_id(customer_id=user_id)
    except:
        return utils.get_customer_by_id(customer_id=user_id)


########## TRANG INDEX CLIENT ##############
@app.route('/')
def index():
    notification_code = request.args.get('notification_code')
    if not notification_code:
        notification_code = ''
    if current_user.is_authenticated:
        orders_history = utils.get_history_look_up(current_user.phone_number)
        return render_template('index.html', current_user=current_user, orders_history=orders_history,
                               notif=notification_code)
    else:
        customers_list = utils.get_customer_phone_list()
        return render_template('index.html', customers_list=customers_list, notif=notification_code)


@app.route('/api/login', methods=['POST'])
def customer_login():
    if request.method.__eq__('POST'):
        otp_code = session.pop('response', None)
        otp = str(request.form.get('otp_code'))
        if otp == otp_code:
            #get customer
            customer = utils.get_accepted_customer_by_phone(request.form['customerPhoneNumber'])
            if customer:
                login_user(user=customer)
                return redirect(url_for('index'))
            else:
                return redirect(url_for('index', notification_code='noSuccessReceipt'))
    return render_template('index.html', current_phone=request.form['customerPhoneNumber'], error_code="Mã xác thực không hợp lệ.")


@app.route("/api/otp-auth", methods=['POST'])
def otp_auth():
    if request.method.__eq__('POST'):
        otp_code = random.randrange(100000, 999999)
        if request.json:
            phone_number = request.json['phoneNumber']
            session.modified = True
            session['response'] = str(otp_code)
            print("======================== OTP la " + str(otp_code))
            ###########Enable this line to send OTP for customer validation########################
            message = utils.send_messages(phone_number, '[Phòng mạch Hồng Hiền Vy Tiến] Mã số xác thực của bạn là: ' + str(otp_code)
                                              + '. Xin vui lòng không chia sẻ mã số này cho ai khác kể cả nhân viên của phòng mạch.')
    return 'OK'


@app.route("/api/otp-auth-again", methods=['POST'])
def otp_auth_again():
    if request.method.__eq__('POST'):
        otp_code = random.randrange(100000, 999999)
        if request.json:
            utils.session_clear('response')
            session.modified = True
            session['response'] = str(otp_code)
            print("======================== AGAIN OTP la " + str(otp_code))
            phone_number = request.json['phoneNumber']
            ###########Enable this line to send OTP for again customer validation########################
            message = utils.send_messages(phone_number, '[Phòng mạch Hồng Hiền Vy Tiến] Mã số xác thực của bạn là: ' + str(otp_code)
                                              + '. Xin vui lòng không chia sẻ mã số này cho ai khác kể cả nhân viên của phòng mạch.')
    return 'OK'


@app.route("/api/add-new-order", methods=['get', 'post'])
@login_required
def new_order_from_client():
    if current_user.is_authenticated:
        if request.method.__eq__('POST'):
            first_name = current_user.first_name
            last_name = current_user.last_name
            birthday = current_user.birthday
            gender_id = current_user.gender_id
            phone_number = current_user.phone_number
            appointment_date = request.form.get('order-date')
            #New data
            note = str(request.form.get('customer-note'))
            schedules = utils.rounded_time(datetime.strptime(request.form.get('order-date'), '%Y-%m-%dT%H:%M'))
            print(phone_number)
            print(schedules)
            if not utils.check_customer_exist_on_date(schedules.date(), phone_number):
                if not utils.check_exist_order_at_date_time(schedules):
                    #commit to database
                    utils.add_new_order(first_name, last_name, birthday, phone_number, gender_id, appointment_date, note)
                    return redirect(url_for('index', notification_code='submitSuccess'))
                else:
                    return redirect(url_for('index', notification_code='ExistOne'))
            else:
                return redirect(url_for('index', notification_code='justOneADay'))
    return redirect(url_for('index', notification_code='none'))


@app.route("/api/logout", methods=['get', 'post'])
def customer_logout():
    logout_user()
    if session:
        utils.session_clear('response')
    return redirect(url_for('index'))


################## ADMIN VIEW ##############
####### admin chung #############
@app.route('/admin/sign-in', methods=['get', 'post'])
def signin():
    if current_user.is_authenticated:
        return redirect('/admin')
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = utils.check_password(username=username, password=password)
        if user:
            login_user(user=user)
            return redirect('/admin')
        else:
            err_msg = 'Tài khoản hoặc mật khẩu sai.'

    return render_template('admin/login.html', err_msg=err_msg, cur=current_user)


def add_new_regulation():
    max_customer = request.form.get('new_max_customer')
    medical_fee = request.form.get('new_fee')

    all_reg = db.session.query(Regulation).all()
    for reg in all_reg:
        reg.id = reg.id + 1
        db.session.add(reg)
    new = Regulation(id=1, examination_price=medical_fee, customer_quantity=max_customer)
    db.session.add(new)
    db.session.commit()

    return


@app.route("/admin/submit-change", methods=['get', 'post'])
def submit_change():
    if current_user.is_authenticated:
        if request.method.__eq__('POST'):
            id_access = utils.get_user_information().id
            user = utils.get_user_by_id(id_access)
            avatar = request.files.get('avatar')

            if avatar:
                res = cloudinary.uploader.upload(avatar)
                avatar_path = res['secure_url']
                user.avatar = avatar_path
                db.session.add(user)
                db.session.commit()
                return redirect("/admin/accountset")

            if request.form:
                user.first_name = request.form['first_name']
                user.last_name = request.form['last_name']
                user.birthday = request.form['birthday']
                user.phone_number = request.form['phone']
                user.gender_id = list(Gender)[int(request.form['gender']) - 1]

                db.session.add(user)
                db.session.commit()

        return redirect("/admin/accountset")


@app.route("/admin/submit-change-pass", methods=['get', 'post'])
def change_pass():
    if current_user.is_authenticated:
        if request.method.__eq__('POST'):
            user = utils.get_user_information()
            us = request.form.get('username')
            if us.__eq__(user.username):
                mode = 0
                user.password = str(hashlib.md5(request.form.get('new-pass').encode('utf-8')).hexdigest())
                db.session.add(user)
                db.session.commit()
    return redirect(url_for('accountset.__index__'))

####################### DOCTOR ###########################
@app.route("/admin/cancel-medicalbill", methods=['post'])
def cancel_medicalbill():
    data = request.json
    id = data.get('id')
    try:
        c = utils.cancel_medicalbill(id, date.today())
    except:
        return {'status': 404, 'msg': 'Lỗi'}

    return {'status': 201, 'msg':c.id}

@app.route("/admin/createmedicalbill/load-patient", methods=['post'])
def load_patient():
    data = request.json
    sdt = data.get('sdt')
    phieukham = data.get('phieukham')
    try:
        p = utils.tim_khach_hang(sdt=sdt)
    except:
        return {'status': 404, 'err_msg' :'Lỗi hệ thống'}

    if p:
        if str(p.gender_id).__eq__('Gender.NU'):
            gender = 'Nữ'
        else:
            if str(p.gender_id).__eq__('Gender.NAM'):
                gender = 'Nam'
            else:
                gender = 'Khác'

    return {'status': 201, 'patient': {
        'id': p.id,
        'first_name': p.first_name,
        'last_name': p.last_name,
        'age': datetime.now().year - p.birthday.year,
        'gender': gender,
        'phone_number': p.phone_number,
    }, 'phieukham': phieukham}

@app.route('/admin/createmedicalbill/add-medicine', methods=['post'])
def add_medicine_to_medical_bill():
    data = request.json
    medicine_name = data.get('medicine_name')
    medicine = session.get('medicine')
    try:
        m = utils.get_medicine_by_name(name=medicine_name)
    except:
        return {'status': 404, 'err_msg': 'Lỗi hệ thống !!'}

    if not medicine:
        medicine = {}

    if str(m.id) in medicine:
        medicine[str(m.id)]['quantity'] = int(medicine[str(m.id)]['quantity']) + 1
    else:
        medicine[str(m.id)] = {
            'id': m.id,
            'name': m.name,
            'quantity': 1,
            'how_to_use': '',
            'price': m.price
        }

    session['medicine'] = medicine

    return {'status': 201, 'medicine': medicine[str(m.id)]}

@app.route('/admin/createmedicalbill/delete-medicinebill-details', methods=['post'])
def del_medicinebill_details():
    try:
        del session['medicine']
    except:
        return jsonify({'code': 400})

    return jsonify({'code': 200})

@app.route('/admin/createmedicalbill/update/quantity', methods=['put'])
def update_medicine_quantity():
    data = request.json
    id = str(data.get('id'))
    quantity = data.get('quantity')
    medicine = session.get('medicine')
    if medicine and id in medicine:
        if int(quantity) <= Medicine.query.get(int(id)).quantity:
            medicine[id]['quantity'] = quantity
            session['medicine'] = medicine
            return {'status': 201}
        else:
            return {'status': 400, 'msg': 'Thuốc trong kho không đủ số lượng'}

    return {'status': 404}


@app.route('/admin/createmedicalbill/update/how-to_use', methods=['put'])
def update_how_to_use():
    data = request.json
    id = str(data.get('id'))
    how_to_use = data.get('how_to_use')
    medicine = session.get('medicine')
    if medicine and id in medicine:
        medicine[id]['how_to_use'] = how_to_use
        session['medicine'] = medicine
        return {'status': 201}

    return {'status': 404}

@app.route('/admin/createmedicalbill/delete-medicine', methods=['put'])
def delete_medicine():
    data = request.json
    id = str(data.get('id'))
    medicine = session.get('medicine')
    if medicine and id in medicine:
        del medicine[id]
        session['medicine'] = medicine
    else:
        return {'status': 404}

    return {'status': 201, 'medicine': medicine}

@app.route('/admin/createmedicalbill/create-medicalbill', methods=['post'])
def create_medical_bill():
    data = request.json
    try:
        medical_bill = session.get('medical_bill')
        medical_bill = {
            'ten': data.get('ten'),
            'sdt': data.get('sdt'),
            'tuoi': data.get('tuoi'),
            'gioitinh': data.get('gioitinh'),
            'phieukham': data.get('phieukham'),
            'trieuchung': data.get('trieuchung'),
            'benhchuandoan': data.get('benhchuandoan')
        }
        session['medical_bill'] = medical_bill
    except:
        return {'status': 404, 'err_msg': 'Lỗi hệ thống'}

    return {'status': 201, 'medical_bill': medical_bill}

@app.route('/admin/createmedicalbill/', methods=['post'])
def add_new_medicalbill():
    if request.method.__eq__('POST'):
        medicine = session.get('medicine')
        medical_bill = session.get('medical_bill')
        try:
            customer = utils.get_customer_by_phone(medical_bill['sdt'])
            customersche = utils.get_customersche(customer_id=customer.id, date=date.today())
            m = utils.add_medical_bill(cs=customersche, medicalinfo=medical_bill, medicinebilldetails=medicine)
            del session['medicine']
            del session['medical_bill']
        except:
            return jsonify({'code': 400})

        return jsonify({'code': 201, 'customersche': customersche.id,'m':m.id})

@app.context_processor
def common_response():
    return {
        'medicine': session.get('medicine'),
        'medical_bill': session.get('medical_bill')
    }


#########################NURSE ###########################
#tạo lịch hẹn mới trên trang y tá
@app.route("/add-new-appoinment", methods=['get', 'post'])
def new_orderCus():
    if current_user.is_authenticated:
        err_msg = ''
        if request.method.__eq__('POST'):
            first_name = request.form.get('customer-fname')
            last_name = request.form.get('customer-lname')
            birthday = request.form.get('customer-birth')
            gender_id = request.form.get('customer-gender')
            phone_number = request.form.get('customer-phone')
            appointment_date = request.form.get('order-date')
            note = str(request.form.get('customer-note'))
            schedules = utils.rounded_time(datetime.strptime(request.form.get('order-date'), '%Y-%m-%dT%H:%M'))
            print(phone_number)
            print(schedules)
            if not utils.check_customer_exist_on_date(schedules.date(), phone_number):
                if not utils.check_exist_order_at_date_time(schedules):
                    # commit to database
                    utils.add_new_appointment(first_name, last_name, birthday, phone_number, gender_id, appointment_date, note)
                    return redirect(url_for('new_order', err_msg='Đơn hẹn đã được đặt thành công'))
                else:
                    return redirect(url_for('new_order', err_msg='Thời gian hẹn của khách hàng bị trùng lịch hẹn. Vui lòng đăng ký hẹn thời điểm khác.'))
            else:
                return redirect(url_for('new_order', err_msg='Đơn hẹn ngày hôm nay của khách hàng đã được đặt. Trùng lịch hẹn.'))
        return redirect(url_for('new_order', err_msg=''))


@app.route("/new_order")
def new_order():
    return redirect('/admin/appoinments')


@app.route('/api/payment', methods=['get', 'post'])
def pay():
    if current_user.is_authenticated:
        if request.method.__eq__("POST"):
            medical_id = request.form['medical-bill-id']
            if medical_id:
                customer_id = utils.get_customer_sche_information(
                    utils.get_medical_bill_by_id(medical_id).customer_sche).customer_id
                regulation = utils.get_last_reg()

                utils.add_new_receipt(regulation_id=regulation, medical_bill_id=medical_id,
                                      customer_id=customer_id)
                utils.pdf_create_receipt(medical_bill_id=medical_id)
                return redirect('/admin/payment' + "?statusPayment=submitSuccess")
    return redirect('/admin/payment' + "?statusPayment=falseCheckout")


@app.route('/api/check-receipt', methods=['get', 'post'])
def check_receipt_history():
    if current_user.is_authenticated:
        if request.method.__eq__("POST"):
            phone_check = request.form['phone-check']
            list_re = utils.get_receipt_history(phone_check)
            if list_re:
                return render_template('/admin/receipt_history.html', phone_check=phone_check, list_re=list_re)
    return render_template('/admin/receipt_history.html')


@app.route('/admin/appoinments/confirm-customersche', methods=['put'])
def confirm_customer_sche():
    data = request.json
    id = data.get('id')

    timer = Customer.query.get(id).appointment_date.time()
    schedule = utils.get_schedule_by_date(Customer.query.get(id).appointment_date.date())
    if not schedule:
        schedule = utils.add_schedule(Customer.query.get(id).appointment_date.date())
    if utils.KiemTra(sche=schedule) < Regulation.query.all()[-1].customer_quantity:
        try:
            utils.add_customer_sche(id, schedule.id, timer)
        except:
            return {'status': 404}
    else:
        return {'status': 400, 'msg': 'Lịch hẹn của ngày đã đủ số lượng'}

    return {'status': 201, 'id': id}


@app.route('/admin/appoinments/cancel-customersche', methods=['put'])
def cancel_customer_sche():
    data = request.json
    id = data.get('id')
    try:
        utils.cancel_customersche(id)
    except:
        return {'status': 404}

    return {'status': 201, 'id': id}


if __name__ == '__main__':
    pre_user = None
    from admin import *
    app.run(debug=True)
