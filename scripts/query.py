"""
this script tests a url, mountpoint and location against ntrip.catalog.json
"""

import argparse
import json
import logging
import os
import pathlib
from io import BytesIO
from urllib.parse import urlparse

import pycurl

local_path = pathlib.Path(__file__).parent.parent.resolve().as_posix()

logger = logging.getLogger(__name__)


def get_streams_from_server(url):
    logger.debug(f"+++ Connecting to {url}")
    sio = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.TIMEOUT, 10)
    curl.setopt(pycurl.CONNECTTIMEOUT, 3)
    curl.setopt(pycurl.WRITEFUNCTION, sio.write)
    curl.setopt(
        pycurl.HTTPHEADER, ["Ntrip-Version: Ntrip/2.0", "User-Agent: NTRIPClient/1.0"]
    )

    try:
        curl.perform()
        curl.close()
        try:
            return sio.getvalue().decode().splitlines()
        except Exception:
            return sio.getvalue().decode("iso-8859-1").splitlines()

    except pycurl.error as e:
        logger.error("pycurl exception", e)
        raise pycurl.error(e)
    except Exception as e:
        logger.error("exception", e)
        raise Exception(e)


def get_str_line_from_server(streams_from_server, mountpoint):
    for line in streams_from_server:
        splitted = line.split(";")
        if len(splitted) > 2 and splitted[0] == "STR" and splitted[1] == mountpoint:
            return splitted
    return None


def load_json(json_path=None):
    path = json_path
    if not path:
        path = os.path.join(local_path, "dist", "ntrip-catalog.json")
    with open(path) as f:
        return json.load(f)


def normalize_lon(lon):
    while lon > 180:
        lon -= 360
    while lon < -180:
        lon += 360
    return lon


def normalize_bbox(bbox):
    return [normalize_lon(bbox[0]), bbox[1], normalize_lon(bbox[2]), bbox[3]]


def point_in_bbox(point_lat, point_lon, bbox):
    if point_lat > bbox[3] or point_lat < bbox[1]:
        return False

    point_lon = normalize_lon(point_lon)
    bbox = normalize_bbox(bbox)
    if bbox[0] > bbox[2]:
        # crossing antimeridian
        return point_lon <= bbox[0] or point_lon >= bbox[2]
    else:
        return point_lon >= bbox[0] and point_lon <= bbox[2]


def filter_crs(
    json_entry,
    url,
    mountpoint,
    rover_lat,
    rover_lon,
    rover_country=None,
    sourcetable_lines_splitted=None,
):
    def filter_by_rover(crss):
        for crs in crss:
            if "rover_bbox" in crs:
                if point_in_bbox(rover_lat, rover_lon, crs["rover_bbox"]):
                    return crs
            elif "rover_countries" in crs:
                if rover_country and rover_country in crs["rover_countries"]:
                    return crs
            else:
                return crs
        return None

    def crss_from_stream(stream, server_streams):
        crss = stream["crss"]
        stream_filter = stream["filter"]
        if "mountpoints" in stream_filter:
            if mountpoint in stream_filter["mountpoints"]:
                return crss
        else:
            if not server_streams:
                server_streams += get_streams_from_server(url)
            line = get_str_line_from_server(server_streams, mountpoint)
            if not line or len(line) < 10:
                return None
            country = line[8]
            base_lat = float(line[9])
            base_lon = normalize_lon(float(line[10]))

            if country in stream_filter.get("countries", []):
                return crss

            for bbox in stream_filter.get("lat_lon_bboxes", []):
                if point_in_bbox(base_lat, base_lon, bbox):
                    return crss

    server_streams = [*sourcetable_lines_splitted] if sourcetable_lines_splitted else []

    for stream in json_entry["streams"]:
        crss = crss_from_stream(stream, server_streams)
        if crss:
            crs = filter_by_rover(crss)
            if crs:
                return crs

    return None


def search_url_in_data(url, data):
    for entry in data["entries"]:
        if url in entry["urls"]:
            return entry
    return None


def get_url_from_args(args):
    url = args.url
    if not url.startswith("http"):
        url = "http://" + url
    parsed = urlparse(args.url)
    hostname = parsed.hostname
    if not hostname:
        raise Exception(f"{url} is not a valid URL")
    port = parsed.port or args.port or 2101
    res = parsed.scheme + "://" + parsed.hostname + ":" + str(port)
    return res


def query_ntrip_catalog(args):
    url = get_url_from_args(args)
    if args.log_streams:
        logger.info(f"Connecting to {url}")
        logger.info("\n".join(get_streams_from_server(url)))
    json_data = load_json(args.json_path)
    entry = search_url_in_data(url, json_data)
    if not entry:
        # the url is not found among the entries
        return None

    sourcetable_lines_splitted = None
    if args.sourcetable:
        if os.path.exists(os.path(args.sourcetable)):
            with open(args.sourcetable) as f:
                sourcetable_lines_splitted = f.read()
        else:
            sourcetable_lines_splitted = args.sourcetable

        if "STR" not in sourcetable_lines_splitted:
            raise Exception("Cannot find STR in provided sourcetable")
        else:
            sourcetable_lines_splitted = sourcetable_lines_splitted.splitlines()

    crs = filter_crs(
        entry,
        url,
        args.mountpoint,
        args.rover_lat,
        args.rover_lon,
        args.rover_country,
        sourcetable_lines_splitted,
    )
    return crs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test a url, mountpoint and location against ntrip.catalog.json."
    )

    parser.add_argument(
        "--json-path",
        type=str,
        help="Location of ntrip-catalog.json. Defaults to ../dist/ntrip-catalog.json",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL of the NTRIP server",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port NTRIP server. It can be also included in the URL",
        default=2101,
    )
    parser.add_argument(
        "--mountpoint",
        help="Mountpoint used. Mandatory field",
        type=str,
    )
    parser.add_argument(
        "--rover-lat",
        help="Rover latitude",
        type=float,
    )
    parser.add_argument(
        "--rover-lon",
        help="Rover longitude",
        type=float,
    )
    parser.add_argument(
        "--rover-country",
        help="Rover country (3 letter code)",
        type=float,
    )
    parser.add_argument(
        "--sourcetable",
        help=(
            "Content of the source table or filepath to it."
            " When provided no http request is done."
        ),
        type=str,
    )
    parser.add_argument(
        "--log-streams",
        help="Logs all the STR.",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    crs = query_ntrip_catalog(args)
    logger.info(crs)


if __name__ == "__main__":
    main()
