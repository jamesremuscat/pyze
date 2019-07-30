from pyze.api import Gigya

import getpass


help_text = 'Log in to your MY Renault account.'


def run(args):
    email = input('Enter your My Renault email address: ')
    password = getpass.getpass('Enter your password: ')

    g = Gigya()
    if g.login(email, password):
        g.account_info()
        print('Logged in successfully.')
    else:
        print('Failed to log in!')
