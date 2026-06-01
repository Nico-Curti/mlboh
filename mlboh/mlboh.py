#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

from sklearn.base import clone
# the following import is used for the correct typehint
from sklearn.base import BaseEstimator 

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

__author__ = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

__all__ = [
  'manual_parallel_cv_threads',
  'manual_parallel_cv_processes',
]

# NOTE: according to the Python "nomenclature", all the functions
# with a name with prefix '_' should be considered as "private", i.e.
# not accessible or usable by no-expert users.
def _train_and_score(estimator : BaseEstimator, X : np.ndarray, y : np.ndarray, train_idx : list, test_idx : list, metric : callable, *args, **kwargs) -> float:
  '''
  Single fold fit->prediction of the estimator pipeline.

  Parameters
  ----------
    estimator: BaseEstimator
      Machine learning estimator pipeline to use
    X: np.ndarray
      Input variables/features to analyze **without** train/test subdivision
    y: np.ndarray
      Input labels/ground-truths to analyze **without** train/test subdivision
    train_idx: list
      List of indices to use for the train set
    test_idx: list
      List of indices to use for the test set
    metric: callable
      Sklearn-like callable function in which the first argument **is** the
      `y_true` list and the second is the `y_pred` list

  Returns
  -------
    score: float
      Output of the metric function applied on the predicted labels
      of the provided ML model.

  Notes
  -----
  This function performes an internal copy of the provided estimator.
  This is particularly import when you want to use a parallelism based on 
  theads in which ALL the involved variables are SHARED among all the threads;
  if the pipeline is not manually copied, a "slow thread" could find the 
  estimator already fitted, avoiding the re-fit and so introducing errors 
  in the data management (!!!)
  '''

  # clone the pipeline to avoid concurrencies of
  # internal variables
  # NOTE: this is particularly import when you want to
  # use a parallelism based on theads in which ALL the
  # involved variables are SHARED among all the threads;
  # if the pipeline is not manually copied, a "slow thread"
  # could find the estimator already fitted, avoiding the
  # re-fit and so introducing errors in the data management (!!!)
  model = clone(estimator)

  # extraction of train/test subsets using indices
  X_train, X_test = X[train_idx], X[test_idx]
  y_train, y_test = y[train_idx], y[test_idx]

  # fit the pipeline
  model.fit(
    X=X_train, 
    y=y_train,
    *args,   # possible extra-parameters required by the fit
    **kwargs # possible extra-parameters required by the fit
  )
  # now predict the labels of the corresponding
  # test set
  y_pred = model.predict(X=X_test)

  # return the metric score
  return metric(
    y_true=y_test, 
    y_pred=y_pred
  )


def manual_parallel_cv_threads(estimator : BaseEstimator, X : np.ndarray, y : np.ndarray, cv, metric : callable, max_workers : int = 4, *args, **kwargs) -> np.ndarray:
  '''
  Run cross-validation manually using multiple threads.

  Parameters
  ----------
    estimator: BaseEstimator
      Machine learning estimator pipeline to use
    X: np.ndarray
      Input variables/features to analyze **without** train/test subdivision
    y: np.ndarray
      Input labels/ground-truths to analyze **without** train/test subdivision
    train_idx: list
      List of indices to use for the train set
    test_idx: list
      List of indices to use for the test set
    metric: callable
      Sklearn-like callable function in which the first argument **is** the
      `y_true` list and the second is the `y_pred` list
    max_worker: int (default := 4)
      Maximum number of threads to use for the parallelization

  Returns
  -------
    score: np.ndarray
      Output list of the metric function applied on the predicted labels
      of the provided ML model.
  '''
  # declare the empty list in which store the resulting
  # scores, computed for each fold of the cv
  scores = []

  # In the thread-based implementation, each cross-validation fold 
  # is submitted as an independent task to a ThreadPoolExecutor. 
  # Every thread receives the same original estimator, data matrix, labels, 
  # and fold indices. 
  # Inside each task, the estimator is cloned before training, so different 
  # threads do not share the same model instance. 
  # This is important because fitting a scikit-learn estimator modifies 
  # its internal state.
  # Threads run within the same Python process and share the same memory space. 
  # Therefore, the input arrays X and y do not need to be copied to 
  # separate processes. 
  # This makes threads lightweight and convenient.
  # However, Python threads are affected by the Global Interpreter Lock, so they 
  # are most effective when the heavy computations are performed by NumPy, SciPy,
  # or scikit-learn routines that release the GIL internally.
  with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # declare an empty list of promises
    futures = []

    # Generate the train/test split for each fold.
    for train_idx, test_idx in cv.split(X, y):
      # Submit one fold as an independent task.
      # The task starts running as soon as a worker thread is available.
      future = executor.submit(
        _train_and_score,
        estimator=estimator,
        X=X,
        y=y,
        train_idx=train_idx,
        test_idx=test_idx,
        metric=metric,
        *args,
        **kwargs,
      )
      # Store the Future object.
      # A Future represents a result that will be available later.
      futures.append(future)

    # Collect results as soon as each thread finishes.
    # The order may differ from the original fold order.
    for future in as_completed(futures):

      # Retrieve the score returned by _train_and_score.
      # If the thread raised an exception, it is raised here.
      scores.append(future.result())

  # return the array version of the score list
  return np.array(scores)


