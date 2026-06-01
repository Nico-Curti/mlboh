#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import argparse
from time import time as now

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score

from .__version__ import __version__
from .mlboh import manual_parallel_cv_threads
from .mlboh import manual_parallel_cv_processes

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
  # mlboh --input <file>
  # This option allows the user to specify an input file from which to read the data.
  # If both 'data' and 'input' are provided, 'data' will take precedence.
  parser.add_argument(
    '--input', '-i',
    dest='input',
    type=str,
    required=True,
    #default=None, # the default is uselss since it is a mandatory input
    help=(
      'The input file from which to read the data. '
      'The file must be in CSV format with the column of labels identified '
      'by the name "Y"; all the other columns will be interpreted as input '
      'columns/features'
    ),
  )

  # mlboh --parallel <str>
  # Choose the parallelism to use for the ML application
  parser.add_argument(
    '--parallel', '-p',
    dest='parallel',
    required=False,
    action='store',
    default='threads',
    choices=[
      'threads',
      'processes',
    ],
    help='Parallelization scheme to use for the ML cross-validation'
  )

  # mlboh --num-workers <int>
  # This option allows the user to specify the number of worker threads/processes 
  # to use for parallel computation.
  parser.add_argument(
    '--num-workers', '-n',
    dest='num_workers',
    type=int,
    required=False,
    default=4,
    help='The number of worker threads/processes to use for parallel computation. Default is 4.',
  )

  return parser.parse_args()

def main ():
  # extraction of the command line arguments
  args = parse_args()
  # check if the version is required from the user
  if args.version:
    print(f'The version installed is v{__version__}')
    # if only the version is required we can exit with success
    exit(0)

  # check if the input file exists and can be opened
  if not args.input.endswith('.csv'):      
    print(
      f'Error! Input file must be a CSV file.',
      file=sys.stderr, flush=True
    )
    exit(1)
  # try to open the input file to check if it exists
  try:
    # read the input file
    with open(args.input, 'r') as fp:
      # read the data from the file
      # split the lines 
      data = fp.read().splitlines()
      names = data[0]
      data = data[1:]

    # check if the ground truth column is in the file
    if 'Y' not in names:
      print(
      f'Error! Input file must contain a column with name "Y"',
      file=sys.stderr, flush=True
    )
    exit(1)

    # convert the data to a list of floats
    X = [
      [
        float(x) 
        for x in row.strip().split(',')[1:]
      ] 
      for row in data
    ]
    y = [
      row.strip().split(',')[0] 
      for row in data
    ]

  except FileNotFoundError:
    print(
      f'Error! Input file {args.input} not found.',
      file=sys.stderr, flush=True
    )
    exit(1)

  ###############################################################
  #
  #     Machine Learning Pipeline and Parameters
  # 
  ###############################################################
  # NOTE: this part could be customized according to an appropriated
  # command line interface to manage multiple pipeline structures
  # (compatible with sklearn interface), multiple CV strategies
  # (compatible with sklearn interface), and multiple metric scores
  # (compatible with sklearn interface).

  # define the estimator/classifier of the ml pipeline
  # NOTE: according to the sklearn nomenclature, the
  # estimator could be an entire Pipeline object
  # (ref. 
  #      https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html
  # and
  #      https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.make_pipeline.html#sklearn.pipeline.make_pipeline
  # )
  estimator = LogisticRegression(
    max_iter=5000,
    n_jobs=1
  )

  # define a cross validation strategy for the train/test
  # split
  skf = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42, # fix the random seed for reproducibility
  )

  # start the timer
  tic = now()

  if args.parallel == 'threads':
    # run the pipeline in a parallel threads framework
    thread_scores = manual_parallel_cv_threads(
      estimator=estimator,
      X=X,
      y=y,
      cv=skf,
      metric=accuracy_score,
      max_workers=args.num_workers
    )
    print(f'Thread scores: {thread_scores}')
    print(f'Thread mean: {thread_scores.mean()}')

  elif args.paralle == 'processes':
    # run the pipeline in a parallel processes framework
    process_scores = manual_parallel_cv_processes(
      estimator=estimator,
      X=X,
      y=y,
      cv=skf,
      metric=accuracy_score,
      max_workers=args.num_workers
    )
    # log the results
    print('Process scores:', process_scores)
    print('Process mean:', process_scores.mean())

  # log the time taken to compute the cross validation
  toc = now()
  print(
    f'[DONE] took {toc - tic:.2f} sec.',
    file=sys.stdout, flush=True
  )

if __name__ == '__main__':
  main()
