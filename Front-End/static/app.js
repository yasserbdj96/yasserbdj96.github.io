// app.js (loaded once for the entire app)

let appData = null;

async function loadDataOnce() {
    if (appData) return appData;

    try {
        let response;
        try {
            response = await fetch('https://yasserbdj96.pythonanywhere.com/data.json');
            if (!response.ok) throw new Error('Failed to load remote data');
            } catch (error) {
            console.warn('Remote fetch failed, falling back to local data:', error);
            response = await fetch('./data.json');
            }

        appData = await response.json();
        //console.log(data);

        //const response = await fetch('./data.json');
        //appData = await response.json();
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