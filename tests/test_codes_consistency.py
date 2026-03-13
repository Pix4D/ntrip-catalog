import json
import urllib.error
import urllib.request
import warnings

from scripts import query as ntrip_query

server_path = "scripts.query.get_streams_from_server"


def download_crslist():
    with urllib.request.urlopen("https://spatialreference.org/crslist.json") as f:
        crslist = json.load(f)
    return crslist


def test_codes():
    try:
        crslist = download_crslist()  # this may fail because it is an http request.
    except urllib.error.HTTPError as e:
        warnings.warn(UserWarning("exception " + str(e)))
        return

    renamed_systems = {
        "BH_ETRS89": "ETRS89-BIH [BH_ETRS89]",
        "LKS-92": "ETRS89-LVA [LKS-92]",
        "EST97": "ETRS89-EST [EST97]",
        "ETRS89/DREF91/2016": "ETRS89-DEU [ETRS89/DREF91/2016]",
        "SWEREF99": "ETRS89-SWE [SWEREF 99]",
        "RGF93 v2b": "ETRS89-FRA [RGF93 v2b]",
    }

    def testit(id, name):
        id_exists = False
        for crs in crslist:
            if crs["auth_name"] + ":" + crs["code"] == id:
                # in  PROJ 9.8.0 (March 2026) the lastest version of EPSG was included.
                # It has changes in the datum ensemble ETRS89, and renamed many
                # European CRSs, keeping the code.
                # During a transition period we will allow old an new names.
                # Usually as "ETRS89-xxx [old_name]", being xxx the country code.
                # As they are just a few, it is easier keeping here a small table.
                name = renamed_systems.get(name, name)
                assert crs["name"] == name

                # when systems with only 2D are added, change this test
                assert crs["type"] == "GEOGRAPHIC_3D_CRS"

                id_exists = True
                break
        assert id_exists

    json_data = ntrip_query.load_json()
    counter = 0
    for entry in json_data["entries"]:
        for stream in entry["streams"]:
            for crs in stream["crss"]:
                if crs["id"] and crs["name"]:
                    counter += 1
                    print(crs["id"], crs["name"])
                    testit(crs["id"], crs["name"])

    assert counter > 30  # We are testing something!
