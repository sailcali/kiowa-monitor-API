const getForecast = () => {
    axios.get('../api/weather/outlook')
    .then((response) => {
        var lastDate = new Date(response.data['list'][0]['dt']* 1000)
        var day = 1;
        var thisContainer = document.getElementById("day1Container");
        var h = document.createElement("h1");
        h.innerHTML = lastDate.getDate() + " " + lastDate.toLocaleString('default', { month: 'long' });
        thisContainer.append(h);
        for (var i=0; i<response.data['list'].length; i++) {
            
            var thisDateTime = new Date(response.data['list'][i]['dt']* 1000);
            if (thisDateTime.getDate() != lastDate.getDate()) {
                day ++;
                if (day == 6) {
                    break;
                }
                lastDate = new Date(thisDateTime)
                thisContainer = document.getElementById("day" + day + "Container");
                h = document.createElement("h1");
                h.innerHTML = thisDateTime.getDate() + " " + thisDateTime.toLocaleString('default', { month: 'long' });
                thisContainer.append(h);
            }
            var p = document.createElement("p");
            p.innerHTML = 'At ' + thisDateTime.getHours() + ":00 it will be " + 
                response.data['list'][i]['main']['temp'] + "*F";
            thisContainer.append(p);
            
        }

    })
}

getForecast();