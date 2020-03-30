"""
  ____          ____   ____   _                         ____  ____ __     __
 |  _ \  _   _ |  _ \ / ___| | |  ___    __ _          / ___|/ ___|\ \   / /
 | |_) || | | || | | |\___ \ | | / _ \  / _` |  _____  \___ \\___ \ \ \ / /
 |  __/ | |_| || |_| | ___) || || (_) || (_| | |_____|  ___) |___) | \ V /
 |_|     \__, ||____/ |____/ |_| \___/  \__, |         |____/|____/   \_/
         |___/                          |___/

"""
from __future__ import division, print_function
from scipy.stats import pearsonr
import numpy as np

__author__ = "FBU, www.ssv-embedded.de"
__version__ = "0.0.1"

class SignalClassificator:
    """
    Class used to predict machine states from new signals

    Parameters
    ----------
    min_pears_correlation" : (0-1) Minimum pearson correlation for signal clustering in subgroups

    max_subgroups: maximal number of subgroups for a single class

    """

    def __init__(self, min_pears_correlation=0.7, max_subgroups=5, outliers=False):

        self.master_dict = {}
        self.min_correlation = min_pears_correlation
        self.max_subgroups = max_subgroups
        self.outliers = outliers

    def fit(self, x_train, y_train, verbose=False):
        """
        "fit" or "train" the algorithm with a set of signals and labels

        Parameters
        ----------
        x_train : nd array
            The array containing the signals. the dimensions are (number of signal x components x signal length)
        y_train : 1d array
            The array with the labels for the signals. It has to be a number that represent the state corresponding to
            the signal in x_train
        verbose : boolean
            nothing defined

        """

        # get the different labels and the times that appears in the labels array
        dif_labels, counts = np.unique(y_train, return_counts=True)

        # make a dict where dif_labels and counts are stored
        count_dict = {}
        for l in range(0, len(dif_labels)):
            count_dict.update({str(dif_labels[l]):counts[l]})

        # every component  is stored in a dict
        # example:  {e:{Nc:{count:{}, groups:{}}}} with N = number of component and e = label of class
        for e in range(0, dif_labels.shape[0]):
            self.master_dict.update({str(dif_labels[e]):{"c"+str(c):{"count":{},"groups":{}} for c in range(x_train.shape[1])}})

        # fill the new dict with start values. count = 0 and  group  1 = zeros array of signal length
        for l_key in self.master_dict.keys():
            for c_key in self.master_dict[l_key].keys():
                self.master_dict[l_key][c_key]["count"].update({1:0})
                self.master_dict[l_key][c_key]["groups"].update({1:np.zeros((x_train.shape[2]))})

        # extract label for current signal
        for no in range(0, x_train.shape[0]):
            label = str(y_train[no])

            # extract current component of current signal
            for co in range(0, x_train.shape[1]):
                v = x_train[no, co, :]

                # if first run, then count is = 0
                if self.master_dict[str(label)]["c"+str(co)]["count"][1] == 0:

                    # So first signal is saved directly
                    self.master_dict[str(label)]["c"+str(co)]["groups"].update({1: x_train[no, co, :]})
                    # and count is updated to 1
                    self.master_dict[str(label)]["c"+str(co)]["count"].update({1: 1})

                else:

                    # if not first run, then for every subgroup for the current component in the current signal,
                    d_group_cor = {}
                    for gr in self.master_dict[str(label)]["c"+str(co)]["groups"].keys():

                        d_sig = self.master_dict[str(label)]["c"+str(co)]["groups"][gr]
                        # do average signal by dividing component by count
                        d_sig = np.divide(d_sig, self.master_dict[str(label)]["c"+str(co)]["count"][gr])

                        # look for the correlation and save in correlations dict
                        cor = pearsonr(d_sig, x_train[no, co, :])[0]
                        d_group_cor.update({gr:cor})

                    # look for the subgroup with maximum correlation
                    top_hit = max(d_group_cor, key=d_group_cor.get)

                    # if maximum correlation found is higher than min_correlation
                    if d_group_cor[top_hit] > self.min_correlation:

                        d_sig = self.master_dict[str(label)]["c"+str(co)]["groups"][top_hit]
                        count = self.master_dict[str(label)]["c"+str(co)]["count"][top_hit]

                        # component of signal belongs to this subgroup. Add to subgroup array and update count +1
                        self.master_dict[str(label)]["c"+str(co)]["groups"].update({top_hit:np.add(d_sig, x_train[no, co, :])})
                        self.master_dict[str(label)]["c"+str(co)]["count"].update({top_hit:count+1})

                    else:

                        c = self.master_dict[str(label)]["c"+str(co)]["count"].keys()

                        # if number of existing subgroups is lower than max_subgroups
                        if len(c) < self.max_subgroups:

                            current_n = max(c)
                            new_g = current_n + 1

                            # update with new subgroup
                            self.master_dict[str(label)]["c"+str(co)]["groups"].update({new_g:x_train[no, co, :]})
                            self.master_dict[str(label)]["c"+str(co)]["count"].update({new_g:1})

                        # if max_subgroups is reached, then update subgroup with higher correlation
                        else:

                            d_sig = self.master_dict[str(label)]["c"+str(co)]["groups"][top_hit]
                            count = self.master_dict[str(label)]["c"+str(co)]["count"][top_hit]

                            self.master_dict[str(label)]["c"+str(co)]["groups"].update({top_hit:np.add(d_sig, x_train[no, co, :])})
                            self.master_dict[str(label)]["c"+str(co)]["count"].update({top_hit:count+1})




    def predict(self, signals, tolerance, ax_independent=False, verbose=False):
        """
        Predict the class of a signal

        Parameters
        ----------
        signals : nd array
            The array containing the signals. the dimensions are (number of signal x components x signal)
        tolerance : int or float
            A number that represents a tolerance. If difference is higher to this tolerance, then it belongs to another class.
            If all classes are outside of this tolerance, then we found a new class or we have an anomaly
        verbose : bool
            nothing defined

        """
        # expand dimension to 3. So we can use this function with one or with many signals
        for no in range(len(signals.shape), 3):
            signals = np.expand_dims(signals, axis=0)

        last_cls_diff = 0

        ret = []
        # for every signal to predict
        for no in range(0, signals.shape[0]):

            dis_dict = {}
            dis_la_dict = {}
            # for every label in master dict
            for la in self.master_dict.keys():

                abs_dis = 0
                co_dict = {}
                # for every component
                for co in range(0, signals.shape[1]):

                    cor_dict = {}
                    # for every subgroup
                    for gr in self.master_dict[la]["c"+str(co)]["groups"].keys():

                        # look for correlation
                        d_sig = self.master_dict[la]["c"+str(co)]["groups"][gr]
                        d_sig = np.divide(d_sig, self.master_dict[la]["c"+str(co)]["count"][gr])
                        cor = pearsonr(d_sig, signals[no, co, :])[0]

                        # update dict with correlations
                        cor_dict.update({gr:cor})

                    # look for maximum correlation
                    top_hit = max(cor_dict, key=cor_dict.get)

                    # do average
                    d_sig = self.master_dict[la]["c"+str(co)]["groups"][top_hit]
                    d_sig = np.divide(d_sig, self.master_dict[la]["c"+str(co)]["count"][top_hit])

                    # calculate difference
                    dis = np.subtract(d_sig, signals[no, co, :])
                    dis = np.absolute(dis)
                    d = np.divide(np.sum(dis), signals.shape[2])
                    co_dict.update({co:d})

                dis_la_dict.update({la: co_dict})
                for la in dis_la_dict.keys():
                    dis = 0
                    for co in dis_la_dict[la].keys():
                        dis += dis_la_dict[la][co]
                    abs_dis = float(dis) / float(signals.shape[1])
                    dis_dict.update({la:abs_dis})

            if verbose:
                print(dis_dict)
                #print(dis_la_dict)

            # get the class with minimum difference
            min_cls = min(dis_dict, key=dis_dict.get)


            flag = False
            for co in dis_la_dict[min_cls].keys():
                if dis_la_dict[min_cls][co] > tolerance:
                    flag = True
                if dis_la_dict[min_cls][co] > last_cls_diff:
                    last_cls_diff = dis_la_dict[min_cls][co]


            # if distance is bigger than tolerance, then class -1 (-1 = Anomaly or unknown class)
            if self.outliers:

                if flag:
                    ret.append(-1)              # -1 = Anomaly or unknown class
                else:
                    ret.append(min_cls)

            else:
                ret.append(min_cls)

        if verbose:
            print("Maximal difference found: ", last_cls_diff)

        # return prediction
        return np.array(ret).astype(int)