def manual_parallel_cv_processes(estimator : BaseEstimator, X : np.ndarray, y : np.ndarray, cv, metric : callable, max_workers : int = 4, *args, **kwargs) -> np.ndarray:
  '''
  Run cross-validation manually using multiple processes.

  Parameters
  ----------
    estimator: BaseEstimator
      Machine learning estimator pipeline to use
    X: np.ndarray
      Input variables/features to analyze **without** train/test subdivision
    y: np.ndarray
      Input labels/ground-truths to analyze **without** train/test subdivision
    train_idx: list
      List of indices to use for the train set
    test_idx: list
      List of indices to use for the test set
    metric: callable
      Sklearn-like callable function in which the first argument **is** the
      `y_true` list and the second is the `y_pred` list
    max_worker: int (default := 4)
      Maximum number of threads to use for the parallelization

  Returns
  -------
    score: np.ndarray
      Output list of the metric function applied on the predicted labels
      of the provided ML model.
  '''

  # declare the empty list in which store the resulting
  # scores, computed for each fold of the cv
  scores = []

  # In the process-based implementation, each cross-validation fold is 
  # executed in a separate Python process using a ProcessPoolExecutor. 
  # Unlike threads, processes do not share the same interpreter or memory space. 
  # Each worker process has its own Python runtime and its own 
  # Global Interpreter Lock (GIL), allowing true parallel execution across multiple CPU cores.
  # When a task is submitted to the process pool, all required objects 
  # (the estimator, data, and fold indices) must be serialized and transferred 
  # to the worker process. This introduces additional overhead compared to threads, 
  # but it also removes the GIL limitation and often provides better scalability 
  # for CPU-intensive workloads.
  # As in the thread-based version, the estimator is cloned inside each task to 
  # ensure that every fold is trained independently.
  # Once a worker finishes training and evaluation, the computed score is sent back 
  # to the main process and collected through a Future object.
  with ProcessPoolExecutor(max_workers=max_workers) as executor:
    # declare an empty list of promises
    futures = []

    # Generate the train/test split for each fold.
    for train_idx, test_idx in cv.split(X, y):
      # Submit one fold as an independent task.
      # The task starts running as soon as a worker process is available.
      future = executor.submit(
        _train_and_score,
        estimator=estimator,
        X=X,
        y=y,
        train_idx=train_idx,
        test_idx=test_idx,
        metric=metric,
        *args,
        **kwargs,
      )
      futures.append(future)

    # Collect results as soon as each process finishes.
    # The order may differ from the original fold order.
    for future in as_completed(futures):

      # Retrieve the score returned by _train_and_score.
      # If the process raised an exception, it is raised here.
      scores.append(future.result())

  # return the array version of the score list
  return np.array(scores)


if __name__ == '__main__':

  # The following imports are included ONLY into the
  # '__main__' sections since are related to the proof
  # of concept of the current file and they are not 
  # mandatory for the correct execution of 'mlboh'
  # package (!!)  
  from sklearn.datasets import load_breast_cancer
  from sklearn.linear_model import LogisticRegression
  from sklearn.model_selection import StratifiedKFold
  from sklearn.metrics import accuracy_score

  # timing of the execution
  from time import time as now

  # load of a dummy dataset from standard sklearn sampels
  X, y = load_breast_cancer(return_X_y=True)

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

  # start the clock for the timing
  tic = now()
  # run the pipeline in a parallel threads framework
  thread_scores = manual_parallel_cv_threads(
    estimator=estimator,
    X=X,
    y=y,
    cv=skf,
    metric=accuracy_score,
    max_workers=4
  )
  # stop the clock
  toc = now()
  
  # log the results
  print(f'Thread scores: {thread_scores}')
  print(f'Thread mean: {thread_scores.mean()}')
  print(f'Elapsed time: {toc - tic:.3f} sec')

  # (re-)start the clock for the timing
  tic = now()
  # run the pipeline in a parallel processes framework
  process_scores = manual_parallel_cv_processes(
    estimator=estimator,
    X=X,
    y=y,
    cv=skf,
    metric=accuracy_score,
    max_workers=4
  )
  # stop the clock
  toc = now()

  # log the results
  print('Process scores:', process_scores)
  print('Process mean:', process_scores.mean())
  print(f'Elapsed time: {toc - tic:.3f} sec')
