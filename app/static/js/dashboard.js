
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
        for (let element of document.getElementsByClassName("winter")){
            element.style.display="none";
         }
    } else {
        for (let element of document.getElementsByClassName("summer")){
            element.style.display="none";
         }
    };
    
};
venstarModeSetting();

const changeDateHref = () => {
    const dateInput = document.getElementById("dateInputTemp").value;
    const link = document.getElementById("dateButtonTemp");
    console.log(dateInput)
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
        console.log(response.data)
        const garageTempElement = document.getElementById("garageTemperature");
        const landscapeStateElement = document.getElementById("landscapeState");
        const landscapeDelayElement = document.getElementById("landscapeDelaySetTime");
        const slider = document.getElementById("landscapeLightSwitch");
        garageTempElement.innerHTML = "Garage Temp: " + parseInt(response.data['temperature']) + "*F";
        landscapeDelayElement.innerHTML = "Current Delay Set: " + response.data['current_delay'];
        if (response.data['lighting_state'] == 1) {
            landscapeStateElement.innerHTML = "Landscape Lighting: ON"
            slider.checked = true
        } else {
            landscapeStateElement.innerHTML = "Landscape Lighting: OFF"
            slider.checked = false
        }
        
    })
}

const registerEvents = () => {
    getGarageData();
    const dateInput = document.getElementById('dateInputTemp');
    dateInput.addEventListener('input', changeDateHref);
    const lightingSwitch = document.getElementById('landscapeLightSwitch');
    lightingSwitch.addEventListener('click', adjustLandscapeLighting);
  
};
  
  document.addEventListener('DOMContentLoaded', registerEvents);
  