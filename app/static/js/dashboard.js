
const venstarModeSetting = () => {
    
    // Check the radio buttons for current HVAC modes
    if (data.mode === "OFF") {
        const radio = document.getElementById('modeoff');
        radio.checked = true
    }
    else if (data.mode === "HEAT") {
        const radio = document.getElementById('modeheat');
        radio.checked = true
    }
    else if (data.mode === "COOL") {
        const radio = document.getElementById('modecool');
        radio.checked = true
    }
    else if (data.mode === "AUTO") {
        const radio = document.getElementById('modeauto');
        radio.checked = true
    };
    if (data.fan_setting === "AUTO") {
        const radio = document.getElementById('fanauto');
        radio.checked = true
    }
    else if (data.fan_setting === "ON") {
        const radio = document.getElementById('fanon');
        radio.checked = true
    };
    if (data.landscape_state === 'ON') {
        const slider = document.getElementById("landscapeLightSwitch")
        slider.checked = true
    };

    // Do not display heat modes in summer / cool modes in winter
    const current_month = new Date().getMonth()
    if (current_month > 3 & current_month < 11) {
        for (let element of document.getElementsByClassName("summer")){
            element.style.display="flex";
         }
    } else {
        for (let element of document.getElementsByClassName("winter")){
            element.style.display="flex";
         }
    };
    
};

const changeDateHref = () => {
    const dateInput = document.getElementById("dateInputTemp").value;
    const link = document.getElementById("dateButtonTemp");
    link.setAttribute('href', "/temps/"+dateInput);
}
const adjustLandscapeLighting = () => {
    const newDelay = document.getElementById("delayDateTime")
    var delay = 0
    if (newDelay.value != '') {
        delay = newDelay.value
    }
    if (data.landscape_state === 'ON') {
        axios.post('landscape/change-state', {
            state: 0,
            delay_time: delay
          })
          .then(function (response) {
            location.reload()
          })
          .catch(function (error) {
            console.log(error);
            lightingSwitch.checked = true;

          });
        } else {
            axios.post('landscape/change-state', {
            state: 1,
            delay_time: delay
          })
          .then(function (response) {
            location.reload()
          })
          .catch(function (error) {
            console.log(error);
            lightingSwitch.checked = false;
          });
        };
        
    };

const getGarageData = () => {
    axios.get('api/garage-status')
    .then((response) => {
        const current_date = new Date()
        const delay_date = new Date(response.data['current_delay'])
        const garageTempElement = document.getElementById("garageTemperature");
        const landscapeStateElement = document.getElementById("landscapeState");
        const landscapeDelayElement = document.getElementById("landscapeDelaySetTime");
        const slider = document.getElementById("landscapeLightSwitch");
        garageTempElement.innerHTML = "Garage Temp: " + parseInt(response.data['temperature']) + "*F";
        
        if (response.data['lighting_state'] == 1) {
            landscapeStateElement.innerHTML = "Landscape Lighting: ON"
            slider.checked = true
        } else {
            landscapeStateElement.innerHTML = "Landscape Lighting: OFF"
            slider.checked = false
        }

        if (delay_date > current_date) {
            landscapeDelayElement.innerHTML = "Delay Set Time: " + response.data['current_delay'];
            landscapeDelayElement.style.display="flex";
        }
        
    })
}

const adjustSetTemperature = (event) => {
    const heatElement = document.getElementById('heattemp')
    const coolElement = document.getElementById('cooltemp')
    if (event.target.id == 'heatIncrease') {
        heatElement.value = parseInt(heatElement.value) + 1
    } else if (event.target.id == 'HeatDecrease') {
        heatElement.value = parseInt(heatElement.value) - 1
    } else if (event.target.id == 'coolIncrease') {
        coolElement.value = parseInt(coolElement.value) + 1
    } else if (event.target.id == 'coolDecrease') {
        coolElement.value = parseInt(coolElement.value) - 1
    };
}

