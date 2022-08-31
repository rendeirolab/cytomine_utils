# Cytomine Utils

A package with utilities to interact with Cytomine's API.

## Installation

You can install _Cytomine Utils_ via [pip]:

```bash
$ pip install git+https://github.com/rendeirolab/cytomine-utils.git
```

## Usage

Save your credentials into a file `~/.cytomine.auth.json`:
```json
{
        "host": "cytomine.int.cemm.at",
        "upload_host": "cytomine-upload.int.cemm.at",
        "public_key": "",
        "private_key": ""
}
```
Where the values of `public_key` and `private_key` can be retrieved from [your account page on Cytomine](http://cytomine.int.cemm.at/#/account).

Then to connect to the server, call the `connect` function once each session, and the API is now ready to interface with the server:
```python
import cytomine_utils as cu

cu.connect()
prjs = cu.get_projects()
```

## Documentation

The API is fully documented and can be seen in HTML by building it locally:

```bash
$ make docs
$ browser docs/build/html/index.html
```
It requires the installation of dependencies like sphinx and its extensions:
```bash
pip install -r docs/requirements.txt
```
