"use strict";

let g_data = null
let g_entry = null
let g_url = null
let g_fetched_sourcetable = null
let g_fetched_sourcetable_status = null

function split_by_lines(text) {
    let line_endings = ["\r\n","\n\r","\r","\n"], line_ending = "";
    for(line_ending of line_endings){
        if (text.indexOf(line_ending)!=-1){
            break;
        }
    }
    return text.split(line_ending);
}

function get_str_line_from_server(streams_from_server, mountpoint) {
    if (!streams_from_server)
        return null;
    const lines = split_by_lines(streams_from_server);
    for (const line of lines) {
        const splitted = line.split(";")
        if (splitted.length > 2 && splitted[0] == "STR" && splitted[1] == mountpoint)
            return splitted
    }
    return null;
}

function normalize_lon(lon) {
    while (lon > 180)
        lon -= 360
    while (lon < -180)
        lon += 360
    return lon
}


function normalize_bbox(bbox) {
    return [normalize_lon(bbox[0]), bbox[1], normalize_lon(bbox[2]), bbox[3]]
}


function point_in_bbox(point_lat, point_lon, bbox) {
    if (point_lat > bbox[3] || point_lat < bbox[1])
        return false

    point_lon = normalize_lon(point_lon)
    bbox = normalize_bbox(bbox)
    if (bbox[0] > bbox[2]) {
        // crossing antimeridian
        return point_lon >= bbox[0] || point_lon <= bbox[2]
    } else {
        return point_lon >= bbox[0] && point_lon <= bbox[2]
    }
}

function _crss_from_stream(stream, mountpoint, url, server_streams) {
    const crss = stream["crss"]
    const stream_filter = stream["filter"]
    if (stream_filter == "all") {
        return crss;
    } else if ("mountpoints" in stream_filter) {
        if (stream_filter["mountpoints"].includes(mountpoint))
            return crss;
    } else {
        const line = get_str_line_from_server(server_streams, mountpoint)
        if (!line || line.length < 10) {
            console.error(`To process this service completely we need the SOURCETABLE from ${url}, that is not accesible`); // should we alert?
            return null;
        }
        const country = line[8];
        const base_lat = parseFloat(line[9]);
        const base_lon = normalize_lon(parseFloat(line[10]));

        if ((stream_filter["countries"] ?? []).includes(country))
            return crss;

        for (const bbox of (stream_filter["lat_lon_bboxes"] ?? [])) {
            if (point_in_bbox(base_lat, base_lon, bbox))
                return crss;
        }
    }
    return null;
}

function filter_crs(
    entry,
    url,
    mountpoint,
    rover_lat,
    rover_lon,
    rover_country=null) {

    function filter_by_rover(crss) {
        for (const crs of crss) {
            if ("rover_bbox" in crs) {
                if (isNaN(rover_lat) || isNaN(rover_lon)) {
                    console.error("Rover latitude and longitude needed for this configuration");
                    return null;
                }
                if (point_in_bbox(rover_lat, rover_lon, crs["rover_bbox"]))
                    return crs;
            } else if ("rover_countries" in crs) {
                if (!rover_country || !rover_country.length) {
                    console.warn("Rover 3 letter country code could be needed for this configuration");
                }
                if (rover_country && crs["rover_countries"].includes(rover_country))
                    return crs;
            } else {
                return crs;
            }
        }
        return null;
    }

    for (const stream of entry["streams"]) {
        const crss = _crss_from_stream(stream, mountpoint, url, g_fetched_sourcetable.content)
        if (crss) {
            const crs = filter_by_rover(crss)
            if (crs) {
                return crs
            }
        }
    }

    return null
}

function entry_needs_country_latlon(entry) {
    // check if any crs in the entry needs country or latlon
    // to require it in the input.
    let country = false;
    let latlon = false;
    for (const stream of entry["streams"]) {
        for (const crs of stream["crss"]) {
            if ("rover_bbox" in crs) {
                latlon = true;
            }
            if ("rover_countries" in crs) {
                country = true;
            }
        }
    }
    return [country, latlon];
}

function fill_mp_select(fetched_sourcetable) {
    let sel = document.querySelector('#mp_select');
    if (!fetched_sourcetable || !fetched_sourcetable.content) {
        sel.classList.add('hidden');
    }
    const lines = split_by_lines(fetched_sourcetable.content);
    for (const line of lines) {
        const splitted = line.split(";")
        if (splitted.length > 2 && splitted[0] == "STR") {
            const mp = splitted[1];
            let opt = document.createElement("option");
            opt.value = mp;
            opt.innerText = mp;
            sel.append(opt);
        }
    }
    sel.addEventListener('change', function() {
        document.querySelector('#mountpoint').value = this.value;
    });
    sel.removeAttribute("disabled");
}

