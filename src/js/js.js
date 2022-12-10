//links
function links(res){
    var links_html="";
    for (let i = 0; i < res["links"].length; i++) {
        var icon=res["links"][i]["icon"];
        var url=res["links"][i]["url"];
        links_html+='<a class="transform hover:-translate-y-1 active:translate-y-1" href="'+url+'"><img src="'+icon+'"></a>';
    }
     document.getElementById("links").innerHTML=links_html;
}

//read_json();
function read_json(){
    const xhr = new XMLHttpRequest();
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                const res = JSON.parse(xhr.responseText);
                
                //links
                links(res);
                
            };
        }
    };
    xhr.open('GET', "./src/json/data.json", true);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.send(null);
}