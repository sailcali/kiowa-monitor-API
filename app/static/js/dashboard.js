
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
    const newDelay = document.getElementById("delayDateTime").value
    var delay = 0
    if (newDelay != '') {
        delay = newDelay
    }
    if (data.landscape_state === 'ON') {
        axios.post('http://192.168.86.31/change-state', {
            state: 0,
            delay_time: delay
          })
          .then(function (response) {
            console.log(response);
          })
          .catch(function (error) {
            console.log(error);
          });
        } else {
            axios.post('http://192.168.86.31/change-state', {
            state: 1,
            delay_time: delay
          })
          .then(function (response) {
            console.log(response);
          })
          .catch(function (error) {
            console.log(error);
          });
        };
        
    };

const registerEvents = () => {
    const dateInput = document.getElementById('dateInputTemp');
    dateInput.addEventListener('input', changeDateHref);
    const lightingSwitch = document.getElementById('landscapeLightSwitch');
    lightingSwitch.addEventListener('click', adjustLandscapeLighting);
  };
  
  document.addEventListener('DOMContentLoaded', registerEvents);
  