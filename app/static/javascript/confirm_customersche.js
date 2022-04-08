function scheduleSuccess(id){
    fetch('/admin/appoinments/confirm-customersche',{
        method:'put',
        body:JSON.stringify({
            'id':id
        }),
        headers:{
            'Content-Type':'application/json'
        }
        }).then(res => res.json()).then(data =>{
            if(data.status==201){
                let btnsuccess = document.getElementById('button-success'+data.id)
                let btncancel = document.getElementById('button-cancel'+data.id)
                btnsuccess.innerHTML = `
                <button type="submit" class="btn btn-success">Đã xác nhận</button>
                `
                btncancel.innerHTML = ``
            } else if(data.status==400){
                alert(data.msg)
            }
            else {
                alert('Lỗi hệ thống')
            }
        })
}
function scheduleError(id){
    if (confirm('Hủy lịch hẹn ?')==true){
        fetch('/admin/appoinments/cancel-customersche', {
            method:'put',
            body:JSON.stringify({
                'id':id
            }),
            headers:{
                'Content-Type':'application/json'
            }
            }).then(res => res.json()).then(data => {
                if(data.status==201){
                    let btnsuccess = document.getElementById('button-success'+data.id)
                    let btncancel = document.getElementById('button-cancel'+data.id)
                    btnsuccess.innerHTML = `
                        <button type="submit" class="btn btn-secondary">Đã hủy lịch hẹn</button>
                    `
                    btncancel.innerHTML = ``
                } else{
                    alert('Lỗi hệ thống')
                }
            })
    }
}