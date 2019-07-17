from pyze.api import Kamereon


help_text = 'List the vehicles on your account.'


def run(args):
    k = Kamereon()

    vehicles = k.get_vehicles().get('vehicleLinks')

    print(
        'Found {} vehicle{}'.format(
            len(vehicles),
            '' if len(vehicles) == 1 else 's'
        )
    )

    for v in vehicles:
        print(
            ' - {}: {} {} [{}]'.format(
                v['vehicleDetails']['registrationNumber'],
                v['vehicleDetails']['brand']['label'],
                v['vehicleDetails']['model']['label'],
                v['vin']
            )
        )
