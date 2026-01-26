# Example for NATRF2022

During the transition period until the Modernized NSRS in the USA, Canada and Mexico is fully adopted, NTRIP providers will have to provide corrections for the "old" and the "new" CRS during the transition period. This will inevitably cause confusion about which is the correct CRS to use with a given NTRIP mount point.

[NTRIP-catalog](https://ntrip-catalog.org) can help to automatically identify it, making the transition soft and easy.

The misalignment of the earth's center [by 2.2 meters](https://geodesy.noaa.gov/datums/newdatums/) in NAD83(2011)
make differences between 1 and 2 meters (3 to 6 feet) between NAD83(2011) and NATRF2022.
While the difference is not small, it is in the order of magnitude of many other errors, make it difficult for users to notice configuration errors immediately.

[NTRIP-catalog](https://ntrip-catalog.org) can help avoid configuration errors in the first place, as it can be used to select the correct CRS automatically based on the client device configuration (URL, port, mountpoint, position, ...)

These examples for the transition from `NAD83(2011)` to `NATRF2022` in the USA [https://beta.ngs.noaa.gov/](https://beta.ngs.noaa.gov/) show how easy it is to specify a service providing both systems allowing automatic client selection.

The NTRIP-catalog schema provides several methods to specify NTRIP services offered in multiple CRSs by the same provider. Here we show the two main ones:
 - Use different mountpoints in the same URL
 - Use different ports (or even hostnames) for the each CRS

Do not wait for `NATRF2022` (and its siblings `PATRF2022`, `CATRF2022` and `MATRF2022`) to be officially released.
You can include the configuration for `NAD83(2011)` now, and update it once you know the new data.

## Example using different mountpoints

Some providers will add more mountpoints to the existing ones.
The names make the difference between the CRSs.
Filtering by mountpoint name easily allows to choose the correct CRS.

```json
{
    "name": "RTK Sample",
    "description": "Service in port 8000 for both NAD83(2011) and NATRF2022",
    "urls": [
        "http://rtk.example.com:8000"
    ],
    "reference": {
        "url": "http://rtk.example.com/info"
    },
    "last_update": "2026-01-23",
    "streams": [
        {
            "filter": {
                "mountpoints": [
                    "FKP3",
                    "FKP3M",
                    "MAC3",
                    "MAC3M",
                    "VRS3",
                    "VRS3M"
                ]
            },
            "crss": [
                {
                    "id": "EPSG:6319",
                    "name": "NAD83(2011)",
                    "epoch": 2010.0
                }
            ],
            "description": "NAD83(2011)",
            "comments": "These mountpoints will be deprecated in 2028"
        },
        {
            "filter": {
                "mountpoints": [
                    "MAC3NATRF",
                    "MAC3MNATRF",
                    "VRS3NATRF",
                    "VRS3MNATRF"
                ]
            },
            "crss": [
                {
                    "id": "EPSG:10967",
                    "name": "NATRF2022",
                    "epoch": 2020.0
                }
            ],
            "description": "NATRF2022 from the Modernized NSRS in CONUS",
            "comments": "Added in 2026"
        }
    ]
}
```

## Example using different ports

Some providers will create a new access point, using a different port or even a different hostname.
This is probably useful to not extend mountpoint lists which are already very long.
In that case the configuration is straightforward, just adding a new URL with its data.

```json
[
    {
        "name": "Sample-NAD83(2011)",
        "description": "Service in port 8001 for NAD83(2011)",
        "urls": [
            "http://ntrip.example.com:8001"
        ],
        "reference": {
            "url": "http://ntrip.example.com/nad83"
        },
        "last_update": "2026-01-23",
        "streams": [
            {
                "filter": "all",
                "crss": [
                    {
                        "id": "EPSG:6319",
                        "name": "NAD83(2011)",
                        "epoch": 2010.0
                    }
                ]
            }
        ]
    },
    {
        "name": "Sample-NATR2F022",
        "description": "Service in port 8002 for NATRF2022",
        "urls": [
            "http://ntrip.example.com:8002"
        ],
        "reference": {
            "url": "http://ntrip.example.com/natrf2022"
        },
        "last_update": "2026-01-23",
        "streams": [
            {
                "filter": "all",
                "crss": [
                    {
                        "id": "EPSG:10967",
                        "name": "NATRF2022",
                        "epoch": 2020.0
                    }
                ]
            }
        ]
    }
]
```
