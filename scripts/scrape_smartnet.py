#!/usr/bin/env python3
import argparse
import json
import os
import pickle
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Constants
DATA_DIR = Path(__file__).parent.parent / "data" / "World"
CATALOG_JSON = DATA_DIR / "smartnet.json"
# Pickles to store intermediate data so we don't have to re-download everything
DEVICES_PICKLE = Path(__file__).parent / "devices.pkl"
CONNECTIONS_PICKLE = Path(__file__).parent / "connections.pkl"

DATUM_LOOKUP = {
    "NAD83(2011)": {"ReferenceFrame": "NAD83(2011)", "epsg_code": "EPSG:6319"},
    "NAD83(CSRS)v7": {
        "ReferenceFrame": "NAD83(CSRS)v7",
        "epsg_code": "EPSG:8254",
    },
    "CHTRS95": {
        "ReferenceFrame": "CHTRS95",
        "epsg_code": "EPSG:4933",
        "notes": "EPSG:4343 (CHTRF95 (3D)) is deprecated, replaced by EPSG:4933 (CHTRS95)",
    },
    "ETRS89/DREF91/2016": {
        "ReferenceFrame": "ETRS89/DREF91/2016",
        "epsg_code": "EPSG:10283",
    },
    "ETRS89": {"ReferenceFrame": "ETRS89", "epsg_code": "EPSG:4937"},
    "GDA2020": {"ReferenceFrame": "GDA2020", "epsg_code": "EPSG:7843"},
    "PL-ETRF2000": {"ReferenceFrame": "PL-ETRF2000", "epsg_code": "EPSG:9701"},
    "GGRS87": {
        "ReferenceFrame": "GGRS87",
        "epsg_code": "EPSG:4121",
        "notes": "The EPSG registry only contains an entry for the Geographic 2D CRS, no 3D",
    },
    "RDN": {"ReferenceFrame": "RDN", "epsg_code": "EPSG:6705"},
    "SWEREF99": {"ReferenceFrame": "SWEREF99", "epsg_code": "EPSG:4977"},
    "RGF93v2": {"ReferenceFrame": "RGF93v2", "epsg_code": "EPSG:9776"},
    "SKTRF2009": {
        "ReferenceFrame": "SKTRF2009",
        "epsg_code": "EPSG:7931",
        "notes": "SKTRF2009 = ETRF2000@2008.5",
    },
    "ETRF2000": {"ReferenceFrame": "ETRF2000", "epsg_code": "EPSG:7931"},
    "ITRF2014": {"ReferenceFrame": "ITRF2014", "epsg_code": "EPSG:7912"},
}


def make_stream_all(
    reference_frame: str, epoch: float, epsg: str, notes: str | None = None
) -> dict:
    """
    Build a single 'all'-filter stream, optionally carrying
    a per-CRS description from notes.
    """
    crs = {"id": epsg, "name": reference_frame, "epoch": float(epoch)}
    if notes:
        crs["description"] = notes

    return {"filter": "all", "crss": [crs]}


def make_stream_mountpoints(
    mountpoints: list[str],
    reference_frame: str,
    epsg: str,
    epoch: float | None = None,
    notes: str = "",
    comments: str = "",
) -> dict:
    """
    Build a mountpoint-filtered stream.  If `notes` is non-empty,
    it becomes the CRS-level description.
    """
    crs = {"id": epsg, "name": reference_frame}
    if epoch is not None:
        crs["epoch"] = float(epoch)
    if notes:
        crs["description"] = notes

    stream = {"filter": {"mountpoints": mountpoints}, "crss": [crs]}
    if comments:
        stream["comments"] = comments

    return stream


def make_entry(
    name: str,
    description: str,
    urls: list[str],
    reference_url: str,
    reference_comments: str,
    last_update: str,
    streams: list[dict],
) -> dict:
    """
    Build a catalog entry.
    """
    return {
        "name": name,
        "description": description,
        "urls": urls,
        "reference": {"url": reference_url, "comments": reference_comments},
        "last_update": last_update,
        "streams": streams,
    }


