from preprocess import PreProcess
import numpy as np
import logging
import csv
from sklearn.svm import SVC
from sklearn.grid_search import GridSearchCV

if __name__ == "__main__":
    logging.basicConfig(format='--%(asctime)s:[%(levelname)s]:%(lineno)d:%(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.INFO)
    logging.info("Program Start")
    p = PreProcess()
    #PREPROCESS = False

    #filepath = 'data/train_1M.csv'
    #out_filepath = 'data/train_1M.csv.out'
    out_filepath = 'data/train_s404_10K.out'
    #out_filepath = 'data/train_1000.csv.out'
    #if PREPROCESS:
    #    out_filepath = p.convert(filepath)

    #Load data
    X, y, enc, map_dict = p.load_train_data(out_filepath, category = True)
    #X, y = p.load_train_data(out_filepath)
    logging.info("Shape X = %r, y =%r" %(X.shape, y.shape ))
    logging.info("example X = %s\ny =%r" %(X[0], y[0]))
    logging.info("classes: %r" % list(np.unique(y)))

    #TODO Add ShuffleSplit
    #Sampling
    #At least 3
    POWER = 3
    CONST = 1
    #At least 2
    CV = 5
    n_subsamples = CONST*10**POWER
    n_size = y.shape[0]
    if n_subsamples < n_size:
        logging.info("second index : %d to %d" % (n_size - n_subsamples/2, n_size))
        X_small_train = X[range(n_subsamples/2)+range(n_size - n_subsamples/2, n_size)]
        y_small_train = y[range(n_subsamples/2)+range(n_size - n_subsamples/2, n_size)]
    else:
        X_small_train, y_small_train = X, y
    n_subsamples = y_small_train.shape[0]
    logging.info("Samples : %d, CV :%d" % (n_subsamples, CV))
    
    #Kernal
    KERNEL = 'rbf'
    #CV
    svc_params = {
            'C': np.logspace(-1, 2, 4),
            'gamma': np.logspace(-4, 0, 5),
            }
    #Add class_weight
    class_weight = {
            1:4.8,
            0:1.0
            }
    gs_svc = GridSearchCV(SVC(probability=True, verbose = False, kernel = KERNEL, cache_size = 200, class_weight ='balanced'), svc_params, refit=True ,scoring='log_loss', cv=CV, n_jobs=-1, verbose = 1)

    gs_svc.fit(X_small_train, y_small_train)

    logging.info("Best params: %s\nScore: %s" % (gs_svc.best_params_, gs_svc.best_score_))
    
    #XXX skip test
    exit()

    #Load test data for 5 times
    test_filepattern = 'data/test_%d_M.out'
    field = ['id', 'click']
    for part in range(1, 6):
        test_filepath = test_filepattern % part
        logging.info("Loading test set [%s]..." % test_filepath)
        #X_test, ids_test= p.load_test_data(test_filepath)
        #Load data with category

        width = 10000
        for a_slice in range(100):
            logging.info("+++Doing slice %d+++" %(a_slice))
            X_test, ids_test= p.load_test_data(test_filepath, enc = enc, map_dict = map_dict, start_line_no = a_slice*width)
            if X_test == None:
                break
            logging.info("Shape X = %r, ids =%r" %(X_test.shape, ids_test.shape ))
            logging.info("example X = %s\nids =%r" %(X_test[0], ids_test[0]))
            svc_probs = gs_svc.predict_proba(X_test)
            #[prob of 0, prob of 1]
            logging.info("prob of test: %s" % svc_probs[:10])
            out_filepath = "%s-svc-s%d-c%f-g%f.csv" %(test_filepath, n_subsamples, gs_svc.best_params_['C'], gs_svc.best_params_['gamma'])
            logging.info("Writing out file %s" % out_filepath)
            if len(ids_test) != len(svc_probs):
                logging.error("Test case count don:t match")
            else :
                with open(out_filepath, 'a') as ofile:
                    writer = csv.DictWriter(ofile, field)
                    if part == 1:
                        writer.writeheader()
                    for i in range(len(ids_test)):
                        row = {'id' : ids_test[i], 'click' : svc_probs[i][1]}
                        #logging.info("row %d : %s" %(i, row))
                        writer.writerow(row)

    
    logging.info("Program End")