function update_browser_url_with_params(form) {
    let url = new URL(location);
    function process_key(key, uppercase) {
        let v = form.elements[key].value;
        if (uppercase) {
            v = v.toUpperCase()
        }
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

// Event when Filter button is clicked or page is loaded with entry and mountpoint data
function submit_details(form) {
    document.querySelector('#crs_content').textContent = '';
    if (!form) {
        form = document.querySelector('#details_form');
    }
    update_browser_url_with_params(form);
    let crs = filter_crs(g_entry, g_url,
        form.elements.mountpoint.value,
        parseFloat(form.elements.latitude.value),
        parseFloat(form.elements.longitude.value),
        form.elements.country.value);
    if (crs) {
        if (crs.name)
        {
            document.querySelector('#crs_name').textContent = crs.name;
        }
        if (crs.id) {
            let auth_code = crs.id.split(':');
            let link = `https://spatialreference.org/ref/${auth_code[0].toLowerCase()}/${auth_code[1]}/`;
            document.querySelector('#crs_id').innerHTML = `<a href="${link}" target=_blank>${crs.id}</a>`;
        }
        if (crs.description)
        {
            document.querySelector('#crs_description').textContent = crs.description;
        }
        document.querySelector('#crs-ok').classList.remove("hidden");
        document.querySelector('#crs-not-ok').classList.add("hidden");

    } else {
        document.querySelector('#crs_name').textContent = '';
        document.querySelector('#crs_id').innerHTML = ''
        document.querySelector('#crs_description').textContent = '';

        document.querySelector('#crs-ok').classList.add("hidden");
        document.querySelector('#crs-not-ok').classList.remove("hidden");
    }
    document.querySelector('#crs_content').textContent = JSON.stringify(crs, null, 4);
}

function paramsToDic(location) {
    let url = new URL(location);
    let dic = {};
    for (let k of url.searchParams.keys()) {
        dic[k] = url.searchParams.get(k);
    }
    return dic;
}

function init_search() {
    const params = paramsToDic(window.location);
    function fill_value(key) {
        document.querySelector(`#${key}`).value = params[key] || "";
    }
    if (Object.keys(params).length) {
        ['url', 'port'].forEach(e => fill_value(e));
        ['https', 'proxy'].forEach(e => {if (params[e]) document.querySelector(`#${e}`).checked = true;})

        fetch('../dist/ntrip-catalog.json', {
            method: "GET",
        })
        .then(response => response.json())
        .then(data => {
            g_data = data;
            let entry = null
            const requested_url = (params.https ? "https" : "http") + "://" + params.url + ":" + params.port
            for (let i = 0; i < data.entries.length && entry==null; i++) {
                for (let j = 0; j < data.entries[i].urls.length; j++) {
                    let url = data.entries[i].urls[j];
                    if (url == requested_url) {
                        entry = data.entries[i];
                        g_entry = entry;
                        g_url = url;
                        document.querySelector('#entry_content').textContent = JSON.stringify(entry, null, 4);
                        document.querySelector('#entry_name').textContent = entry.name;
                        document.querySelector('#entry_description').textContent = entry.description;
                        document.querySelector('#entry_ref').innerHTML = `<a href="${entry.reference.url}" target="_blank">${entry.reference.url}</a>`;

                        ['mountpoint', 'country', 'latitude', 'longitude'].forEach(e => fill_value(e));
                        if (document.querySelector('#mountpoint').textContent)
                            document.querySelector('#crs_content').textContent = "... loading";

                        const [country, latlon] = entry_needs_country_latlon(entry);
                        document.querySelector(`#country`).required = country;
                        document.querySelector(`#latitude`).required = latlon;
                        document.querySelector(`#longitude`).required = latlon;

                        // We do this request via this service to avoid CORS problems.
                        // See that bumblebee is currently located in AWS, and some countries/services
                        // may lock (or allow) those URLs
                        let server_url = "https://api.webgis.pix4d.com/bumblebee/v0/ntrip/sourcetable"
                        if (params['proxy']) {
                            // add &proxy=on to use this local proxy
                            server_url = "http://localhost:8010";
                            console.log("Using", server_url)
                        }
                        fetch(server_url, {
                            method: "POST",
                            headers: {
                                "accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({ "url": url })
                        })
                        .then((response) => {
                            if (response.ok) {
                                return response.json();
                            }
                            console.log(response)
                            throw new Error('Something went wrong getting the soucetable for ' + url);
                        })
                        .then((json) => {
                            console.log("release:", json.release, "url:", json.url);
                            document.querySelector('#sourcetable_content').textContent = json.content;
                            g_fetched_sourcetable = json;
                            fill_mp_select(json);
                            //const invalid = ['#mountpo'].find(v => !document.querySelector(m).checkValidity())
                            if (document.querySelector('#mountpoint').checkValidity() && document.querySelector('#country').checkValidity())
                                submit_details();
                        })
                        .catch((error) => {
                            console.log(error)
                            document.querySelector('#crs_content').textContent = "--- error ---"
                            document.querySelector('#crs-not-ok').classList.remove("hidden");
                        });
                        break;
                    }
                }
            }
            if (entry) {
                document.querySelector('#url-ok').classList.remove("hidden");
            } else {
                document.querySelector('#url-not-ok').classList.remove("hidden");
            }
        });
    }
}
