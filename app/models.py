from app import db, app
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Enum, ForeignKey, Time, Date
from sqlalchemy.orm import relationship, backref
from datetime import datetime, time, date
from enum import Enum as ENUM
from sqlalchemy.ext.declarative import declared_attr
from flask_login import UserMixin

class Gender(ENUM):
    NAM = 1
    NU = 2
    KHAC = 3

class Province(db.Model):
    __tablename__ = 'province'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    districts = relationship('District', backref='province', lazy=True)

    def __str__(self):
        return self.name


class District(db.Model):
    __tablename__ = 'district'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    wards = relationship('Ward', backref='district', lazy=True)
    province_id = Column(Integer, ForeignKey(Province.id), nullable=False)

    def __str__(self):
        return self.name + ', ' + str(Province.query.get(self.province_id))


class Ward(db.Model):
    __tablename__ = 'ward'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    addresss = relationship('Address', backref='ward', lazy=True)
    district_id = Column(Integer, ForeignKey(District.id), nullable=False)

    def __str__(self):
        return self.name + ', ' + str(District.query.get(self.district_id))


class Address(db.Model):
    __tablename__ = 'address'
    id = Column(Integer, primary_key=True, autoincrement=True)
    info = Column(String(50))
    ward_id = Column(Integer, ForeignKey(Ward.id), nullable=False)

    def __str__(self):
        return self.info + ', ' + str(Ward.query.get(self.ward_id))


class Person(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(10), nullable=False)
    last_name = Column(String(50))
    birthday = Column(DateTime, nullable=False)
    phone_number = Column(String(20), nullable=False)
    gender_id = Column(Enum(Gender))
    @declared_attr
    def address_id(self):
        return Column(Integer, ForeignKey(Address.id))


class UserRole(ENUM):
    MANAGER = 1
    DOCTOR = 2
    NURSE = 3


class User(Person, UserMixin):
    __tablename__ = 'user'
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    avatar = Column(String(100))
    join_date = Column(DateTime, default=datetime.now())
    active = Column(Boolean, default=True)
    user_role = Column(Enum(UserRole), nullable=False)
    medical_bills = relationship('MedicalBill', backref='user', lazy=True)
    receipts = relationship('Receipt', backref='user', lazy=True)


class Customer(Person, UserMixin):
    __tablename__ = 'customer'
    appointment_date = Column(DateTime, nullable=False) #ngày hẹn
    note = Column(String(100))
    was_scheduled = Column(Boolean, default=False)  #sau khi được xác nhận lịch hẹn -> True
    schedules = relationship('CustomerSche', backref='customers', lazy=True)
    receipts = relationship('Receipt', backref='customer', lazy='subquery')


class CustomerSche(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=False, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('schedule.id'), nullable=False, primary_key=True)
    examined = Column(Boolean, default=False)
    timer = Column(Time, nullable=False)
    medical_bill = relationship('MedicalBill', backref='customersche', lazy=True, uselist=False)


class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    examination_date = Column(Date, nullable=False)  #ngày khám đã xác nhận
    customers = relationship('CustomerSche', backref='schedules', lazy=True)


