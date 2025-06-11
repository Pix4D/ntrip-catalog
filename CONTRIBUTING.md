# Contributing

## NTRIP Provider Quick Start

We welcome contributions from NTRIP providers to help make this catalog as accurate and comprehensive as possible. There are two easy ways to contribute:

1. **Create an Issue (Simplest)**:
   - Create a [new issue](https://github.com/pix4d/ntrip-catalog/issues/new)
   - You'll need a free GitHub account
   - Fill out the template with your NTRIP service information
   - We'll handle creating the proper JSON file for you

2. **Submit a Pull Request (Advanced)**:
   - Fork the repository
   - Add your service information
   - Submit a pull request

## What We Need

To add your NTRIP service to the catalog, we need:

1. **Basic Service Information**:
   - Service name
   - Service URL(s) including protocol (`http`, `https`) and port
   - List of mountpoints, and the CRS that each uses

2. **CRS Information**:
   - The Coordinate Reference System(s) used by your service
   - EPSG code
   - Epoch
   - If different regions use different CRS, please specify

3. **Documentation Reference**:
   - Link to official documentation or webpage where this CRS information is published
   - NTRIP catalog is intended to be a trustworthy source of information. It's therefore a requirement to provide an official reference in order to merge a submission.

## Making a Pull Request

If you're comfortable with GitHub and JSON, here's how to submit a PR:

1. Add your service information to the appropriate country file in the `data` folder
2. Update `data/release.txt` with an incremented version number
3. Sign your commits with the Developer Certificate of Origin (DCO):
   ```bash
   git commit -s -m "Your commit message"
   ```

The DCO signature certifies that you have the right to submit this contribution. It will be automatically added when using the `-s` flag.

## Examples

We have three common scenarios for NTRIP networks. Below are examples for each case:

### 1. Simple: Single CRS for All Mountpoints
Many regional networks use the same CRS for all mountpoints. This is the simplest case.

**Example:** [NYSNet Network](https://github.com/Pix4D/ntrip-catalog/blob/master/data/World/Americas/USA/nysnet.json)
- All mountpoints use NAD83(2011)
- A single JSON entry covers all the URLs and mountpoints
- Perfect starting point for many providers

### 2. Multiple CRS: Different Mountpoints, Different CRS
Some networks offer mountpoints in different coordinate systems.

**Example:** [MnCORS Network](https://github.com/Pix4D/ntrip-catalog/blob/master/data/World/Americas/USA/mncors.json)
- Some mountpoints use NAD83(2011)
- Others use NAD83(CORS96)
- Each CRS group is defined in its own stream

### 3. Advanced: Region-Based CRS Selection
For networks spanning multiple regions where CRS varies by location.

**Example:** [Point One Nav](https://github.com/Pix4D/ntrip-catalog/blob/master/data/World/pointonenav.json)

Two ways to specify regions:
1. **By Country** (`rover_countries`):
   - Use [3-letter ISO country codes](https://countrycode.org/)
   - Best for country-specific CRS definitions

2. **By region area** (`rover_bbox`):
   - Uses bounding boxes for specific regions
   - Perfect for regions that differ from their country's standard
   - Example: Hawaii using NAD83(PA11) vs mainland USA using NAD83(2011)
   - Important: List region-specific entries before country-wide ones

Need help? Email us at `ntrip-catalog (at) ntrip-catalog.org`
