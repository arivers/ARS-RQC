#!/usr/bin/env python3
# rqcparser.py - A module for parsing files generated by rqcfilter
# Adam Rivers 02/2017 USDA-ARS-GBRU

import pandas as pd
import json
import numpy as np
import os
import logging
from ars_rqc.definitions import ROOT_DIR


def _header_lines(file, symbol='#'):
    """returns number of header lines at the beginning of a file and the total number of lines"""
    try:
        with open(file, 'r') as f:
            lc = 0
            for n, line in enumerate(f):
                if line.startswith(symbol):
                    lc += 1
            return lc, n + 1
    except IOError:
        print("could not open file {}".format(file))


def _remove_percent(llist):
    """removes percent signs from the end of items in list and retuns list"""
    # this removes the percent signs from columns
    try:
        ll = []
        for item in llist:
            if isinstance(item, str):
                if item.strip().endswith('%'):
                    ll.append(item.strip()[:-1])
                else:
                    ll.append(item)
            else:
                ll.append(item)
        return ll
    except RuntimeError:
        print("Could not remove percentages frome some columns, returning the \
              origional list.")
    return llist

def rmdfpct(df):
    """Removes percents from columns in data frames repalcing them with
    numeric values"""
    for col in df:
        qc = "df." + col + ".dtype"
        try:
            if eval(qc) == 'O':
                qry = 'df.' + col + '.str.strip("%")'
                df[col] = pd.to_numeric(eval(qry))
        except:
            logging.warn("could not evaluate a column in the dataframe")
            continue
    return df

def _parser_1(file):
    """Takes a file awith any number of # commented lines followed by
    a header line with a leading # and returns a dictionary containing a list
    oriented dictionary of a pandas dataframe."""
    try:
        f = os.path.abspath(file)
        hlines, totlines = _header_lines(f)
        if hlines==totlines:
            return {"dataframe": None}
        dta = pd.read_csv(f, sep="\t", skiprows=hlines-1, comment=None)
        
        # Remove # from the first header row if present
        if dta.columns[0].startswith('#'):
            dta = dta.rename(index=str, columns={dta.columns[0]:
                             dta.columns[0][1:]})
        # remove percent signs from data columns
        dta = rmdfpct(dta)
        return {"dataframe": dta.to_dict(orient='list')}
    except RuntimeError:
        logging.error("could not parse the file {}".format(file))


def _parser_2(file):
    """Reads files with preliminary lines of key-value data
    prefixed by a # followed by one header line preceded by a #, followed by
    tabular data. Converts tabular data to pandas dataframe then returns a
    a dictionary with the key-value data and a list oriented dictionary of the
    pandas dataframe."""
    try:
        f = os.path.abspath(file)
        hlines, totlines = _header_lines(f)  # Count number of header lines
        ddict = {}  # Create temporary dictionary
        with open(f, 'r') as d1:  # Open the data file
            for n, line in enumerate(d1):  # Read and count lines
                if n < (hlines - 1):
                    llist = line.strip().split('\t')
                    ll = _remove_percent(llist)
                    try:
                        if len(ll) == 2:
                                cleankey = ll[0][1:]
                                ddict[cleankey] = ll[1]
                    except RuntimeError:
                        print("parser 2 failed: There were not two columns in \
                              line {}".format(str(n+1)))
                else:
                    break
        dataframe = _parser_1(file)["dataframe"]
        return {"desc": ddict, "dataframe": dataframe}
    except RuntimeError:
        logging.error("Could not parse file {}".format(file))


