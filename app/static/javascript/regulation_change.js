function add_new_regulation(new_quantity, new_fee) {
    event.preventDefault();

    fetch('/api/new-regulation', {
        method: 'post',
        body: JSON.stringify({
            'new_quantity': new_quantity,
            'new_fee': new_fee
        }),
        header: {
            'Content-Type': 'application/json'
        }
    })
}