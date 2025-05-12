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


// HTML validation check function
const isValidHTML = (str) => {
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(str, "text/html");
        return Array.from(doc.body.childNodes).some(node => node.nodeType === 1); // Check for element nodes
    } catch (e) {
        return false;
    }
};