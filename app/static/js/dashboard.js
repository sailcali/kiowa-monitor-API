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
    }

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

const registerEvents = () => {
    const dateInput = document.getElementById('dateInputTemp');
    dateInput.addEventListener('input', changeDateHref);
  };
  
  document.addEventListener('DOMContentLoaded', registerEvents);
  