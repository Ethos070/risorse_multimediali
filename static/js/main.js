const date = new Date();

let day = date.getDate();
let month = date.getMonth() + 1;
let year = date.getFullYear();

// This arrangement can be altered based on how we want the date's format to appear.
let currentDate = `${year}-${month}-${day}`;

function prenota() {
    document.getElementById("box").innerHTML += `
    <h2>Prenota</h2>
    <form action="#" method="post">
        <label for="data">Data prenotazione:</label>
        <input type="date" name="data_inizio" min="${currentDate}" required>
        <input type="submit" value="submit">
    </form>`;
}
