
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
    if (current_month > 2 && current_month < 10) {
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
    if (data.landscape_state === 'ON') {
        axios.post('landscape/change-state', {
            state: 0
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
            state: 1
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
        const garageTempElement = document.getElementById("garageTemperature");
        const slider = document.getElementById("landscapeLightSwitch");
        garageTempElement.innerHTML = "Garage Temp: " + parseInt(response.data['temperature']) + "*F";
        
        if (response.data['lighting_state'] == 1) {
            slider.checked = true
        } else {
            slider.checked = false
        }
        var labelName = document.getElementById('landscapelightsLabel');
        labelName.classList.remove("crossedOutLabel");
        addLandscapeListener();
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
            var switchName = response.data['devices'][i]['name'].toLowerCase();
            switchName = switchName.replace(/\s+/g, '');
            var Switch = document.getElementById(switchName + 'Switch');
            
            if (response.data['devices'][i]['state'] != 'OFFLINE') {
                var labelName = document.getElementById(switchName + 'Label');
            }
            labelName.classList.remove("crossedOutLabel");
            if (response.data['devices'][i]['state'] == 'on') {
                Switch.checked = true;
            } else {
                Switch.checked = false;
            };
        addLightListeners();
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

const addLandscapeListener = () => {
    const lightingSwitch = document.getElementById('landscapeLightSwitch');
    lightingSwitch.addEventListener('click', adjustLandscapeLighting);
}

const addLightListeners = () => {
    const pineappleSwitch = document.getElementById('pineappleSwitch');
    pineappleSwitch.addEventListener('click', adjustLighting);
    const diningSwitch = document.getElementById('diningroomSwitch');
    diningSwitch.addEventListener('click', adjustLighting);
    const garageSwitch = document.getElementById('garageSwitch');
    garageSwitch.addEventListener('click', adjustLighting);
    const bedroomSwitch = document.getElementById('bedroomSwitch');
    bedroomSwitch.addEventListener('click', adjustLighting);
    const lanternSwitch = document.getElementById('lanternSwitch');
    lanternSwitch.addEventListener('click', adjustLighting);
    const stringSwitch = document.getElementById('stringlightsSwitch');
    stringSwitch.addEventListener('click', adjustLighting);
    const frontdoorSwitch = document.getElementById('frontdoorSwitch');
    frontdoorSwitch.addEventListener('click', adjustLighting);
}

const registerEvents = () => {
    venstarModeSetting();

    const dateInput = document.getElementById('dateInputTemp');
    setCurrentDate(dateInput);
    dateInput.addEventListener('input', changeDateHref);
    
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