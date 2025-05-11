// app.js (loaded once for the entire app)

let appData = null;

async function loadDataOnce() {
    if (appData) return appData;

    try {
        const response = await fetch('./data.json');
        appData = await response.json();
        return appData;
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

window.loadDataOnce = loadDataOnce;
