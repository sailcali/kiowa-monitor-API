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
  