# Example for NATRF2022

During the adoption of the Modernized NSRS in the USA, Canada and Mexico, there can be confusion about the CRS used for the corrections.
NTRIP providers will provide the service for the "old" and the "new" CRS during the transition period.
[NTRIP-catalog](https://ntrip-catalog.org) can help to automatically identify it, making the transition soft and easy.

These examples for the transition from `NAD83(2011)` to `NATRF2022` in the USA [https://beta.ngs.noaa.gov/](https://beta.ngs.noaa.gov/) show how easy it is to identify them properly.

There are several options to make the difference. Here we show the two main ones:
 - Use different mountpoints in the same URL:port
 - Use different port (or even URL) for the new CRS

## Example using different mountpoints
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