def fetch_manufacturer_devices() -> pd.DataFrame:
    """
    Fetch all manufacturer devices from the SmartNet website.
    """
    if DEVICES_PICKLE.exists():
        print("Loading cached manufacturer devices data...")
        with open(DEVICES_PICKLE, "rb") as f:
            return pickle.load(f)

    base_url = "https://www.smartnetna.com"
    api_url = base_url + "/script_page.cfm"
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": base_url,
            "Referer": base_url + "/resources_configuration.cfm",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "DNT": "1",
        }
    )

    r = session.get(base_url + "/resources_configuration.cfm", timeout=10)
    if not r.ok:
        print(f"[!] Failed to GET referrer page: {r.status_code}", file=sys.stderr)
        return None

    all_records = []
    columns = None

    for manufacturer_id in tqdm(range(1, 26), desc="Fetching manufacturer data"):
        payload = {
            "ScriptName": "ChangeManufacturerConnectionV2",
            "ManufacturerID": manufacturer_id,
        }

        try:
            resp = session.post(api_url, data=payload, timeout=10)
            if resp.status_code != 200:
                print(
                    f"[!] HTTP {resp.status_code} for ManufacturerID={manufacturer_id}",
                    file=sys.stderr,
                )
                continue

            js = resp.json()
            if columns is None:
                columns = js.get("COLUMNS", [])
                if not columns:
                    print(
                        f"[!] No COLUMNS key in JSON for ManufacturerID={manufacturer_id}",
                        file=sys.stderr,
                    )
                    continue

            for row in js.get("DATA", []):
                record = dict(zip(columns, row))
                all_records.append(record)

        except Exception as e:
            print(
                f"[!] Error for ManufacturerID={manufacturer_id}: {e}",
                file=sys.stderr,
            )
            continue

    if not all_records:
        print("[!] No data collected", file=sys.stderr)
        return None

    df = pd.DataFrame(all_records)

    with open(DEVICES_PICKLE, "wb") as f:
        pickle.dump(df, f)

    return df


def fetch_connection_info(m_id, r_id, region):
    """
    Fetch connection info for a given manufacturer, rover model, and region.
    """
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.smartnetna.com",
            "Referer": "https://www.smartnetna.com/resources_configuration.cfm",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "DNT": "1",
        }
    )

    max_retries = 3
    base_delay = 2
    resp = None

    for attempt in range(max_retries):
        try:
            r_prime = session.get(
                "https://www.smartnetna.com/resources_configuration.cfm",
                timeout=10,
            )
            r_prime.raise_for_status()

            resp = session.post(
                "https://www.smartnetna.com/script_page.cfm",
                data={
                    "ScriptName": "GetConnectionInfo",
                    "ManufacturerID": m_id,
                    "RoverModelID": r_id,
                    "CorrectionAreaID": region,
                    "DomainSupport": 1,
                },
                timeout=10,
            )
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            print(
                f"Attempt {attempt + 1}/{max_retries} failed for task ({m_id},{r_id},{region}): {e}",
                file=sys.stderr,
            )
            if attempt + 1 == max_retries:
                return []

            delay = base_delay * (2**attempt)
            print(f"Waiting {delay} seconds before retrying...", file=sys.stderr)
            time.sleep(delay)
    else:
        return []

    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    server_input = soup.find("input", id="ServerAddress")
    server_address = server_input["value"] if server_input else ""
    if not server_address:
        return []

    tbl = soup.find("table", class_="default-border-black")
    if not tbl:
        return []

    out = []
    for tr in tbl.find_all("tr")[1:]:
        cols = tr.find_all("td")
        if len(cols) == 5:
            port = cols[0].get_text(strip=True)
            mount = cols[1].get_text(strip=True)
            url = f"http://{server_address}:{port}"
            out.append(
                {
                    "ManufacturerID": m_id,
                    "RoverModelID": r_id,
                    "CorrectionAreaID": region,
                    "ServerAddress": server_address,
                    "Port": port,
                    "MountPoint": mount,
                    "CorrectionType": cols[2].get_text(strip=True),
                    "ReferenceFrame": cols[3].get_text(strip=True),
                    "Epoch": cols[4].get_text(strip=True),
                    "URL": url,
                }
            )
    return out


