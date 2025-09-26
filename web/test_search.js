"use strict"
let list_checked = [];
let g_data = null;

function load_pages() {
    let counter = 0;
    let iframe = null;
    for (let test of g_data) {
        for (let check of test.checks) {
            let src = `./search.html?url=${test.url}&port=${test.port}&mountpoint=${check.mountpoint}`;
            if (test.https)
                src += '&https=on'
            for (const item of ['latitude', 'longitude', 'country']) {
                if (check[item] !== undefined)
                    src += `&${item}=${check[item]}`
            }
            iframe = document.getElementById(`iframe_${counter}`)
            const r = `res_${counter}`;
            iframe.onload = function () {
                document.getElementById(`${r}`).innerHTML = '+++';
                const loaded = 1 + parseInt(document.getElementById('loaded').innerText)
                document.getElementById('loaded').innerText = loaded;
                if (loaded == list_checked.length) {
                    document.getElementById('button_check').disabled = false;
                    run_checks();
                }
            }
            iframe.src = src;
            counter += 1;
        }
    }
    document.getElementById('button_load').disabled = true;
}

function run_checks() {
    let counter = 0;
    for (let test of g_data) {
        for (let check of test.checks) {
            let iframe = document.querySelector(`#iframe_${counter}`).contentWindow.document;
            let a = iframe.querySelector('#crs_content');
            if (iframe.querySelector('#crs_content').textContent.length > 0){
                let res = true;
                if (check.result === false) {
                    // didn't find a CRS
                    if (iframe.querySelector('#crs_content').textContent != 'null')
                        res = false;
                } else {
                    if (check.result.name) {
                        let name = iframe.querySelector('#crs_name');
                        if (name.innerText != check.result.name)
                            res = false;
                    }
                    if (check.result.id) {
                        let id = iframe.querySelector('#crs_id');
                        if (!id.innerHTML.includes(check.result.id))
                            res = false;
                    }
                }
                list_checked[counter] = res;
                document.querySelector(`#res_${counter}`).innerHTML = res ? '&#x2705;' : '&#x274C;';
                document.getElementById('checked').innerText = list_checked.filter(d => d).length
            }
            counter += 1;
        }
    }

    if (!list_checked.every(v => v !== ''))
        setTimeout(run_checks, 1000);
}


function init_test_search() {
    fetch('./test_search.json', {
        method: "GET",
    })
    .then(response => response.json())
    .then(data => {
        g_data = data;
        let counter = 0;
        for (let test of data) {
            for (let check of test.checks) {
                let iframe = document.createElement('iframe');
                let src = `./search.html?url=${test.url}&port=${test.port}&mountpoint=${check.mountpoint}`;
                if (test.https)
                    src += '&https=on'
                for (const item of ['latitude', 'longitude', 'country']) {
                    if (check[item] !== undefined)
                        src += `&${item}=${check[item]}`
                }
                //iframe.src = src;
                iframe.width = "50%";
                iframe.height="5";
                iframe.id= `iframe_${counter}`
                iframe.title = check.description;
                const desc = document.createElement('div');
                desc.innerHTML = `<a href="${src}" target=_blank>${check.description}</a>`;
                const res = document.createElement('div');
                res.id = "res_" + counter;
                res.innerHTML = '... &quest;'
                document.getElementById('iframes_list').appendChild(desc);
                document.getElementById('iframes_list').appendChild(res);
                document.getElementById('iframes_list').appendChild(iframe);
                counter += 1;
            }
        }
        list_checked = new Array(counter).fill('');
        document.getElementById('total').innerText = counter;
        document.getElementById('button_load').disabled = false;
    })
}
