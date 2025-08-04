import warnings

import pycurl

from scripts import query as ntrip_query


def test_spain_ign_2101():
    try:
        url = "http://ergnss-tr.ign.es:2101"
        json_data = ntrip_query.load_json()
        entry = ntrip_query.search_url_in_data(url, json_data)
        assert entry

        mountpoint = "CERCANA3"
        crs = ntrip_query.filter_crs(entry, url, mountpoint, 40, -1.5)
        assert crs
        assert crs["id"] == "EPSG:7931"
        assert crs["name"] == "ETRF2000"

        crs = ntrip_query.filter_crs(entry, url, mountpoint, 28, -16)
        assert crs
        assert crs["id"] == "EPSG:4080"
        assert crs["name"] == "REGCAN95"
    except pycurl.error as e:
        warnings.warn(UserWarning("pycurl exception " + str(e)))


def test_spain_ign_2102():
    url = "http://ergnss-tr.ign.es:2102"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    try:
        mountpoint = "IGNE3M"  # Madrid - IGN
        crs = ntrip_query.filter_crs(entry, url, mountpoint, 40, -1.5)
        assert crs
        assert crs["id"] == "EPSG:7931"
        assert crs["name"] == "ETRF2000"

        mountpoint = "IZAN3M"  # Izana, Tenerife
        crs = ntrip_query.filter_crs(entry, url, mountpoint, 28, -16)
        assert crs
        assert crs["id"] == "EPSG:4080"
        assert crs["name"] == "REGCAN95"
    except pycurl.error as e:
        warnings.warn(UserWarning("pycurl exception " + str(e)))


def test_vrsnow_de_2101_countries():
    try:
        url = "http://vrsnow.de:2101"
        json_data = ntrip_query.load_json()
        entry = ntrip_query.search_url_in_data(url, json_data)
        assert entry

        crs = ntrip_query.filter_crs(entry, url, "TVN_RTCM_31", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:10283"
        assert crs["name"] == "ETRS89/DREF91/2016"

        crs = ntrip_query.filter_crs(entry, url, "TVN_CMR_X_GPS_GLO", 0, 0)
        assert crs
        assert crs["id"] == "EPSG:10283"
        assert crs["name"] == "ETRS89/DREF91/2016"
    except pycurl.error as e:
        warnings.warn(UserWarning("pycurl exception " + str(e)))
