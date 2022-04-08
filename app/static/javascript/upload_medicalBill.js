//function add_new_medicalBill(new_customer_name, new_phoneNumber, new_age, new_gender,
//            new_maPhieuKham, new_symptom, new_diagnostic_disease, new_how_to_use, new_medicine_name) {
//
//    event.preventDefault();
//
//    fetch('/api/new-regulation', {
//        method: 'post',
//        body: JSON.stringify({
//            'new_customer_name': new_customer_name,
//            'new_phoneNumber': new_phoneNumber,
//            'new_age': new_age,
//            'new_gender': new_gender,
//            'new_maPhieuKham': new_maPhieuKham,
//            'new_symptom': new_symptom,
//            'new_diagnostic_disease': new_diagnostic_disease,
//            'new_how_to_use': new_how_to_use,
//            'new_medicine_name': new_medicine_name
//        }),
//        header: {
//            'Content-Type': 'application/json'
//        }
//    })
//}
function cancelMedicalBill(id){
    if (confirm('Hủy lập phiếu cho lịch hẹn này ?')==true){
        fetch('/admin/cancel-medicalbill',{
            method:'post',
            body: JSON.stringify({
                'id':id
            }),
            headers:{
                'Content-Type':'application/json'
            }
        }).then(res => res.json()).then(data=>{
            if (data.status==201){
                location.reload()
            } else{
                alert(data.msg)
            }
        })
    }
}

function createmedicalbill(callback){
    let ten = document.getElementById('customer_name').value
    let sdt = document.getElementById('phoneNumber').value
    let tuoi = document.getElementById('customer-age').value
    let gioitinh = document.getElementById('customer-gender').value
    let phieukham = document.getElementById('medical-id').value
    let trieuchung = document.getElementById('symptom').value
    let benhchuandoan = document.getElementById('diagnostic_disease').value
    fetch('/admin/createmedicalbill/create-medicalbill', {
    method:'post',
    body: JSON.stringify({
        'ten': ten,
        'sdt': sdt,
        'tuoi': tuoi,
        'gioitinh': gioitinh,
        'phieukham': phieukham,
        'trieuchung': trieuchung,
        'benhchuandoan': benhchuandoan
    }),
    headers:{
        'Content-Type': 'application/json'
    }
    }).then(res => res.json()).then(data => {
        if(data.status == 201){
            console.info(data.medical_bill)
            callback()
            return 201
        }
        else if(data.status==404){
            alert(data.err_msg)
            return 404
        }
    })
}

function addMedicine(){
    createmedicalbill(saveMedicine)
}

function saveMedicine(){
    let obj = document.getElementById('medicine-name');
    fetch('/admin/createmedicalbill/add-medicine', {
        method:'post',
        body:JSON.stringify({
            'medicine_name':obj.value
        }),
        headers:{
        'Content-Type': 'application/json'
        }
    }).then(function(res){
        if (!res.ok) {
            alert('Hãy chọn thuốc !')
        }
        else{
            console.info(res)
            return res.json()
        }
    }).then(data =>{
        if (data.status == 201){
            console.info(data.medicine)
            location.reload()
        } else if(data.status == 404){
            alert(data.err_msg)
        }
    })

}

function del(){
    createmedicalbill(none)
    if(confirm('Xóa phiếu ?')==true){
        fetch('/admin/createmedicalbill/delete-medicinebill-details',{
            method:'post'
        }).then(res => res.json()).then(data =>{
            if (data.code == 200)
                location.reload()
            else
                alert('Lỗi')
        }).catch(err=>console.error(err))
    }
}

function updateMedicineQuantity(obj, id){
    fetch('/admin/createmedicalbill/update/quantity', {
        method:'put',
        body: JSON.stringify({
            'id':id,
            'quantity':obj
        }),
        headers:{
            'Content-Type':'application/json'
        }
    }).then(res => res.json()).then(data =>{
        if(data.status == 400){
            alert(data.msg)
        } else {
            console.info(data.status)
        }
    })
}