class MedicalBill(db.Model):
    __tablename__ = 'medical_bill'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symptom = Column(String(100))   #triệu chứng
    diagnostic_disease = Column(String(100))    #bệnh chuẩn đoán
    created_date = Column(DateTime, default=datetime.now())
    customer_sche = Column(Integer, ForeignKey(CustomerSche.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    details = relationship('MedicalBillDetail', backref='medicalbill', lazy=True)
    receipt = relationship('Receipt', backref='medicalbill', uselist=False, lazy=True)


class Producer(db.Model):
    __tablename__ = 'producer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    medicines = relationship('Medicine', backref='producer', lazy=True)

    def __str__(self):
        return self.name


class MedicineType(db.Model):
    __tablename__ = 'medicine_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(50))
    medicines = relationship('Medicine', backref='medicinetype', lazy=True)

    def __str__(self):
        return self.type_name


class Medicine(db.Model):
    __tablename__ = 'medicine'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    quantity = Column(Integer, default=0)
    unit = Column(String(20))
    price = Column(Float, default=0)
    out_of_date = Column(DateTime)
    producer_id = Column(Integer, ForeignKey('producer.id'))
    medicine_type = Column(Integer, ForeignKey('medicine_type.id'))
    medical_bill_details = relationship('MedicalBillDetail', backref='medicines', lazy=True)
    def __str__(self):
        return self.name


class MedicalBillDetail(db.Model):
    medical_bill = Column(Integer, ForeignKey('medical_bill.id'), nullable=False, primary_key=True)
    medicine = Column(Integer, ForeignKey('medicine.id'), nullable=False, primary_key=True)
    quantity = Column(Integer, default=0)
    how_to_use = Column(String(100))
    unit_price = Column(Float, default=0)


class Receipt(db.Model):
    __tablename__ = 'receipt'
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_price = Column(Float, default=0)
    created_date = Column(DateTime, default=datetime.now())
    regulation = Column(Integer, ForeignKey('regulation.id')) #quy định
    medical_bill = Column(Integer, ForeignKey('medical_bill.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)


class Regulation(db.Model):
    __tablename__ = 'regulation'
    id = Column(Integer, primary_key=True)
    examination_price = Column(Float, default=100000)
    customer_quantity = Column(Integer, default=30)
    created_date = Column(DateTime, default=datetime.now())
    receipts = relationship('Receipt', backref='regulations', lazy=True)


if __name__ == "__main__":
    # #Add adrress
    # p1 = Province(name='Hồ Chí Minh')
    # db.session.add(p1)
    #
    # d1 = District(name='Quận 1', province_id=1)
    # d2 = District(name='Quận 2', province_id=1)
    # db.session.add(d1)
    # db.session.add(d2)
    #
    # w1 = Ward(name='Phường 1', district_id=1)
    # w2 = Ward(name='Phường 2', district_id=1)
    # w3 = Ward(name='Phường 1', district_id=2)
    # w4 = Ward(name='Phường 2', district_id=2)
    # db.session.add(w1)
    # db.session.add(w2)
    # db.session.add(w3)
    # db.session.add(w4)
    #
    # a1 = Address(info='Âu Cơ', ward_id=1)
    # a2 = Address(info='Âu Cơ', ward_id=2)
    # a3 = Address(info='Âu Cơ', ward_id=3)
    # a4 = Address(info='Âu Cơ', ward_id=4)
    # a5 = Address(info='Hùng Vương', ward_id=1)
    # a6 = Address(info='Hùng Vương', ward_id=2)
    # a7 = Address(info='Hùng Vương', ward_id=3)
    # a8 = Address(info='Hùng Vương', ward_id=4)
    # db.session.add(a1)
    # db.session.add(a2)
    # db.session.add(a3)
    # db.session.add(a4)
    # db.session.add(a5)
    # db.session.add(a6)
    # db.session.add(a7)
    # db.session.add(a8)

    # #Add user
    # u1 = User(first_name='Hien', last_name='Tran', birthday=datetime(2001, 8, 6, 0), phone_number='0964345627',
    #           username='hien', password='202cb962ac59075b964b07152d234b70', user_role=UserRole.MANAGER, gender_id=Gender.NU)
    # u2 = User(first_name='Hong', last_name='Tran', birthday=datetime(2001, 7, 11, 0), phone_number='0912123321',
    #           username='hong', password='202cb962ac59075b964b07152d234b70', user_role=UserRole.DOCTOR, gender_id=Gender.NU)
    # u3 = User(first_name='Vi', last_name='Nguyen', birthday=datetime(2001, 11, 29, 0), phone_number='0987632121',
    #           username='vi', password='202cb962ac59075b964b07152d234b70', user_role=UserRole.NURSE, gender_id=Gender.NU)
    # db.session.add(u1)
    # db.session.add(u2)
    # db.session.add(u3)

    # #Add customer
    # c1 = Customer(first_name='Hien', last_name='Tran Thi Thu', birthday=datetime(2001, 8, 6, 0), address_id=1,
    #               phone_number='0964345626', appointment_date=datetime(2021, 12, 18, 8, 0), gender_id=Gender.NU, was_scheduled=True)
    # c2 = Customer(first_name='Vi', last_name='Nguyen Thi Trieu', birthday=datetime(2001, 11, 29, 0), address_id=2,
    #               phone_number='0964321321', appointment_date=datetime(2022, 1, 15, 8, 30, 0), gender_id=Gender.NU, was_scheduled=True)
    # c3 = Customer(first_name='Hong', last_name='Tran Thi Bich', birthday=datetime(2001, 7, 11, 0), address_id=2,
    #               phone_number='0965443215', appointment_date=datetime(2021, 12, 18, 9, 0), gender_id=Gender.NU, was_scheduled=True)
    # c4 = Customer(first_name='Tien', last_name='Nguyen Minh', birthday=datetime(2001, 1, 1, 0), address_id=7,
    #               phone_number='0962904570', appointment_date=datetime(2022, 1, 15, 9, 0), gender_id=Gender.NAM, was_scheduled=True)
    # c5 = Customer(first_name='A', last_name='Nguyen Van', birthday=datetime(2006, 1, 1, 0), address_id=5,
    #               phone_number='0965443307', appointment_date=datetime(2021, 12, 20, 13, 0), gender_id=Gender.NAM, was_scheduled=True)
    # c6 = Customer(first_name='B', last_name='Tran Thi', birthday=datetime(1999, 1, 1, 0), address_id=6,
    #               phone_number='0965455221', appointment_date=datetime(2022, 1, 14, 8, 30, 0), gender_id=Gender.NU, was_scheduled=True)
    # c7 = Customer(first_name='C', last_name='Le Hoai', birthday=datetime(1992, 1, 1, 0), address_id=7,
    #               phone_number='0965455521', appointment_date=datetime(2022, 1, 15, 10, 0), gender_id=Gender.NU, was_scheduled=True)
    # c8 = Customer(first_name='An', last_name='Tran Nguyen Duy', birthday=datetime(2001, 1, 6, 0), address_id=3,
    #               phone_number='0856382954', appointment_date=datetime(2022, 1, 20, 8, 0), gender_id=Gender.NAM, was_scheduled=True)
    # c9 = Customer(first_name='Dao', last_name='Le Thi Hong', birthday=datetime(2001, 1, 29, 0), address_id=3,
    #               phone_number='0584937427', appointment_date=datetime(2022, 1, 23, 11, 0, 0), gender_id=Gender.NU)
    # c9 = Customer(first_name='Bao', last_name='Le Gia', birthday=datetime(2001, 7, 11, 0), address_id=6,
    #               phone_number='0856473859', appointment_date=datetime(2022, 1, 23, 14, 0), gender_id=Gender.NAM)
    # c10 = Customer(first_name='Cao', last_name='Bui Nam', birthday=datetime(2001, 1, 1, 0), address_id=4,
    #               phone_number='0657382647', appointment_date=datetime(2022, 1, 23, 14, 30, 0), gender_id=Gender.NAM)
    # c11 = Customer(first_name='Loc', last_name='Pham Hoang Diem', birthday=datetime(2006, 1, 1, 0), address_id=4,
    #               phone_number='0856483953', appointment_date=datetime(2022, 1, 23, 15, 0), gender_id=Gender.NU)
    # c12 = Customer(first_name='Minh', last_name='Vo Thi Thu', birthday=datetime(1999, 1, 1, 0), address_id=6,
    #               phone_number='0965534245', appointment_date=datetime(2022, 1, 23, 15, 20, 0), gender_id=Gender.NU)
    # c13 = Customer(first_name='Kiet', last_name='Doan Tuan', birthday=datetime(1992, 1, 1, 0), address_id=7,
    #               phone_number='0647357284', appointment_date=datetime(2022, 1, 23, 10, 0), gender_id=Gender.NAM)
    # db.session.add(c1)
    # db.session.add(c2)
    # db.session.add(c3)
    # db.session.add(c4)
    # db.session.add(c5)
    # db.session.add(c6)
    # db.session.add(c7)
    # db.session.add(c8)
    # db.session.add(c9)
    # db.session.add(c10)
    # db.session.add(c11)
    # db.session.add(c12)
    # db.session.add(c13)
    #
    # #Add Schedule
    # s1 = Schedule(examination_date=date(2021, 12, 18))
    # s2 = Schedule(examination_date=date(2021, 12, 20))
    # s3 = Schedule(examination_date=date(2022, 1, 14))
    # s4 = Schedule(examination_date=date(2022, 1, 15))
    # s5 = Schedule(examination_date=date(2022, 1, 20))
    # db.session.add(s1)
    # db.session.add(s2)
    # db.session.add(s3)
    # db.session.add(s4)
    # db.session.add(s5)
    #
    # #Add CustomerSche
    # cs1 = CustomerSche(customer_id=1, schedule_id=1, examined=True, timer=time(9, 3, 2, 3))
    # cs2 = CustomerSche(customer_id=2, schedule_id=1, examined=True, timer=time(10, 0, 0, 0))
    # cs3 = CustomerSche(customer_id=3, schedule_id=1, examined=True, timer=time(11, 0, 0, 0))
    # cs4 = CustomerSche(customer_id=4, schedule_id=2, examined=True, timer=time(15, 0, 0, 0))
    # cs5 = CustomerSche(customer_id=5, schedule_id=2, examined=True, timer=time(16, 0, 0, 0))
    # cs6 = CustomerSche(customer_id=6, schedule_id=3, examined=True, timer=time(9, 0, 0, 0))
    # cs7 = CustomerSche(customer_id=1, schedule_id=3, examined=True, timer=time(10, 0, 0, 0))
    # cs8 = CustomerSche(customer_id=3, schedule_id=3, examined=True, timer=time(11, 0, 0, 0))
    # cs9 = CustomerSche(customer_id=7, schedule_id=4, examined=True, timer=time(8, 0, 0, 0))
    # cs10 = CustomerSche(customer_id=2, schedule_id=4, examined=True, timer=time(10, 0, 0, 0))
    # cs11 = CustomerSche(customer_id=4, schedule_id=4, examined=True, timer=time(10, 0, 0, 0))
    # cs12 = CustomerSche(customer_id=8, schedule_id=5, examined=True, timer=time(10, 0, 0, 0))
    # db.session.add(cs1)
    # db.session.add(cs2)
    # db.session.add(cs3)
    # db.session.add(cs4)
    # db.session.add(cs5)
    # db.session.add(cs6)
    # db.session.add(cs7)
    # db.session.add(cs8)
    # db.session.add(cs9)
    # db.session.add(cs10)
    # db.session.add(cs11)
    # db.session.add(cs12)
    #
    # #Add regulation
    # r1 = Regulation(created_date=datetime(2021, 12, 18, 0))
    # db.session.add(r1)

    # #Add medicine_type
    # mt1 = MedicineType(type_name='Thuốc ho')
    # mt2 = MedicineType(type_name='Thuốc giảm đau')
    # mt3 = MedicineType(type_name='Thuốc hạ sốt')
    # mt4 = MedicineType(type_name='Thuốc đau bụng')
    # mt5 = MedicineType(type_name='Thuốc an thần')
    # mt6 = MedicineType(type_name='Thuốc trợ tim')
    # db.session.add(mt1)
    # db.session.add(mt2)
    # db.session.add(mt3)
    # db.session.add(mt4)
    # db.session.add(mt5)
    # db.session.add(mt6)
    #
    # #Add producer
    # prd1 = Producer(name='Imexpharm')
    # prd2 = Producer(name='DHG PHARMA')
    # prd3 = Producer(name='MEBIPHAR')
    # prd4 = Producer(name='Traphaco')
    # db.session.add(prd1)
    # db.session.add(prd2)
    # db.session.add(prd3)
    # db.session.add(prd4)
    #
    # #Add medicine
    # m1 = Medicine(name='Paracetamol', quantity=100, price=20000, out_of_date=datetime(2025, 9, 12, 0), producer_id=1, medicine_type=3)
    # m2 = Medicine(name='Benzodiazepinesg', quantity=120, price=30000, out_of_date=datetime(2025, 9, 12, 0), producer_id=1, medicine_type=5)
    # m3 = Medicine(name='Morphine', quantity=70, price=40000, out_of_date=datetime(2025, 9, 12, 0), producer_id=2, medicine_type=2)
    # m4 = Medicine(name="angiotensin", quantity=0, price=10000, out_of_date=datetime(2025, 9, 12, 0), producer_id=3, medicine_type=6)
    # m5 = Medicine(name="Touxirup", quantity=10, price=15000, out_of_date=datetime(2025, 9, 12, 0), producer_id=4, medicine_type=1)
    # m6 = Medicine(name="Prospan Forte", quantity=120, price=10000, out_of_date=datetime(2025, 9, 12, 0), producer_id=3,medicine_type=1)
    # m7 = Medicine(name="Loperamid", quantity=200, price=15000, out_of_date=datetime(2025, 9, 12, 0), producer_id=4, medicine_type=4)
    # db.session.add(m1)
    # db.session.add(m2)
    # db.session.add(m3)
    # db.session.add(m4)
    # db.session.add(m5)
    # db.session.add(m6)
    # db.session.add(m7)
    #
    # #Add medicall_bill
    # mb1 = MedicalBill(user_id=2, customer_sche=1, symptom='Người hay bị nhức mỏi',
    #                    diagnostic_disease= 'Cơ thể yếu do không vận động thường xuyên', created_date=datetime(2021,12,18,0))
    # mb2 = MedicalBill(user_id=2, customer_sche=2, symptom='Ho, đau họng', diagnostic_disease= 'Viêm họng', created_date=datetime(2021,12,18,0))
    # mb3 = MedicalBill(user_id=2, customer_sche=3, symptom='Ho', diagnostic_disease= 'Viêm họng', created_date=datetime(2021,12,18,0))
    # mb4 = MedicalBill(user_id=2, customer_sche=4, symptom='Chảy máu mũi', diagnostic_disease= 'Viêm xoang', created_date=datetime(2021,12,20,0))
    # mb5 = MedicalBill(user_id=2, customer_sche=5, symptom='Đau đầu', diagnostic_disease='Đau đầu', created_date=datetime(2021,12,20,0))
    # mb6 = MedicalBill(user_id=2, customer_sche=6, symptom='Ho, mất vị giác', diagnostic_disease='Có thể bị covid, theo dõi thêm', created_date=datetime(2022,1,14,0))
    # mb7 = MedicalBill(user_id=2, customer_sche=7, symptom='Đau lưng, mỏi gối', diagnostic_disease='Dấu hiệu tuổi già', created_date=datetime(2022,1,14,0))
    # mb8 = MedicalBill(user_id=2, customer_sche=8, symptom='Thường xuyên hắt xì hơi', diagnostic_disease='Viêm xoang', created_date=datetime(2022,1,14,0))
    # mb9 = MedicalBill(user_id=2, customer_sche=9, symptom='Đau tim', diagnostic_disease='Đau tim', created_date=datetime(2022,1,15,0))
    # mb10 = MedicalBill(user_id=2, customer_sche=10, symptom='Đau lưng', diagnostic_disease='Thoái hóa cột sống', created_date=datetime(2022,1,15,0))
    # mb11 = MedicalBill(user_id=2, customer_sche=11, symptom='Mất ngủ', diagnostic_disease='Mất ngủ', created_date=datetime(2022,1,15,0))
    # mb12 = MedicalBill(user_id=2, customer_sche=12, symptom='Đau mỏi vai', diagnostic_disease='Ngồi sai thế', created_date=datetime(2022,1,20,0))
    # db.session.add(mb1)
    # db.session.add(mb2)
    # db.session.add(mb3)
    # db.session.add(mb4)
    # db.session.add(mb5)
    # db.session.add(mb6)
    # db.session.add(mb7)
    # db.session.add(mb8)
    # db.session.add(mb9)
    # db.session.add(mb10)
    # db.session.add(mb11)
    # db.session.add(mb12)
    #
    # #Add medical_bill_detail
    # mbd1 = MedicalBillDetail(medical_bill=1, medicine=2, quantity=5, unit_price=30000, how_to_use='1 ngày uống 2 lần')
    # mbd2 = MedicalBillDetail(medical_bill=1, medicine=3, quantity=10, unit_price=40000, how_to_use='1 ngày uống 3 lần')
    # mbd3 = MedicalBillDetail(medical_bill=2, medicine=1, quantity=15, unit_price=20000, how_to_use='2 ngày uống 1 lần')
    # mbd4 = MedicalBillDetail(medical_bill=3, medicine=2, quantity=30, unit_price=30000, how_to_use='1 tuần uống 3 lần')
    # mbd5 = MedicalBillDetail(medical_bill=4, medicine=1, quantity=13, unit_price=30000, how_to_use='1 tuần uống 7 lần')
    # mbd6 = MedicalBillDetail(medical_bill=5, medicine=5, quantity=5, unit_price=30000, how_to_use='1 ngày uống 2 lần')
    # mbd7 = MedicalBillDetail(medical_bill=6, medicine=7, quantity=10, unit_price=40000, how_to_use='1 ngày uống 3 lần')
    # mbd8 = MedicalBillDetail(medical_bill=7, medicine=4, quantity=15, unit_price=20000, how_to_use='2 ngày uống 1 lần')
    # mbd9 = MedicalBillDetail(medical_bill=8, medicine=6, quantity=30, unit_price=30000, how_to_use='1 tuần uống 3 lần')
    # mbd10 = MedicalBillDetail(medical_bill=9, medicine=5, quantity=13, unit_price=30000, how_to_use='1 tuần uống 7 lần')
    # mbd11 = MedicalBillDetail(medical_bill=10, medicine=6, quantity=30, unit_price=30000, how_to_use='1 tuần uống 3 lần')
    # mbd12 = MedicalBillDetail(medical_bill=11, medicine=5, quantity=13, unit_price=30000, how_to_use='1 tuần uống 7 lần')
    # mbd13 = MedicalBillDetail(medical_bill=12, medicine=6, quantity=30, unit_price=30000, how_to_use='1 tuần uống 3 lần')
    # db.session.add(mbd1)
    # db.session.add(mbd2)
    # db.session.add(mbd3)
    # db.session.add(mbd4)
    # db.session.add(mbd5)
    # db.session.add(mbd6)
    # db.session.add(mbd7)
    # db.session.add(mbd8)
    # db.session.add(mbd9)
    # db.session.add(mbd10)
    # db.session.add(mbd11)
    # db.session.add(mbd12)
    # db.session.add(mbd13)
    #
    # #Add receipt
    # w1 = Receipt(total_price=230000, regulation=1, medical_bill=1, customer_id=1, user_id=3,
    #              created_date=datetime(2021, 12, 18, 0))
    # w2 = Receipt(total_price=250000, regulation=1, medical_bill=2, customer_id=2, user_id=3,
    #              created_date=datetime(2021, 12, 18, 0))
    # w3 = Receipt(total_price=520000, regulation=1, medical_bill=3, customer_id=3, user_id=3,
    #              created_date=datetime(2021, 12, 18, 0))
    # w4 = Receipt(total_price=720000, regulation=1, medical_bill=4, customer_id=4, user_id=3,
    #              created_date=datetime(2021, 12, 20, 0))
    # w5 = Receipt(total_price=230000, regulation=1, medical_bill=5, customer_id=5, user_id=3,
    #              created_date=datetime(2021, 12, 20, 0))
    # w6 = Receipt(total_price=250000, regulation=1, medical_bill=6, customer_id=6, user_id=3,
    #              created_date=datetime(2022, 1, 14, 0))
    # w7 = Receipt(total_price=520000, regulation=1, medical_bill=7, customer_id=1, user_id=3,
    #              created_date=datetime(2022, 1, 14, 0))
    # w8 = Receipt(total_price=720000, regulation=1, medical_bill=8, customer_id=3, user_id=3,
    #              created_date=datetime(2022, 1, 14, 0))
    # w9 = Receipt(total_price=720000, regulation=1, medical_bill=9, customer_id=7, user_id=3,
    #              created_date=datetime(2022, 1, 15, 0))
    # w10 = Receipt(total_price=615000, regulation=1, medical_bill=10, customer_id=2, user_id=3,
    #              created_date=datetime(2022, 1, 15, 0))
    # w11 = Receipt(total_price=1003000, regulation=1, medical_bill=11, customer_id=4, user_id=3,
    #              created_date=datetime(2022, 1, 15, 0))
    # w12 = Receipt(total_price=325000, regulation=1, medical_bill=12, customer_id=8, user_id=3,
    #              created_date=datetime(2022, 1, 20, 0))
    # db.session.add(w1)
    # db.session.add(w2)
    # db.session.add(w3)
    # db.session.add(w4)
    # db.session.add(w5)
    # db.session.add(w6)
    # db.session.add(w7)
    # db.session.add(w8)
    # db.session.add(w9)
    # db.session.add(w10)
    # db.session.add(w11)
    # db.session.add(w12)

    # #Thêm dữ liệu ngày hiện tại để xem thống kê
    # cx = Customer.query.get(5)
    # cy = Customer.query.get(6)
    # cz = Customer.query.get(3)
    # cx.appointment_date = datetime(2022, 1, 23, 8, 30, 20, 0)
    # cy.appointment_date = datetime(2022, 1, 23, 10, 30, 20, 0)
    # cz.appointment_date = datetime(2022, 1, 23, 13, 30, 20, 0)
    # db.session.add(cx)
    # db.session.add(cy)
    # db.session.add(cz)
    # s = Schedule(examination_date=datetime.now())
    # db.session.add(s)
    # db.session.commit()
    # csx = CustomerSche(customer_id=cx.id, schedule_id=s.id, examined=True, timer=time(8, 30, 20))
    # csy = CustomerSche(customer_id=cy.id, schedule_id=s.id, examined=False, timer=time(10, 30, 20))
    # csz = CustomerSche(customer_id=cz.id, schedule_id=s.id, examined=False, timer=time(13, 30, 20))
    # db.session.add(csx)
    # db.session.add(csy)
    # db.session.add(csz)
    # db.session.commit()
    # mbx = MedicalBill(user_id=2, customer_sche=csx.id, symptom='Đau đầu, sổ mũi', diagnostic_disease='Đau đầu')
    # db.session.add(mbx)
    # db.session.commit()
    # mbdx = MedicalBillDetail(medical_bill=mbx.id, medicine=1, quantity=15, unit_price=20000, how_to_use='2 ngày uống 1 lần')
    # mbdy = MedicalBillDetail(medical_bill=mbx.id, medicine=3, quantity=15, unit_price=50000, how_to_use='2 ngày uống 2 lần')
    # db.session.add(mbdx)
    # db.session.add(mbdy)
    # r = Receipt(total_price=740000, regulation=1, medical_bill=mbx.id, customer_id=csx.customer_id, user_id=3,
    #              created_date=datetime.now())
    # db.session.add(r)
    #
    # db.session.commit()
    db.create_all()

