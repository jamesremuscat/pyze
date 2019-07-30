# PyZE: Python client for Renault ZE API

## CLI Quickstart

```bash
python3 setup.py install

export GIGYA_API_KEY=XXXXXXXX
export KAMEREON_API_KEY=YYYYYYYY

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
