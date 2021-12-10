const venstarModeSetting = () => {
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
};
venstarModeSetting();
const changeDateHref = () => {
    const dateInput = document.getElementById("dateInput").value;
    const link = document.getElementById("dateButton");
    console.log(dateInput)
    link.setAttribute('href', "/temps/"+dateInput);
}

const registerEvents = () => {
    
    const dateInput = document.getElementById('dateInput');
    dateInput.addEventListener('input', changeDateHref);
  };
  
  document.addEventListener('DOMContentLoaded', registerEvents);
  