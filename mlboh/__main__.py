#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from .__version__ import __version__

__author__ = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

__all__ = [

]

def parse_args ():
    '''
    Parse of command line for CLI usage
    '''
    # definition of the argument parser object
    # with the main parameters
    parser = argparse.ArgumentParser(
        prog='mlboh',
        argument_default=None,
        add_help=True,
        allow_abbrev=True,
        exit_on_error=True
    )
    # add an extra flag for the version of the package
    parser.add_argument(
        '--version', '-v',
        dest='version',
        required=False,
        action='store_true',
        default=False,
        help='Get the current version installed',
    )

    return parser.parse_args()

def main ():
    # extraction of the command line arguments
    args = parse_args()
    # check if the version is required from the user
    if args.version:
        print(f'The version installed is v{__version__}')
    
    pass

if __name__ == '__main__':

    main()