def _parser_3(file):
    """Converts bbduk filter contaminants scaffold report files to a dictionary
    containing descriptive statistics and a list oriented dictionary of a
    pandas dataframe."""
    try:
        f = os.path.abspath(file)
        hlines, totlines = _header_lines(f)  # Count number of header lines
        ddict = {}  # Create temporary dictionary
        with open(f, 'r') as d1:  # Open the data file
            for n, line in enumerate(d1):  # Read and count lines
                llist = line.strip().split('\t')
                ll = _remove_percent(llist)
                if n == 0:
                    continue
                if n == 1:
                    ddict["TotalReads"] = ll[1]
                    ddict["TotalBases"] = ll[2]
                elif n == 2:
                    ddict["ReadsMatched"] = ll[1]
                    ddict["PctReadsMatched"] = ll[2]
                else:
                    break
        dataframe = _parser_1(file)["dataframe"]
        return {"desc": ddict, "dataframe": dataframe}
    except RuntimeError:
        logging.error("Could not parse file {}".format(file))

def _parser_4(file):
    """Converts bbduk trim adaptor report files to a dictionary containing
    descriptive statistics and a pandas dataframe"""
    try:
        f = os.path.abspath(file)
        hlines, totlines = _header_lines(f)  # Count number of header lines
        ddict = {}  # Create temporary dictionary
        with open(f, 'r') as d1:  # Open the data file
            for n, line in enumerate(d1):  # Read and count lines
                llist = line.strip().split('\t')
                ll = _remove_percent(llist)
                if n == 0:
                    continue
                if n == 1:
                    ddict["TotalReads"] = ll[1]
                elif n == 2:
                    ddict["ReadsMatched"] = ll[1]
                    ddict["PctReadsMatched"] = ll[2]
                else:
                    break
        dataframe = _parser_1(file)["dataframe"]
        return {"desc": ddict, "dataframe": dataframe}
    except RuntimeError:
        logging.error("Could not parse file {}".format(file))


def _parser_5(file):
    with open(os.path.abspath(file), 'r') as f:
        value = f.readline().strip()
        pname = os.path.basename(file).split(".")[0]
        return {"desc": {pname: value}}

def _parser_6(file):
    """Reads sendsketch files"""
    try:
        f = os.path.abspath(file)
        ddict = {}  # Create temporary dictionary
        with open(f, 'r') as d1:  # Open the data file
            for line in d1:  # Read and count lines
                if line.startswith("Query"):
                    llist = line.strip().split('\t')
                    newlist = []
                    for j in llist:
                        ml = j.split(': ')
                        for k in ml:
                            newlist.extend([k])
                    ddict[newlist[2]] = newlist[3]
                    ddict[newlist[4]] = int(newlist[5])
                    ddict[newlist[6]] = int(newlist[7])
                    ddict[newlist[8]] = int(newlist[9])
                    ddict[newlist[10]] = int(newlist[11])
                    break
        dta = pd.read_csv(f, sep="\t", skiprows=2, comment=None)
        dta = rmdfpct(dta)
        return {"desc": ddict, "dataframe": dta.to_dict(orient='list')}
    except RuntimeError:
        logging.error("Could not parse file {}".format(file))


def _select_pfunc(file):
    try:
        fbase = os.path.basename(file)
        with open(os.path.join(ROOT_DIR, 'data', 'parameters.json'), 'r') as p:
            fastq_parameters = json.load(p)
            if fbase in fastq_parameters["parser"]:
                pfunc = fastq_parameters["parser"][fbase]
                return "_" + str(pfunc)
            else:
                return None
    except IOError:
        logging.error("Could not determine the correct parsing function to use for the \
              file {}. Check the paramaters.json file".format(file))


def parse_dir(dir):
    """ takes a file path looks the file name up in the parameters file and \
    returns a dataframe"""
    bname = os.path.basename(dir)
    ddict = {}
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            filepath = (os.path.join(root, name))
            try:
                pfunc = _select_pfunc(name)
                if pfunc:
                    command = str(pfunc) + '("' + str(filepath) + '")'
                    result = eval(command)
                    ddict[name] = result
                    logging.info("processing file {}".format(filepath))
                else:
                    logging.info("skipping file {}".format(filepath))
                    continue
            except IOError:
                logging.error("could not parse file {}".format(filepath))
                continue
    return ddict