def process_device_connections(df_devices: pd.DataFrame) -> pd.DataFrame:
    """
    Fetch connection info for all devices in the manufacturer devices data.
    """
    if CONNECTIONS_PICKLE.exists():
        print("Loading cached connection data...")
        with open(CONNECTIONS_PICKLE, "rb") as f:
            return pickle.load(f)

    tasks = [
        (row["MANUFACTURERID"], row["RECORDID"], region)
        for _, row in df_devices.iterrows()
        for region in range(
            1, 120
        )  # This is just the min/max of the region IDs, some may be missing but this script will handle that.
    ]

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_connection_info, m, r, reg): (m, r, reg)
            for (m, r, reg) in tasks
        }
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Fetching connection info",
        ):
            try:
                recs = future.result()
                if recs:
                    results.extend(recs)
            except Exception as e:
                m, r, reg = futures[future]
                print(
                    f"Error processing task ({m},{r},{reg}): {e}",
                    file=sys.stderr,
                )

    df_connections = pd.DataFrame(results)

    with open(CONNECTIONS_PICKLE, "wb") as f:
        pickle.dump(df_connections, f)

    return df_connections


def clean_connection_data(
    df_conn_raw: pd.DataFrame, datum_lookup_dict: dict
) -> pd.DataFrame:
    """
    Clean the connection data, removing duplicates and standardizing reference frames.
    """
    df = df_conn_raw.copy()
    df["ReferenceFrame"] = df["ReferenceFrame"].str.replace(
        r"NAD83\(NA2011\)\(MYCS2\)", "NAD83(2011)", regex=True
    )
    df["ReferenceFrame"] = df["ReferenceFrame"].str.replace(
        r"(.+)?DREF91(.+)?", "ETRS89/DREF91/2016", regex=True
    )
    df["ReferenceFrame"] = df["ReferenceFrame"].str.replace(
        r"(.+)?DRFEF91(.+)?", "ETRS89/DREF91/2016", regex=True
    )
    df["ReferenceFrame"] = df["ReferenceFrame"].str.replace(
        "NAD83(CSRS)(version 7.1)", "NAD83(CSRS)v7", regex=False
    )
    df["ReferenceFrame"] = df["ReferenceFrame"].str.replace(
        "CHTRF95", "CHTRS95", regex=False
    )

    df["epsg_code"] = None
    df["notes"] = None
    for key, value in datum_lookup_dict.items():
        df.loc[df["ReferenceFrame"] == value["ReferenceFrame"], "epsg_code"] = value[
            "epsg_code"
        ]

    df = df.dropna(subset=["epsg_code"])

    if "ManufacturerID" in df.columns:
        df = df.drop(
            columns=[
                "ManufacturerID",
                "RoverModelID",
                "CorrectionAreaID",
                "ServerAddress",
                "Port",
                "CorrectionType",
            ]
        )

    return df.sort_values(by="URL")


