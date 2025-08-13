"use strict";

let g_data = null

function submit_details(form) {
    let url = new URL(location);
    function process_key(key, uppercase) {
        let v = form.elements[key].value;
        if (uppercase)
            v = v.toUpperCase()
        if (v) {
            url.searchParams.set(key, v);
        } else {
            url.searchParams.delete(key);
        }
    }
    process_key('mountpoint');
    process_key('country', true);
    process_key('latitude');
    process_key('longitude');
    window.history.replaceState('', '', url.toString());
}

function paramsToDic(location) {
    let url = new URL(location);
    url.searchParams.set('hh', "asdf");
    let dic = {};
    for (let k of url.searchParams.keys()) {
        dic[k] = url.searchParams.get(k);
    }
    console.log(url.toString())
    let a = url.toJSON()
    console.log(a)
    return dic;
}

function init_search() {
    const params = paramsToDic(window.location);
    function fill_value(key) {
        document.querySelector(`#${key}`).value = params[key] || "";
    }
    if (Object.keys(params).length) {
        ['url', 'port'].forEach(e => fill_value(e))

        fetch('../dist/ntrip-catalog.json', {
            method: "GET",
        })
        .then(response => response.json())
        .then(data => {
            g_data = data;
            let entry = null
            for (let i = 0; i < data.entries.length && entry==null; i++) {
                for (let j = 0; j < data.entries[i].urls.length; j++) {
                    let url = data.entries[i].urls[j];
                    if (url == "http://" + params.url + ":" + params.port) {
                        entry = data.entries[i];
                        document.querySelector('#entry_content').textContent = JSON.stringify(entry, null, 4);
                        document.querySelector('#entry_name').textContent = entry.name;
                        document.querySelector('#entry_description').textContent = entry.description;
                        document.querySelector('#entry_ref').innerHTML = `<a href="${entry.reference.url}" target="_blank">${entry.reference.url}</a>`;
                        break;
                    }
                }
            }
            if (entry) {
                ['mountpoint', 'country', 'latitude', 'longitude'].forEach(e => fill_value(e))
            }
        });
    }
}
