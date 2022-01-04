
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
    if (current_month > 4 && current_month < 10) {
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
        axios.post('http://192.168.86.31/change-state', {
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
            axios.post('http://192.168.86.31/change-state', {
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
    axios.get('http://192.168.86.31/get-status')
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
    } else if (event.target.id == 'heatDecrease') {
        heatElement.value = parseInt(heatElement.value) - 1
    } else if (event.target.id == 'coolIncrease') {
        coolElement.value = parseInt(coolElement.value) + 1
    } else if (event.target.id == 'heatDecrease') {
        coolElement.value = parseInt(coolElement.value) - 1
    };
}

const registerEvents = () => {
    venstarModeSetting();
    const dateInput = document.getElementById('dateInputTemp');
    dateInput.addEventListener('input', changeDateHref);
    const lightingSwitch = document.getElementById('landscapeLightSwitch');
    lightingSwitch.addEventListener('click', adjustLandscapeLighting);
    const heat_increase = document.getElementById('heatIncrease');
    const heat_decrease = document.getElementById('heatDecrease');
    const cool_increase = document.getElementById('coolIncrease');
    const cool_decrease = document.getElementById('coolDecrease');
    heat_increase.addEventListener('click', adjustSetTemperature);
    heat_decrease.addEventListener('click', adjustSetTemperature);
    cool_increase.addEventListener('click', adjustSetTemperature);
    cool_decrease.addEventListener('click', adjustSetTemperature);

    getGarageData();
};
  
  document.addEventListener('DOMContentLoaded', registerEvents);
  