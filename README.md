# PyZE: Python client for Renault ZE API

![Test status](https://github.com/jamesremuscat/pyze/workflows/Tests/badge.svg) [![Coverage status](https://coveralls.io/repos/github/jamesremuscat/pyze/badge.svg)](https://coveralls.io/github/jamesremuscat/pyze) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Obtaining API keys

You need two API keys: one for Kamereon and one for Gigya. Both can be obtained
from Renault; they're the same for everyone and shouldn't be confused with
your API credentials.

Find them at e.g.

`https://renault-wrd-prod-1-euw1-myrapp-one.s3-eu-west-1.amazonaws.com/configuration/android/config_en_GB.json`

(replacing `en_GB` with your locale, though I'm not sure it makes a difference).

Look for:

```json
"wiredProd": {
    "target": "https://api-wired-prod-1-euw1.wrd-aws.com",
    "apikey": "oF09WnKqvBDcr..."
    ...
},
...
"gigyaProd": {
    "target": "https://accounts.eu1.gigya.com",
    "apikey": "3_e8d4g4SE_Fo8ahyH..."
},
```

## CLI Quickstart

```bash
python3 setup.py install # from checkout of this repo
# OR
pip install pyze # install latest release from PyPI

export KAMEREON_API_KEY=oF09WnKqvBDcr...
export GIGYA_API_KEY=3_e8d4g4SE_Fo8ahyH...

pyze login  # You should only need to do this once
pyze status
```

## API Quickstart

```python
from pyze.api import Gigya, Kamereon, Vehicle

g = Gigya()
g.login('email', 'password')  # You should only need to do this once
g.account_info()  # Retrieves and caches person ID

k = Kamereon(gigya=g)  # Gigya argument is optional - if not supplied it will create one

v = Vehicle('YOUR_VIN', k)  # Kamereon argument is likewise optional

v.battery_status()
```

## Further details

See the [original blog post](https://muscatoxblog.blogspot.com/2019/07/delving-into-renaults-new-api.html)
for a walkthrough of the required steps to authenticate and use the API.

## Contributing

### Issues

Check to see that the problem you're experiencing isn't listed on the
[known issues with the Renault API](https://github.com/jamesremuscat/pyze/wiki/Known-issues-with-the-Renault-API)
page on the wiki. Things listed on that page are not within our power to fix!

### Feature requests

You're welcome to raise an issue with a feature request, but I can't guarantee
it will be implemented (I am but one person). You'll have more luck if you
submit a pull request implementing the feature!

### Pull requests

Pull requests are welcome!

- Fork this repository
- Create a feature or bugfix branch
- Make your changes
- Ensure your code passes `pycodestyle`
- Make a pull request

Apologies if I'm slow to review and merge - I'll get there eventually!

### Testing

We've already experienced some very different behaviour across Zoe models,
and in some cases for the same Zoe model - some endpoints return errors, some
have missing or additional information. These discrepancies are noted
[on the wiki](https://github.com/jamesremuscat/pyze/wiki/Known-issues-with-the-Renault-API).

If you discover that your Zoe is missing something, or conversely, if you
discover something I've not seen, please raise an issue to let me know!

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Renault. I
accept no responsibility for any consequences, intended or accidental, as a
as a result of interacting with Renault's API using this project.

## Licence

This code is licensed under the terms of the standard MIT licence. See the
LICENSE file for details. (Hooray for differences in American and British
English.)
