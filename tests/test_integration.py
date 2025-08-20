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


def test_https():
    url = "https://polaris.pointonenav.com:2102"
    json_data = ntrip_query.load_json()
    entry = ntrip_query.search_url_in_data(url, json_data)
    assert entry

    try:
        mountpoint = "POLARIS_LOCAL"
        crs = ntrip_query.filter_crs(entry, url, mountpoint, 40, -1.5)
        assert crs
        assert crs["id"] == "EPSG:7931"
        assert crs["name"] == "ETRF2000"

        crs = ntrip_query.filter_crs(
            entry, url, mountpoint, 35, 137, rover_country="JPN"
        )
        assert crs
        assert crs["id"] == "EPSG:6667"
        assert crs["name"] == "JGD2011"

        crs = ntrip_query.filter_crs(entry, url, mountpoint, 5, 1)
        assert crs is None

        mountpoint = "POLARIS"
        crs = ntrip_query.filter_crs(entry, url, mountpoint, 28, -16)
        assert crs
        assert crs["id"] == "EPSG:7912"
        assert crs["name"] == "ITRF2014"
    except pycurl.error as e:
        warnings.warn(UserWarning("pycurl exception " + str(e)))


def test_sapos():
    # there were problems with the User-Agent.
    url = "http://www.sapos-ntrip.de:2101"
    try:
        sourcetable = ntrip_query.get_streams_from_server(url)
        assert len(sourcetable) > 2
        for line in sourcetable:
            assert line.startswith(("CAS;", "NET;", "STR;", "ENDSOURCETABLE"))
        json_data = ntrip_query.load_json()
        entry = ntrip_query.search_url_in_data(url, json_data)
        crs = ntrip_query.filter_crs(entry, url, "blah", 40, -1.5)
        assert crs

    except pycurl.error as e:
        warnings.warn(UserWarning("pycurl exception " + str(e)))
