# NTRIP-catalog
Catalog of NTRIP[^1] providers with CRS[^2] information.

## What is NTRIP-catalog
NTRIP-catalog is an [open source and open data repository](https://github.com/pix4d/ntrip-catalog) with the CRS information from multiple NTRIP service providers.
The data is stored as JSON files, so it can be easily parsed by any software.

Access it via its URL [ntrip-catalog.org](https://ntrip-catalog.org). The final json file is [here](https://ntrip-catalog.org/dist/ntrip-catalog.json).

## TL;DR
The purpose of the NTRIP-catalog is to make it easy for an application to find the correct CRS for a given provider URL, mountpoint and rover location.
The user needs to traverse the JSON file, filtering the content based on the given inputs to arrive at the correct CRS (assuming that it exists in this database).

## What is the problem with coordinate reference systems in the NTRIP and RTCM protocols?
Neither RTCM[^3] messages (as of version 3.3 of the standard), nor the NTRIP handshake include any clarification about the coordinate reference system (CRS) that applies to the corrected coordinates.
That can be a significant problem, because the geolocation difference between using one CRS or another can be big, much bigger than the accuracy claimed by RTK[^4] devices, which is around 2 cm.
For example, in Europe the difference between ETRS89 and ITRF2014 is about 80 cm, and growing.
(In reality, RTCM 3.4 has added a new message to declare the CRS, however we can expect it to take years until this is widely adopted.)

Selection of a CRS by the user to label coordinates in end applications is a constant source of error, which we aim to remove.
Some NTRIP service providers document the CRS used in their mountpoints in their web pages or user manuals,
while others do not document it at all, assuming it is well-known data, despite there existing hundreds of CRS definitions and for some of them,
multiple realizations.
In the end, many users do not know what the CRS is that they have to use, because either the information is not clearly disclosed by the provider, or the user lacks the skills to select the correct one.
To increase the confusion, in some countries the official CRS (usually an old one from the 19th or 20th century) is not the CRS used by the NTRIP base stations, which increases the likelihood of users making a mistake.

Knowing the proper CRS for the measurements ensures the best transformation to the needed reference system,
like a projected one, without adding an error that would ruin the RTK accuracy.

## How is NTRIP-catalog improving CRS selections
NTRIP-catalog is a database that allows application developers to make automatic and correct CRS selections for the user based on NTRIP connection data (server, mountpoint, ...),
some user details (rover position, country, ...) and the best known data available for the service provider being used.
It is intended to be a curated community effort that compiles as much global information as possible to reduce the number of times a user has to make a manual CRS selection,
therefore reducing the chances of introducing errors that can have very costly consequences.
At the core of the catalog there's a JSON schema that has been designed to cover as many cases as possible, reducing the amount of information that needs to be included in the database, while still ensuring complete coverage of the different scenarios that can arise when using a particular NTRIP service provider.

## License
This data is distributed as [CC0](https://creativecommons.org/public-domain/cc0/).
This is just a collection of the data that NTRIP providers should be already explaining in their web pages.
We are trying to make it easy to use and to contribute.

See files [DISCLAIMER.md](DISCLAIMER.md) and [LICENSE](LICENSE).

## EPSG
Many applications rely on the data provided by the [EPSG](https://epsg.org/) database.
For that reason EPSG data is preferred in this catalog.
If you do not find the CRS you need in EPSG, ask your regional geodetic authority to register it via https://epsg.org/dataset-change-requests.html.
It is easy and free of charge. (You can still register your NTRIP data without it)

As a helper you can use https://spatialreference.org/, maintained by the [PROJ](https://proj.org/) open source library.


## How can I use the catalog?
There is an example (used also in the tests) in python in `scripts/query.py`.
You don't have to use it, but it can give you an idea of the workflow.

Download the file `ntrip-catalog.json` from the [dist folder](dist/ntrip-catalog.json), and process it in your application with your favourite programming language.
Search among the entries for the URL of your service. The URL is composed by the scheme, hostname or IP, and the port.
Several URLs could be used for the same entry.

Once you have the entry, iterate through the streams applying the described filters.
The filter can be based on the mountpoint name, the country, or the base station latitude-longitude.
The last two cases try to aggregate several mountpoints that share those properties, making the json file smaller and less error prone.

Then iterate through the CRSs for the filtered stream.
CRSs can be different based on the rover latitude-longitude or rover country.
This is done to cover the networks that may aggregate several stations in one mountpoint, but using different CRSs.
An example is the Canary Islands, that are in the REGCAN95 reference system,
different from ETRS89 (ETRF2000) used in the European tectonic plate.

The precedence of the different streams and CRSs are strictly processed by appearance order.
Once a valid CRS is found, that is the solution.
Otherwise keep iterating.

The CRS defintion is done with a `name` and an `id`.
The `id` is the EPSG code of the geographic 3D system (2D if 3D is unfortunately not defined).
In that case, the `name` must be the name in EPSG.
Unfortunately some CRSs are not registered in EPSG.
In that case use only the `name`.

If there is no entry for your service, we are sorry.
It would be nice if you ask your service provider, inviting them to complete this repository.

In case there is an entry for your service, but no proper data is found, please ask the NTRIP provider to complete it with a pull-request.

## Contributing
If you would like to contribute to this project, please read the file [CONTRIBUTING_GUIDE.md](CONTRIBUTING_GUIDE.md).

## JSON syntax details
The JSON schemas are in the folder schemas.
They are documented describing each field.
Looking at `ntrip-catalog.json` will help to understand it.
See that there are three levels to classify the CRS.
First the entry, that is filtered by URL.
Second the stream, that is filtered by the `filter` field.
Finally some cases have a rover_bbox or rover_countries field (when there are several CRSs for the same mountpoint).

#### entries
The JSON file is composed mainly of a list of entries.
Each entry is identified by `name` and `urls` keys.
The name is for informative reasons.
The `urls` is a list of fully defined URLs, including protocol (`http` or `https`), domain and port.
Each URL (including port) must appear only once in the full catalog.
In case a service is available under several URLs (for instance, IP and hostname), all should be added in the same entry.
The `reference` section must contain the source where this information is published.

#### streams
For each entry, the different streams could be aggregated using several filters.

##### mountpoints
This is a list of mountpoints that use the same CRS.

##### lat_lon_bboxes
This filter will select streams which latitude and longitude fields in the source table are inside a defined bounding box.
The purpose of this filter is to easily classify some entries with many mountpoints, but located clearly in different locations.

##### countries
This filter will select streams by the country code in the source table.
The purpose of this filter is easily classify some entries with many mountpoints, where the significant different is the country.
This must match the country code in the sourcetable, even when it is a wrong ISO 3-letter code.

##### all
The special keyword `all` means that all the streams (mountpoints) on this entry are matched.
It is useful in entries covering a limited area or country, where all the streams use the same CRS.
You still have to apply the CRS internal rover-location filters. If none apply, you should continue with the next stream-filters.

#### crss
Once a stream is filtered by the `filter` field, it may include one or more CRSs.
To find the proper one, use the `rover_bbox` or `rover_countries` (also using the 3-letter country code).
These fields allow filtering based on the location of the rover.
There could be a "default" CRS without `rover_bbox` or `rover_countries` at the end of the list.

### Country codes
The RTCM protocol uses three-letter country codes [ISO_3166-1_alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3).

Therefore, when a country is identified in the NTRIP catalog, it is done using these codes.
See that some NTRIP providers do use invalid codes in the stream information, like `GER` for Germany or `SUI` for Switzerland.
If the code in the json is intended to match information from the stream, it should be identical, even if it is a invalid ISO_3166-1_alpha-3 code.

## Contact information
For questions and support please send an email to "ntrip-catalog (at) ntrip-catalog (dot) org".

[^1]: Networked Transport of RTCM via Internet Protocol
[^2]: Coordinate Reference System
[^3]: Radio Technical Commission for Maritime Services
[^4]: Real-time kinematic positioning
