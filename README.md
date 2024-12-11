# NTRIP-catalog
Catalog of NTRIP providers with CRS information

## What is NTRIP-catalog
NTRIP-catalog is an open source and open data repository with the CRS information from multiple NTRIP service providers. The data is stored as JSON files, that can be easily parsed by any software.

## What is the problem with coordinate reference systems in the NTRIP and RTCM protocols?
NTRIP RTCM messages do not include any clarification about the CRS that applies to the corrected coordinates. That can be a significant problem, because the difference between using one CRS or another can be big depending on the scenario. Definitelly much bigger than the accuracy claimed by RTK devices, that is around 2 cm. In Europe the difference between ETRS89 and ITRF2014 is about 80 cm, and growing.

When final applications have to ask the user to provide a CRS to label coordinates it is a constant source of error that we aim to remove.
Some NTRIP service providers document the CRS used in their mount points in their web pages or user manuals, while others do not document it at all assuming it is well known data, despite there exist hundreds of CRS definitions and for some of them, multiple realizations.
In the end, many users do not know what is the CRS that the have to use because either the information is not clearly disclosed by the provided or they are not competent enough to figure it out.
To increase the confusion, in some countries the official CRS (usually an old one from the 19th or 20th century) is not the CRS used by the NTRIP base stations, which increases the likelihood of users making a mistake.

Knowing the proper CRS for the measurements ensures the best transformation to the needed reference system, like a projected one, without adding an error that would ruin the RTK accuracy.

## License
This data is distributed as CC0. This is just a collection of the data that NTRIP providers should be already explaining in their web pages. We try to make it easy to use and contribute.

## EPSG
Many applications rely on the data provided by the [EPSG](https://epsg.org/) database. For that reason EPSG data is preferred in this catalog.
If you do not find the CRS you need in EPSG, ask your geodetic regional authority to register it via https://epsg.org/dataset-change-requests.html. It is easy and free of charge. (You can still register your NTRIP data without it)

As a helper you can use https://spatialreference.org/, maintained by the [PROJ](https://proj.org/) open source library.


## How can I use it?
There is an example (used also in the tests) in python in `scripts/query.py`. You don't have to use it, but it can give you an idea of the workflow.

Download the file `ntrip-catalog.json`, and process it in your application with your favourite programming language.
Search among the entries for the URL of your service. The URL is composed by the scheme, hostname or IP, and the port. Several URLs could be used for the same entry.

Once you have the entry, iterate among the streams applying the described filters. The filter can be based on the mountpoint name, the country, or the base station latitude-longitude. The last two cases try to aggregate several mountpoints that share those properties, making the json file smaller and less error prone.

Then iterate among the CRSs for the filtered stream. CRSs can be different based on the rover latitude-longitude or rover country. This is done to cover the networks that may aggregate several stations in one mountpoint, but using different CRSs. An example is the Canary Islands, that are in the REGCAN95 reference system, different from ETRS89 (ETRF2000) used in the European tectonic plate.

The precedence of the different streams and CRSs are strictly by order. Once a valid CRS is found, that is the solution. Otherwise keep iterating.

The CRS defintion is done with a `name` and `id`. The `id` is the EPSG code of the geographic 3D system (2D if 3D is unfortunately not defined). In that case, the `name` must be the name in EPSG. Unfortunately some CRSs are not registered in EPSG. In that case use only the `name`.

If there is no entry for your service, we are sorry. It would be nice if you ask your service provider, inviting them to complete this repository.

In case there is an entry for your service, but no proper data is found, please ask the NTRIP provider to complete it with a pull-request.

## Who can contribute?
Any contribution should be properly documented, filling the `reference` section in the json file. The best is that the NTRIP providers do submit their data. If you find the proper documentation published by the NTRIP provider confirming the CRS used, and do not expect the provider to do it, you can contribute it as well.

## How to contribute
Just create a PR in this GitHub project. In case you do not know how to do it, or you do not feel confortable with JSON, you can open an Issue providing all the data.
All contributions must be properly documented, filling the `reference` section in the JSON file.
This database is intended to become a trusted source of information, so submissions that cannot be backed by an authoritative reference will not be considered.
See the file in the `data` directory to see what can be done.

## JSON syntax details
The JSON schemas are in the folder schemas. They are documented describing each field. Looking at `ntrip-catalog.json` will help to understand it.
See that there are three levels to classify the CRS. First the entry, that is filtered by URL. Second the stream, that is filtered by the `filter` field. Finally some cases have a rover_bbox or rover_countries field (when there are several CRSs for the same mountpoint).

### Country codes
RTCM protocol uses three-letter country codes [ISO_3166-1_alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3). Therefore when a country is identified in the NTRIP catalog, it is done using these codes. See that some NTRIP providers do use wrong codes in the stream information, like `GER` for Germany or `SUI` for Switzerland. If the code in the json is intended to match information from the stream, it should be identical even if it is a wrong ISO_3166-1_alpha-3 code.