function updateHowToUse(obj,id){
    fetch('/admin/createmedicalbill/update/how-to_use', {
        method:'put',
        body: JSON.stringify({
            'id':id,
            'how_to_use':obj
        }),
        headers:{
            'Content-Type':'application/json'
        }
    }).then(res => res.json()).then(data =>{
        console.info(data)
    })
}
function delMedicine(id){
    createmedicalbill(none)
    if(confirm("Xóa thuốc ?")==true){
        fetch('/admin/createmedicalbill/delete-medicine',{
            method:'put',
            body:JSON.stringify({
                'id':id
            }),
            headers:{
                'Content-Type': 'application/json'
            }
        }).then(res => res.json()).then(data => {
            if (data.status=201){
                console.info(data.medicine)
                location.reload()
            } else if(data.status=404){
                alert('Lỗi hệ thồng')
            }
        })
    }
}

function none(){
    console.info('haha')
}

function loadPatient(){
    let obj = document.getElementById('phoneNumber')
    let phieukham = document.getElementById('medical-id')
    fetch('/admin/createmedicalbill/load-patient',{
        method:'post',
        body:JSON.stringify({
            'sdt':obj.value,
            'phieukham':phieukham.value
        }),
        headers:{
        'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data =>{
        if (data.status == 201){
            let p = data.patient
            let area = document.getElementById('patient-info')

            area.innerHTML = `
            <div class="row d-flex">
                <div class="form-group p-2 flex-fill d-flex" style="margin-bottom:0rem">
                    <label for="customer_name" class="p-2 flex-fill col-md-3">Tên khách hàng:</label>
                    <input style="" value="${p.first_name}" name="customer_name"  type="text" class="form-control p-2 flex-fill" placeholder="Nhập tên khách hàng" required id="customer_name">
                </div>
                <div class="form-group p-2 flex-fill d-flex" style="margin-bottom:0rem">
                    <label for="phoneNumber" class="p-2 flex-fill col-md-3">Số điện thoại:</label>
                    <input onblur="loadPatient(this)" value="${p.phone_number}" style="margin-right:0.5rem" name="phoneNumber" type="text" class="form-control p-2 flex-fill" placeholder="Nhập số điện thoại" required id="phoneNumber">
                </div>
            </div>
            <div class="row d-flex">
                <div class="p-2 d-flex col-md-4">
                    <label class="p-2">Tuổi</label>
                    <span class="text-success p-2" style="margin-left:1rem; margin-right:1rem">
                        <input class='' id="customer-age" value="${p.age}">
                    </span>
                </div>
                <div class="p-2 d-flex col-md-4">
                    <label class="p-2">Giới tính</label>
                    <span  class="text-info p-2" style="margin-left:1rem; margin-right:1rem">
                        <input class='' id="customer-gender" value="${p.gender}">
                    </span>
                </div>
                <div class="p-2 d-flex col-md-4">
                    <label class="p-2">Mã phiếu</label>
                    <span  class="text-danger p-2" style="margin-left:1rem; margin-right:1rem">
                         <input class='' id="medical-id" value="${data.phieukham}">
                    </span>
                </div>
            </div>
            `
            document.getElementById('customer-age').disabled = true;
            document.getElementById('customer-gender').disabled = true;
            document.getElementById('medical-id').disabled = true;
        } else if(data.status == 404){
            alert(data.err_msg)
        }
        createmedicalbill(none)
    })
}

function addMedicalBill(){
    if(confirm('Lập phiếu khám ?')==true){
        fetch('/admin/createmedicalbill/',{
            method:'post'
        }).then(res => {
            console.info(res)
            return res.json()
        }).then(data =>{
            if (data.code == 201){
                console.info(data)
                location.reload()
            }else if(data.code ==400){
                console.info(data.code)
                alert('Lập phiếu khám thất bại')
            }
        })
    }
}