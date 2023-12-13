

(function ($) {
    "use strict";
})(jQuery);
/*
axios
.get('http://127.0.0.1:5000/temps/today_api')
    .then((response) => {
        const table = document.getElementById("table-body");
        const data = response.data.data
        console.log(data)
        for (let i = 0; i < data.length; i++) {
            console.log(i)
            let row = table.insertRow();
            row.className = "tableRow";
            let time = row.insertCell(0);
            time.innerHTML = data[i].time;
            let localT = row.insertCell(1);
            localT.innerHTML = data[i].local_temp;
            let piTemp = row.insertCell(2);
            piTemp.innerHTML = data[i].pi_temp;
            let remoteT = row.insertCell(3);
            remoteT.innerHTML = data[i].remote_temp;
            let humidity = row.insertCell(4);
            humidity.innerHTML = data[i].humidity;
        }
    })
.catch((error) => {
    console.log('not successful')
});

function populate() {
    const api_url = 'http://localhost:5000/temps/today_api';
    let response = fetch(api_url);
    console.log(response); 
    const table = document.getElementById("table-body");
    for (var item of data) {
    let row = table.insertRow();
    let time = row.insertCell(0);
    time.innerHTML = item.time;
    let localT = row.insertCell(1);
    localT.innerHTML = item.local_temp;
    let piTemp = row.insertCell(2);
    piTemp.innerHTML = item.pi_temp;
    let remoteT = row.insertCell(3);
    remoteT.innerHTML = item.outside_temp;
    let humidity = row.insertCell(4);
    humidity.innerHTML = item.humidity;
    };
}*/
