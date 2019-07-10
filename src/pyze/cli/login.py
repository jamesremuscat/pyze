from pyze.api import Gigya

import getpass


def run(args):
    email = input('Enter your My Renault email address: ')
    password = getpass.getpass('Enter your password: ')

    g = Gigya()
    print(g.login(email, password))
