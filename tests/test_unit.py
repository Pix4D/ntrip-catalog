import json
from unittest import mock

from scripts import query as ntrip_query

server_path = "scripts.query.get_streams_from_server"


def mock_server(filename):
    def get_data(url):
        with open(filename) as f:
            mock_ntrip_server_data = json.load(f)

        return mock_ntrip_server_data[url]

    return get_data


def test_spain_ign_2101_mountpoint():
    url = "http://ergnss-tr.ign.es:2101"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    mountpoint = "CERCANA3"
    with mock.patch(
        server_path, side_effect=mock_server("./tests/data/ign_es.json")
    ) as mokked:
        crs = ntrip_query.filter_crs(entry, url, mountpoint, 40, -1)
        assert crs
        assert crs["id"] == "EPSG:7931"
        assert crs["name"] == "ETRF2000"

        crs = ntrip_query.filter_crs(entry, url, mountpoint, 28, -16)
        assert crs
        assert crs["id"] == "EPSG:4080"
        assert crs["name"] == "REGCAN95"

    # if stream is filtered by mountpoint,
    #  the method get_streams_from_server is not called.
    mokked.assert_not_called()


def test_spain_ign_2102_lat_lon():
    url = "http://ergnss-tr.ign.es:2102"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    with mock.patch(
        server_path, side_effect=mock_server("./tests/data/ign_es.json")
    ) as mokked:
        crs = ntrip_query.filter_crs(entry, url, "VCIA3M", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:7931"
        assert crs["name"] == "ETRF2000"

        crs = ntrip_query.filter_crs(entry, url, "IZAN3M", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:4080"
        assert crs["name"] == "REGCAN95"

    # check that we are actually using the mock, and not the http request
    mokked.assert_called()


def test_vrsnow_de_2101_countries():
    url = "http://vrsnow.de:2101"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    with mock.patch(
        server_path, side_effect=mock_server("./tests/data/vrsnow.de.json")
    ) as mokked:
        crs = ntrip_query.filter_crs(entry, url, "TVN_RTCM_31", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:10283"
        assert crs["name"] == "ETRS89/DREF91/2016"

        crs = ntrip_query.filter_crs(entry, url, "TVN_CMR_X_GPS_GLO", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:10283"
        assert crs["name"] == "ETRS89/DREF91/2016"

    # check that we are actually using the mock, and not the http request
    mokked.assert_called()


def test_rover_countries():
    url = "http://rtk.topnetlive.com:2101"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    with mock.patch(
        server_path, side_effect=mock_server("./tests/data/vrsnow.de.json")
    ) as mokked:
        crs = ntrip_query.filter_crs(entry, url, "StarPoint2+RTK", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:9989"
        assert crs["name"] == "ITRF2020"

        crs = ntrip_query.filter_crs(entry, url, "NET_MSM5", 0, 0, "CHE")
        assert crs
        assert crs["id"] == "EPSG:7923"
        assert crs["name"] == "ETRF93"

        crs = ntrip_query.filter_crs(entry, url, "NET_MSM5", 0, 0, "DEU")
        assert crs
        assert crs["id"] == "EPSG:10283"
        assert crs["name"] == "ETRS89/DREF91/2016"

        crs = ntrip_query.filter_crs(entry, url, "NET_MSM5", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:4937"
        assert crs["name"] == "ETRS89"

    mokked.assert_not_called()


def test_rover_antimeridian():
    url = "http://polaris.pointonenav.com:2101"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    # "id": "EPSG:6321",
    # "name": "NAD83(PA11)",
    # "rover_bbox": [
    #     157.47,
    #     -17.56,
    #     -151.27,
    #     31.8
    # ],
    # "description": "Hawaii"

    crs = ntrip_query.filter_crs(entry, url, "POLARIS_LOCAL", 10, 170)
    assert crs
    assert crs["id"] == "EPSG:6321"
    assert crs["name"] == "NAD83(PA11)"

    crs = ntrip_query.filter_crs(entry, url, "POLARIS_LOCAL", 10, -170)
    assert crs
    assert crs["id"] == "EPSG:6321"
    assert crs["name"] == "NAD83(PA11)"

    crs = ntrip_query.filter_crs(entry, url, "POLARIS_LOCAL", 10, 150)
    assert crs is None

    crs = ntrip_query.filter_crs(entry, url, "POLARIS_LOCAL", 10, -140)
    assert crs is None
