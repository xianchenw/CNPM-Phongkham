let customerPhoneNumber = ''
let user = null

function CheckSession(user, idModal) { //user, phoneNumber,
    id = idModal.substring(3);
    //if user exist
    if (user) { //bo 'bt-' ra khoi id cua button
        $("#" + idModal).attr("data-target", '#' + id);
    }
    else {
        $("#" + idModal).attr("data-target", '#login-require');
    }
}
function CheckPhoneNumber(phoneNumber, again) {
    document.getElementById('otp-code').value = ""
    if (phoneNumber.startsWith('84') && phoneNumber.length == 11 || phoneNumber.startsWith('0') && phoneNumber.length == 10) {
        document.getElementById('customerPhoneNumber-status').textContent = '';
        if (again==false)
            OTPSendCode(phoneNumber);
        else OTPSendCodeAgain(phoneNumber);
    }
    else if (phoneNumber.length > 0)
        document.getElementById('customerPhoneNumber-status').textContent = 'Số điện thoại không hợp lệ';
    else
        document.getElementById('customerPhoneNumber-status').textContent = null;
}
function OTPSendCode(phoneNumber) {
    event.preventDefault()

    fetch("/api/otp-auth", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'phoneNumber': phoneNumber
        })
    })
}
function OTPSendCodeAgain(phoneNumber) {
    event.preventDefault()

    fetch("/api/otp-auth-again", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'phoneNumber': phoneNumber
        })
    })
}
function ValidatePhoneNumber(OTPValue, idFormSubmit) {
    phoneNumber = document.getElementById('customerPhoneNumber').value.toString();
    if (phoneNumber.startsWith('84') && phoneNumber.length == 11 || phoneNumber.startsWith('0') && phoneNumber.length == 10) {
        if (OTPValue.length == 6)
        {
            $('#' + idFormSubmit).submit()
        }
    }
}
function CheckOrderDateTime(idEffect, idAlert) {
    //Constant Regulation
    const timeDistanceUnitMAX = 36 * 60 * 60; // maximum at 1.5 days
    const timeDistanceUnitMIN = 1.5 * 60 * 60 // at least 3 hours
    //Regulation
    const hourOpen = 7
    const minuteOpen = 30
            //BREAK
    const hourBreakFrom = 11
    const minuteBreakFrom = 30
    const hourBreakTo = 13
    //const minuteBreakTo  0
    const hourClose = 17
    //const minuteClose = 0
    //Alive value
    currentDateTime = new Date()
    currentDateTime_seconds = currentDateTime.getTime() / 1000
    typedDateTime = new Date(document.getElementById('order-date').value)
    typedDateTime_seconds = typedDateTime.getTime() / 1000
    timeDistances = typedDateTime_seconds - currentDateTime_seconds
    //Check order time in open and close time
    typedHour = typedDateTime.getHours()
    typedMinutes = typedDateTime.getMinutes()

          //07:30 - 17:00 order can be created to check
    if ((typedHour == hourOpen && typedMinutes < minuteOpen) || (typedHour < hourOpen || typedHour > hourClose) ||
            (typedHour == hourClose && typedMinutes > 0)) {   //7:30 - 17:00 (not)
        document.getElementById(idAlert).textContent = 'Thời gian hẹn không hợp lệ. [7:30 - 11:30 và 13:00 - 17:00]'
        SubmitButtonStatus("btn-submit-order", false)
        return false;
    } else if ((typedHour == hourBreakFrom && typedMinutes > minuteBreakFrom) || (typedHour > hourBreakFrom && typedHour < hourBreakTo)) { //11:30 - 13:00
        document.getElementById(idAlert).textContent = 'Thời gian hẹn không hợp lệ. [7:30 - 11:30 và 13:00 - 17:00]'
        SubmitButtonStatus("btn-submit-order", false)
        return false;
    }
        //Ordered time compares with the present
    if (!(timeDistances >= timeDistanceUnitMIN && timeDistances <= timeDistanceUnitMAX)) {
        document.getElementById(idAlert).textContent = 'Thời gian hẹn không hợp lệ. [Đặt hẹn tối đa 36 giờ và tối thiểu 1.5 giờ]'
        SubmitButtonStatus("btn-submit-order", false)
        return false;
    }
    document.getElementById(idAlert).textContent = ''

    //get submit for button
    SubmitButtonStatus("btn-submit-order", true)

    return true;
}
function SubmitButtonStatus(idButton, status) {
    if (status == true) {
        $('#' + idButton).attr('type', 'submit')
    } else {
        $('#' + idButton).attr('type', 'button')
    }
    return true
}