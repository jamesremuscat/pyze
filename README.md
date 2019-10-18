# PyZE: Python client for Renault ZE API

## CLI Quickstart

```bash
python3 setup.py install
```

```
curl https://renault-wrd-prod-1-euw1-myrapp-one.s3-eu-west-1.amazonaws.com/configuration/android/config_en_GB.json |grep Prod -A2
```
en_GB for English, fr_FR for French, etc

```
"wiredProd": {
			"target": "https://api-wired-prod-1-euw1.wrd-aws.com",
			"apikey": "oF09WnKqvBDcr....."
"gigyaProd": {
			"target": "https://accounts.eu1.gigya.com",
			"apikey": "3_e8d4g4SE_Fo8ahyH......................................."
```

```
export GIGYA_API_KEY=oF09WnKqvBDcr.....
export KAMEREON_API_KEY=3_e8d4g4SE_Fo8ahyH.......................................

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

See the [original blog post](https://muscatoxblog.blogspot.com/2019/07/delving-into-renaults-new-api.html) for a walkthrough of the required steps to authenticate and use the API.
