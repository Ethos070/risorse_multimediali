const prenotazione = document.getElementById("prenotazione");
const box = document.getElementById("box");

function prenota() {
    document.getElementById("box").innerHTML += `
    <h2>Prenota</h2>
    <form action="#" method="post">
        <label for="data">Data prenotazione:</label>
        <input type="date" name="data_inizio" required>
        <input type="submit" value="submit">
    </form>`;
}