const getSmartThingsData = () => {
    axios.get('api/smartthings/status')
    .then((response) => {
        for (var i=0; i<response.data['devices'].length; i++) {
            if (response.data['devices'][i]['name'] === 'Pineapple') {
                const pineappleSwitch = document.getElementById('pineappleLightSwitch');
                if (response.data['devices'][i]['state'] == 'on') {
                    pineappleSwitch.checked = true;
                } else {
                    pineappleSwitch.checked = false;
                };      
            } else if (response.data['devices'][i]['name'] === 'Bedroom Light') {
                const bedroomSwitch = document.getElementById('bedroomLightSwitch');
                if (response.data['devices'][i]['state'] == 'on') {
                    bedroomSwitch.checked = true;
                } else {
                    bedroomSwitch.checked = false;
                };
            } else if (response.data['devices'][i]['name'] === 'Garage Light') {
                const garageSwitch = document.getElementById('garageLightSwitch');
                if (response.data['devices'][i]['state'] == 'on') {
                    garageSwitch.checked = true;
                } else {
                    garageSwitch.checked = false;
                };  
            } else if (response.data['devices'][i]['name'] === 'Dining Room Table') {
                const diningSwitch = document.getElementById('diningLightSwitch');
                if (response.data['devices'][i]['state'] == 'on') {
                    diningSwitch.checked = true;
                } else {
                    diningSwitch.checked = false;
                };
            } else if (response.data['devices'][i]['name'] === 'String Lights') {
                const stringSwitch = document.getElementById('stringLightSwitch');
                if (response.data['devices'][i]['state'] == 'on') {
                    stringSwitch.checked = true;
                } else {
                    stringSwitch.checked = false;
                };
            } else if (response.data['devices'][i]['name'] === 'Drinking Lamp') {
                const lanternSwitch = document.getElementById('lanternLightSwitch');
                if (response.data['devices'][i]['state'] == 'on') {
                    lanternSwitch.checked = true;
                } else {
                    lanternSwitch.checked = false;
                };
            };
        };
        
});
}

const adjustLighting = (event) => {
    axios.post('api/smartthings/status', {
        light: event.target.id,
        state: event.target.checked
    })
    .then((response) => {
        console.log(response);
    })
};

const setCurrentDate = (dateInput) => {
    const t = new Date();
    const date = ('0' + t.getDate()).slice(-2);
    const month = ('0' + (t.getMonth() + 1)).slice(-2);
    const year = t.getFullYear();
    dateInput.value = `${year}-${month}-${date}`;
    changeDateHref();
}

const registerEvents = () => {
    venstarModeSetting();

    const dateInput = document.getElementById('dateInputTemp');
    setCurrentDate(dateInput);
    dateInput.addEventListener('input', changeDateHref);
    const lightingSwitch = document.getElementById('landscapeLightSwitch');
    lightingSwitch.addEventListener('click', adjustLandscapeLighting);
    const pineappleSwitch = document.getElementById('pineappleLightSwitch');
    pineappleSwitch.addEventListener('click', adjustLighting);
    const diningSwitch = document.getElementById('diningLightSwitch');
    diningSwitch.addEventListener('click', adjustLighting);
    const garageSwitch = document.getElementById('garageLightSwitch');
    garageSwitch.addEventListener('click', adjustLighting);
    const bedroomSwitch = document.getElementById('bedroomLightSwitch');
    bedroomSwitch.addEventListener('click', adjustLighting);
    const lanternSwitch = document.getElementById('lanternLightSwitch');
    lanternSwitch.addEventListener('click', adjustLighting);
    const stringSwitch = document.getElementById('stringLightSwitch');
    stringSwitch.addEventListener('click', adjustLighting);
    const heat_increase = document.getElementById('heatIncrease');
    const heat_decrease = document.getElementById('heatDecrease');
    const cool_increase = document.getElementById('coolIncrease');
    const cool_decrease = document.getElementById('coolDecrease');
    heat_increase.addEventListener('click', adjustSetTemperature);
    heat_decrease.addEventListener('click', adjustSetTemperature);
    cool_increase.addEventListener('click', adjustSetTemperature);
    cool_decrease.addEventListener('click', adjustSetTemperature);

    getGarageData();
    getSmartThingsData();
};
  
document.addEventListener('DOMContentLoaded', registerEvents);