def build_catalog_entries(
    df_cleaned: pd.DataFrame, datum_lookup_dict: dict, output_json_path: Path
):
    """
    Build the catalog entries. This contains the logic to categorize the URLs
    into uniform and non-uniform streams, and to build the entries for each.
    """
    service_name = "SmartNet"
    description = "Hexagon SmartNet RTK Network"
    reference_url = "https://www.smartnetna.com/resources_configuration.cfm"
    reference_desc = (
        "Scraped and generated from above page, with scripts/scrape_smartnet.py"
    )
    last_update = datetime.now().strftime("%Y-%m-%d")

    catalog = []
    unique_urls = df_cleaned["URL"].unique()
    df = df_cleaned
    uniform_urls = []
    nonuniform_urls = []

    # Categorize the URLs into uniform and non-uniform.
    # Uniform URLs have a single reference frame, epoch, and EPSG code for all mountpoints. These can use a "filter": "all" stream.
    # Non-uniform URLs have multiple reference frames, epochs, and EPSG codes for different mountpoints. These must use a "filter": "mountpoints" stream.
    for url in tqdm(unique_urls, desc="Categorizing URLs"):
        sub = df[df["URL"] == url]
        pairs = set(
            zip(
                sub["ReferenceFrame"],
                sub["Epoch"],
                sub["epsg_code"],
                sub["notes"],
            )
        )
        if len(pairs) == 1:
            uniform_urls.append((url, pairs.pop()))
            df.loc[df["URL"] == url, "_is_uniform"] = True
        else:
            df.loc[df["URL"] == url, "_is_uniform"] = False
            nonuniform_urls.append((url, pairs))

    df_uniform = df[df["_is_uniform"] is True]
    grouped = df_uniform.groupby(["ReferenceFrame", "Epoch"], sort=False)

    # Process uniform URLs, creating a "filter": "all" stream for each.
    # The majority of URLs are uniform, so this saves us from the output file being massive and redundant.
    for (reference_frame, epoch_str), group in tqdm(
        grouped, desc="Processing uniform URLs"
    ):
        urls = group["URL"].unique().tolist()
        epsg_str = datum_lookup_dict[reference_frame]["epsg_code"]
        notes_from_lookup = datum_lookup_dict[reference_frame].get("notes", None)

        stream = make_stream_all(
            reference_frame, epoch_str, epsg_str, notes=notes_from_lookup
        )
        entry = make_entry(
            f"{service_name} - {reference_frame}@{epoch_str}",
            description,
            urls,
            reference_url,
            reference_desc,
            last_update,
            [stream],
        )
        catalog.append(entry)

    # Process non-uniform URLs, creating a "filter": "mountpoints" stream for each.
    # This is the minority of URLs, so I decided that grouping them further was not worth the complexity.
    for url, pairs in tqdm(nonuniform_urls, desc="Processing non-uniform URLs"):
        sub = df[df["URL"] == url]
        streams = []

        for reference_frame, epoch_str, epsg_code_str, notes_from_pair in pairs:
            mask = (
                (sub["ReferenceFrame"] == reference_frame)
                & (sub["Epoch"] == epoch_str)
                & (sub["epsg_code"] == epsg_code_str)
                & (sub["notes"].fillna("") == (notes_from_pair or ""))
            )
            mountpoints = sorted(
                list(set(sub.loc[mask, "MountPoint"].astype(str).tolist()))
            )

            stream = make_stream_mountpoints(
                mountpoints=mountpoints,
                reference_frame=reference_frame,
                epsg=epsg_code_str,
                epoch=epoch_str,
                notes=(notes_from_pair or ""),
                comments="",
            )
            streams.append(stream)

        subdomain_regex = r".+\/\/([a-zA-Z0-9.-]+)"
        port_regex = r":([0-9]+)"

        subdomain_match = re.search(subdomain_regex, url)
        port_match = re.search(port_regex, url)
        subdomain = subdomain_match.group(1) if subdomain_match else "unknown_subdomain"
        port = port_match.group(1) if port_match else "unknown_port"

        entry = make_entry(
            name=f"{service_name} - {subdomain.upper()} - Port {port}",
            description=description,
            urls=[url],
            reference_url=reference_url,
            reference_comments=reference_desc,
            last_update=last_update,
            streams=streams,
        )
        catalog.append(entry)

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w") as f:
        json.dump(catalog, f, indent=4)

    print(f"Catalog successfully generated and saved to {output_json_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape SmartNet NTRIP data")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cached data and fetch fresh from API",
    )
    args = parser.parse_args()

    if args.no_cache:
        print("Cache disabled, fetching fresh data...")
        if DEVICES_PICKLE.exists():
            os.remove(DEVICES_PICKLE)
        if CONNECTIONS_PICKLE.exists():
            os.remove(CONNECTIONS_PICKLE)

    print("Starting script: Fetching manufacturer devices...")
    df_devices = fetch_manufacturer_devices()
    if df_devices is None:
        print("Failed to fetch manufacturer devices. Exiting.")
        sys.exit(1)

    print("Processing device connections...")
    df_connections_raw = process_device_connections(df_devices)

    print("Cleaning connection data...")
    df_cleaned = clean_connection_data(df_connections_raw, DATUM_LOOKUP)

    print("Building NTRIP catalog entries...")
    build_catalog_entries(df_cleaned, DATUM_LOOKUP, CATALOG_JSON)
    print("Script finished.")


if __name__ == "__main__":
    main()
