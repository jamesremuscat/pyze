from pyze.api import Gigya, Kamereon

import getpass


help_text = 'Log in to your MY Renault account.'


def run(args):
    email = input('Enter your My Renault email address: ')
    password = getpass.getpass('Enter your password: ')

    g = Gigya()
    if g.login(email, password):
        g.account_info()

        k = Kamereon(gigya=g)
        accounts = k.get_accounts()
        if len(accounts) > 1:
            Kamereon.print_multiple_account_warning(accounts)

        print('Logged in successfully.')
    else:
        print('Failed to log in!')
