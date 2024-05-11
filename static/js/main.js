const date = new Date();

let day = date.getDate();
let month = date.getMonth() + 1;
let year = date.getFullYear();

if(Number(day)<10){
	day = "0" + day
}
if(Number(month)<10){
	month = "0" + month
}
let currentDate = `${year}-${month}-${day}`;

let b = 0;

function prenota() {
    if(b==0){
    document.getElementById("box").innerHTML += `
    <h2>Prenota</h2>
    <form action="#" method="post">
        <label for="data">Data prenotazione:</label>
        <input type="date" name="data_inizio" min="${currentDate}" required>
        <input type="submit" value="submit">
    </form>`;
    b = b + 1;
    }
}
