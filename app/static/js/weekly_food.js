const meal_names = ['Breakfast', 'Lunch', 'Dinner']
const days_of_week = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

const addDay = (date, days) => {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

const addData = (event) => {
    var column_dates = [new Date()]
    for (var i=0; i<5; i++) {
        column_dates.push(addDay(column_dates[i], 1))
    }
    // var button_date = column_dates[event.target.id[7]-1].toISOString().substring(0, 10);
    var button_date = new Date(column_dates[event.target.id[7]-1].getTime() - (column_dates[event.target.id[7]-1].getTimezoneOffset() * 60000)).toISOString().substring(0, 10);
    
    var button_meal = meal_names[event.target.id[6]]
    const new_date = document.getElementById('date');
    new_date.value = button_date
    const new_meal = document.getElementById('meal');
    new_meal.value = button_meal
}

const fill_tables = () => {

    const tableHeaderElements = document.getElementById('table-header').children;
    var column_dates = [new Date()]
    for (var i=0; i<5; i++) {
        tableHeaderElements[i+1].innerHTML = days_of_week[column_dates[i].getDay()]
        column_dates.push(addDay(column_dates[i], 1))
    }
    
    const tableBody = document.getElementById('table-body');

    var body_date = ''
    for (var r=0; r<3; r++) {
        var row = tableBody.insertRow(r);
        var cell = row.insertCell(0);
        cell.innerHTML = meal_names[r];
        for (var c=1; c<6; c++) {
            body_date = new Date(column_dates[c-1].getTime() - (column_dates[c-1].getTimezoneOffset() * 60000)).toISOString().substring(0, 10);
            console.log(column_dates[c-1])
            console.log(body_date)
            cell = row.insertCell(c);
            if (data[body_date]) {
                for (var f=0; f<data[body_date].length; f++) {
                if (data[body_date][f]['meal'] === meal_names[r]) {
                    
                    cell.innerHTML = '<button type="button" id="button' + r + c + '">' + data[body_date][f]['food'] + '</button>';
                    break
                } else {
                    cell.innerHTML = '<button type="button" id="button' + r + c + '">Add Data</button>'
                };
            };
            } else {
                cell.innerHTML = '<button type="button" id="button' + r + c + '">Add Data</button>'
            }
            cell.addEventListener('click', addData);
        }
    };
    console.log(column_dates)
}

fill_tables();
const registerEvents = () => {

    // const dateInput = document.getElementById('dateInputTemp');
    // dateInput.addEventListener('input', changeDateHref);
};

document.addEventListener('DOMContentLoaded', registerEvents);