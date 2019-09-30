from pyze.api import Kamereon


help_text = 'Set the Kamereon account ID to use. Useful if there are multiple accounts to choose from.'


def configure_parser(parser):
    parser.add_argument('account_id', help='Kamereon account ID to use for future calls')


def run(args):
    k = Kamereon()
    k.set_account_id(args.account_id)
