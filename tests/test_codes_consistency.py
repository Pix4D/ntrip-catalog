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

    def testit(id, name):
        id_exists = False
        for crs in crslist:
            if crs["auth_name"] + ":" + crs["code"] == id:
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
