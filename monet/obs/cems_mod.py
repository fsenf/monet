from __future__ import print_function
import os
import datetime
import pandas as pd
import numpy as np
"""
NAME: cems_mod.py
PGRMMER: Alice Crawford   ORG: ARL
This code written at the NOAA air resources laboratory
Python 3
#################################################################
"""


def get_stack_dict(df, orispl=None):
    """
    Parameters
    ----------
    df dataframe created with stack_height() call
    orispl : list
           list of orispl codes to consider
    Returns
    -------
    stackhash: dictionary
    key orispl code and value list of tuples with
    (stackid, stackht (in feet))
    """
    stackhash = {}
    df = df[df['orispl_code'].isin(orispl)]
    #df = df[['orispl_code', 'boilerid', 'stackht','stackdiam']]

    def newc(x):
        return (x['boilerid'], x['stackht'], x['stackdiam'], x['stacktemp'],
                x['stackvel'])
    for oris in df['orispl_code'].unique():
        dftemp = df[df['orispl_code'] == oris]
        dftemp['tuple'] = dftemp.apply(newc, axis=1)
        value = dftemp['tuple'].unique()
        stackhash[oris] = value
    return stackhash


def max_stackht(df, meters=True, verbose=False):
    """
       adds 'max_stackht' column to dataframe returned by stack_height function.
       this column indicates the largest stack height associated with that
       orispl code.
    """
    df2 = pd.DataFrame()
    iii = 0
    mult = 1
    if meters:
        mult = 0.3048
    for orispl in df['orispl_code'].unique():
        dftemp = df[df['orispl_code'] == orispl]
        slist = mult * np.array(dftemp['stackht'].unique())

        maxval = np.max(slist)
        dftemp['max_stackht'] = maxval
        dftemp.drop(['stackht', 'stackdiam'], inplace=True, axis=1)
        dftemp.drop_duplicates(inplace=True)
        #dftemp['list_stackht'] = 0
        #dftemp.at[orispl, 'list_stackht'] =  list(slist)

        if iii == 0:
            df2 = dftemp.copy()
        else:
            df2 = pd.concat([df2, dftemp], axis=0)
        iii += 1
        if verbose:
            print('ORISPL', orispl, maxval, slist)
        # print(dftemp['list_stackht'].unique())
    return df2


def read_stack_height(verbose=False, testing=False):
    """
    reads file with information on stack heights and diameters and returns a
    dataframe.
    Parameters
    ----------
    verbose: boolean
             if true prints out header information in file.
    testing: boolean
             if true returns dataframe with more columns
    Returns
    -------
    df2: pandas dataframe
         dataframe which contains columns which have stack height and diameter
         for each orispl code and stackid.

    TO DO: CEMS data contains a unit_id but this doesn't seem to correspond to
    the ids availble in the ptinv file. Not clear how to match individual units
    with the same orispl code.
    """
    pd.options.mode.chained_assignment = None
    # This file was obtained from Daniel Tong and Youhua Tang 9/13/2018
    # stack height is in feet in the file.
    basedir = os.path.abspath(os.path.dirname(__file__))[:-3]
    fn = 'ptinv_ptipm_cap2005nei_20jun2007_v0_orl.txt'
    fname = os.path.join(basedir, 'data', fn)

    df = pd.read_csv(fname, comment='#')
    orispl = 'ORIS_FACILITY_CODE'
    # drop rows which have nan in the ORISPL code.
    df.dropna(inplace=True, axis=0, subset=['ORIS_FACILITY_CODE'])
    #df[orispl].fillna(-999, inplace=True)
    df[orispl] = df[orispl].astype(int)

    if verbose:
        print('Data available in ptinv file')
        print(df.columns.values)
        print('----------------------------')
    if testing:  # for testing purposes output all the id codes.
        df2 = df[['STACKID', 'PLANTID', 'POINTID', 'FIPS', 'ORIS_BOILER_ID',
                  'STKHGT', 'STKDIAM', orispl, 'PLANT']]
        df2.columns = ['stackid', 'plantid', 'pointid', 'fips', 'boiler',
                       'stackht', 'stackdiam', 'orispl_code', 'plant']
    else:
    ##May use stack diamter, temperature and velocity for plume rise.
    ##match the oris_boiler_ID to unitid from the cems data.
        df2 = df[[orispl, 'STACKID','ORIS_BOILER_ID',
                 'STKHGT', 'STKDIAM', 'STKTEMP','STKVEL']]
        df2.columns = ['orispl_code', 'stackid', 'boilerid',
                       'stackht','stackdiam','stacktemp','stackvel']
    df2.drop_duplicates(inplace=True)
    df2 = df2[df2['orispl_code'] != -999]
    #df2 = max_stackht(df2)
    #df2.drop(['stackht'], inplace=True)
    # df2.drop_duplicates(inplace=True)
    #print('done here')
    return df2


def getdegrees(degrees, minutes, seconds):
    """
    Parameters
    ----------
    degrees: integer
    minutes: integer
    seconds: integer

    Returns
    ----------
    decimal degrees.
    """
    return degrees + minutes / 60.0 + seconds / 3600.00


def addmonth(dt):
    """
    Parameters
    ----------
    dt : datetime object

    Returns: datetime object
    datetime that is one month from input datetime.
    handles ambiguities that arise when input date is
    at the end of a month and next month does not have the
    same number of days.

    """
    month = dt.month + 1
    year = dt.year
    day = dt.day
    hour = dt.hour
    if month > 12:
        year = dt.year + 1
        month = month - 12
        if day == 31 and month in [4, 6, 9, 11]:
            day = 30
        if month == 2 and day in [29, 30, 31]:
            if year % 4 == 0:
                day = 29
            else:
                day = 28
    return datetime.datetime(year, month, day, hour)


def get_date_fmt(date, verbose=False):
    """Determines what format of the date is in.
    In some files year is first and others it is last.
    Parameters
    ----------
    date: str
          with format either YYYY-mm-DD or mm-DD-YYYY
    verbose: boolean
          if TRUE print extra information
    Returns
    --------
    fmt: str
        string which can be used with datetime object to give format of date
        string.
    """
    if verbose:
        print('Determining date format')
    if verbose:
        print(date)
    temp = date.split('-')
    if len(temp[0]) == 4:
        fmt = "%Y-%m-%d %H"
    else:
        fmt = "%m-%d-%Y %H"
    return fmt


class CEMS(object):
    """
    Class for data from continuous emission monitoring systems (CEMS).
    Data from power plants can be downloaded from
    ftp://newftp.epa.gov/DMDNLoad/emissions/

   Attributes
    ----------
    efile : type string
        Description of attribute `efile`.
    url : type string
        Description of attribute `url`.
    info : type string
        Information about data.
    df : pandas DataFrame
        dataframe containing emissions data.
   Methods
    ----------
    __init__(self)
    add_data(self, rdate, states=['md'], download=False, verbose=True):
    load(self, efile, verbose=True):
    retrieve(self, rdate, state, download=True):

    match_column(self, varname):
    get_var(self, varname, loc=None, daterange=None, unitid=-99, verbose=True):
    retrieve(self, rdate, state, download=True):
    create_location_dictionary(self):
    rename(self, ccc, newname, rcolumn, verbose):
    """

    def __init__(self):
        self.efile = None
        self.url = "ftp://newftp.epa.gov/DmDnLoad/emissions/"
        self.lb2kg = 0.453592  # number of kilograms per pound.
        self.info = "Data from continuous emission monitoring systems (CEMS)\n"
        self.info += self.url + '\n'
        self.df = pd.DataFrame()
        self.namehash = {
        }  # if columns are renamed keeps track of original names.
        # Each facility may have more than one unit which is specified by the
        # unit id.

    def __str__(self):
        return self.info

    def add_data(self, rdate, states=['md'], download=False, verbose=True):
        """
           gets the ftp url from the retrieve method and then
           loads the data from the ftp site using the load method.

        Parameters
        ----------
        rdate : single datetime object of list of datetime objects
               The first datetime object indicates the month and year of the
               first file to retrieve.
               The second datetime object indicates the month and year of the
               last file to retrieve.
        states : list of strings
             list of two letter state identifications.
        download : boolean
               if download=True then retrieve will download the files and load
               will read the downloaded files.
               if download=False then retrieve will return the url and load
               will read directly from ftp site.
        verbose : boolean
               if TRUE prints out additional information.
        Returns
        -------
        boolean True

        """
        if isinstance(states, str):
            states = [states]
        if isinstance(rdate, list):
            r1 = rdate[0]
            r2 = rdate[1]
            rdatelist = [r1]
            done = False
            iii = 0
            while not done:
                r3 = addmonth(rdatelist[-1])
                if r3 <= r2:
                    rdatelist.append(r3)
                else:
                    done = True
                if iii > 100:
                    done = True
                iii += 1
        else:
            rdatelist = [rdate]
        for rd in rdatelist:
            print('getting data')
            print(rd)
            for st in states:
                url = self.retrieve(rd, st, download=download, verbose=verbose)
                self.load(url, verbose=verbose)
        return self.df

    def match_column(self, varname):
        """varname is list of strings.
           returns column name which contains all the strings.
        """
        columns = list(self.df.columns.values)
        cmatch = None
        for ccc in columns:
            # print('-----'  + ccc + '------')
            # print( temp[ccc].unique())
            match = 0
            for vstr in varname:
                if vstr.lower() in ccc.lower():
                    match += 1
            if match == len(varname):
                cmatch = ccc
        return cmatch

    def cemspivot(self, varname, daterange=None, unitid=False, stackht=False,
                  verbose=True):
        """
        Parameters
        ----------
        varname: string
            name of column in the cems dataframe
        daterange: list of two datetime objects
            define a date range
        unitid: boolean.
                 If True and unit id columns exist then these will be kept as
                 separate columns in the pivot table.
        verbose: boolean
                 if true print out extra information.
        stackht: boolean
                 NOT IMPLEMENTED YET. if true stack height is in header column.
        Returns: pandas DataFrame object
            returns dataframe with rows time. Columns are (orispl_code,
            unit_id).
            If no unit_id in the file then columns are just orispl_code.
            if unitid flag set to False then sums over unit_id's that belong to
             an orispl_code. Values are from the column specified by the
             varname input.
        """
        from .obs_util import timefilter
        stackht = False  # option not tested.
        temp = self.df.copy()
        if daterange:
            temp = timefilter(temp, daterange)
        if stackht:
            stack_df = read_stack_height(verbose=verbose)
            olist = temp['orispl_code'].unique()
            stack_df = stack_df[stack_df['orispl_code'].isin(olist)]
            stack_df = max_stackht(stack_df)
            temp = temp.merge(stack_df, left_on=['orispl_code'],
                              right_on=['orispl_code'], how='left')
        if 'unitid' in temp.columns.values and unitid:
            #if temp['unit_id'].unique():
            #    if verbose:
            #        print('UNIT IDs ', temp['unit_id'].unique())
            cols = ['orispl_code', 'unitid']
            if stackht:
                cols.append('stackht')
        else:
            cols = ['orispl_code']
            if stackht:
                cols.append('max_stackht')

        # create pandas frame with index datetime and columns for value for
        # each unit_id,orispl
        pivot = pd.pivot_table(
            temp,
            values=varname,
            index=['time'],
            columns=cols,
            aggfunc=np.sum)
        #print('PIVOT ----------')
        # print(pivot[0:20])
        return pivot

    def get_var(self,
                varname,
                orisp=None,
                daterange=None,
                unitid=-99,
                verbose=True):
        """
           returns time series with variable indicated by varname.
           returns data frame where rows are date and columns are the
           values of cmatch for each fac_id.

           routine looks for column which contains all strings in varname.
           Currently not case sensitive.

           loc and ORISPL CODES.
           unitid is a unit_id

           if a particular unitid is specified then will return values for that
            unit.
        Parameters
        ----------
        varname : string or iteratable of strings
            varname may be string or list of strings.
        loc : type
            Description of parameter `loc`.
        daterange : type
            Description of parameter `daterange`.

        Returns
        -------
        type
            Description of returned object.
        """
        if unitid == -99:
            ui = False
        temp = self.cemspivot(varname, daterange, unitid=ui)
        if not ui:
            returnval = temp[orisp]
        else:
            returnval = temp[orisp, unitid]
        return returnval

    def retrieve(self, rdate, state, download=True, verbose=False):
        """Short summary.

        Parameters
        ----------
        rdate : datetime object
             Uses year and month. Day and hour are not used.
        state : string
            state abbreviation to retrieve data for
        download : boolean
            set to True to download
            if download FALSE then returns string with url of ftp
            if download TRUE then returns name of downloaded file

        Returns
        -------
        efile string
            if download FALSE then returns string with url of ftp
            if download TRUE then returns name of downloaded file
        """
        # import requests
        # TO DO: requests does not support ftp sites.
        efile = 'empty'
        ftpsite = self.url
        ftpsite += 'hourly/'
        ftpsite += 'monthly/'
        ftpsite += rdate.strftime("%Y") + '/'
        print(ftpsite)
        print(rdate)
        print(state)
        fname = rdate.strftime("%Y") + state + rdate.strftime("%m") + '.zip'
        if not download:
            efile = ftpsite + fname
        if not os.path.isfile(fname):
            # print('retrieving ' + ftpsite + fname)
            # r = requests.get(ftpsite + fname)
            # open(efile, 'wb').write(r.content)
            # print('retrieved ' + ftpsite + fname)
            efile = ftpsite + fname
            print('WARNING: Downloading file not supported at this time')
            print('you may download manually using the following address')
            print(efile)
        else:
            print('file exists ' + fname)
            efile = fname
        self.info += 'File retrieved :' + efile + '\n'
        return efile

    def create_location_dictionary(self, verbose=False):
        """
        returns dictionary withe key orispl_code and value  (latitude,
        longitude) tuple
        """
        if 'latitude' in list(self.df.columns.values):
            dftemp = self.df.copy()
            pairs = zip(dftemp['orispl_code'],
                        zip(dftemp['latitude'], dftemp['longitude']))
            pairs = list(set(pairs))
            lhash = dict(pairs)  # key is facility id and value is name.
            if verbose:
                print(lhash)
            return lhash
        else:
            return False

    def create_name_dictionary(self, verbose=False):
        """
        returns dictionary withe key orispl_code and value facility name
        """
        if 'latitude' in list(self.df.columns.values):
            dftemp = self.df.copy()
            pairs = zip(dftemp['orispl_code'], dftemp['facility_name'])
            pairs = list(set(pairs))
            lhash = dict(pairs)  # key is facility id and value is name.
            if verbose:
                print(lhash)
            return lhash
        else:
            return False

    def columns_rename(self, columns, verbose=False):
        """
        Maps columns with one name to a standard name
        Parameters:
        ----------
        columns: list of strings

        Returns:
        --------
        rcolumn: list of strings
        """
        rcolumn = []
        for ccc in columns:
            if 'facility' in ccc.lower() and 'name' in ccc.lower():
                rcolumn = self.rename(ccc, 'facility_name', rcolumn, verbose)
            elif 'orispl' in ccc.lower():
                rcolumn = self.rename(ccc, 'orispl_code', rcolumn, verbose)
            elif 'facility' in ccc.lower() and 'id' in ccc.lower():
                rcolumn = self.rename(ccc, 'fac_id', rcolumn, verbose)
            elif 'so2' in ccc.lower() and ('lbs' in ccc.lower()
                                           or 'pounds' in ccc.lower()) and (
                                               'rate' not in ccc.lower()):
                rcolumn = self.rename(ccc, 'so2_lbs', rcolumn, verbose)
            elif 'nox' in ccc.lower() and ('lbs' in ccc.lower()
                                           or 'pounds' in ccc.lower()) and (
                                               'rate' not in ccc.lower()):
                rcolumn = self.rename(ccc, 'nox_lbs', rcolumn, verbose)
            elif 'co2' in ccc.lower() and ('short' in ccc.lower()
                                           and 'tons' in ccc.lower()):
                rcolumn = self.rename(ccc, 'co2_short_tons', rcolumn, verbose)
            elif 'date' in ccc.lower():
                rcolumn = self.rename(ccc, 'date', rcolumn, verbose)
            elif 'hour' in ccc.lower():
                rcolumn = self.rename(ccc, 'hour', rcolumn, verbose)
            elif 'lat' in ccc.lower():
                rcolumn = self.rename(ccc, 'latitude', rcolumn, verbose)
            elif 'lon' in ccc.lower():
                rcolumn = self.rename(ccc, 'longitude', rcolumn, verbose)
            elif 'state' in ccc.lower():
                rcolumn = self.rename(ccc, 'state_name', rcolumn, verbose)
            else:
                rcolumn.append(ccc.strip().lower())
        return rcolumn

    def rename(self, ccc, newname, rcolumn, verbose):
        """
        keeps track of original and new column names in the namehash attribute
        Parameters:
        ----------
        ccc: str
        newname: str
        rcolumn: list of str
        verbose: boolean
        Returns
        ------
        rcolumn: list of str
        """
        # dictionary with key as the newname and value as the original name
        self.namehash[newname] = ccc
        rcolumn.append(newname)
        if verbose:
            print(ccc + ' to ' + newname)
        return rcolumn

    def add_info(self, dftemp):
        """
        -------------Load supplmental data-----------------------
        Add location (latitude longitude) and time UTC information to dataframe
         dftemp.
        cemsinfo.csv contains info on facility id, lat, lon, time offset from
         UTC.
        allows transformation from local time to UTC.
        If not all power stations are found in the cemsinfo.csv file,
        then Nan will be written in lat, lon and 'time' column.

        Parameters
        ----------
        dftemp: pandas dataframe

        Returns
        ----------
        dftemp: pandas dataframe
        """
        basedir = os.path.abspath(os.path.dirname(__file__))[:-3]
        iname = os.path.join(basedir, 'data', 'cemsinfo.csv')
        # iname = os.path.join(basedir, 'data', 'cem_facility_loc.csv')
        method = 1
        # TO DO: Having trouble with pytest throwing an error when using the
        # apply on the dataframe.
        # runs ok, but pytest fails. Tried several differnt methods.
        if os.path.isfile(iname):
            sinfo = pd.read_csv(iname, sep=',', header=0)
            try:
                dftemp.drop(['latitude', 'longitude'], axis=1, inplace=True)
            except Exception:
                pass
            dfnew = pd.merge(
                dftemp,
                sinfo,
                how='left',
                left_on=['orispl_code'],
                right_on=['orispl_code'])
            print('---------z-----------')
            print(dfnew.columns.values)
            # remove stations which do not have a time offset.
            dfnew.dropna(axis=0, subset=['time_offset'], inplace=True)
            if method == 1:
                # this runs ok but fails pytest
                def i2o(x):
                    return datetime.timedelta(hours=x['time_offset'])

                dfnew['time_offset'] = dfnew.apply(i2o, axis=1)
                dfnew['time'] = dfnew['time local'] + dfnew['time_offset']
            elif method == 2:
                # this runs ok but fails pytest
                def utc(x):
                    return pd.Timestamp(x['time local']) + datetime.timedelta(
                        hours=x['time_offset'])

                dfnew['time'] = dfnew.apply(utc, axis=1)
            elif method == 3:
                # this runs ok but fails pytest
                def utc(x, y):
                    return x + datetime.timedelta(hours=y)

                dfnew['time'] = dfnew.apply(
                    lambda row: utc(row['time local'], row['time_offset']),
                    axis=1)
            # remove the time_offset column.
            dfnew.drop(['time_offset'], axis=1, inplace=True)
            mlist = dftemp.columns.values.tolist()
            # merge the dataframes back together to include rows with no info
            # in the cemsinfo.csv
            dftemp = pd.merge(
                dftemp, dfnew, how='left', left_on=mlist, right_on=mlist)
        return dftemp
        # return dfnew

    def load(self, efile, verbose=False):
        """
        loads information found in efile into a pandas dataframe.
        Parameters
        ----------
        efile: string
             name of csv file to open or url of csv file.
        verbose: boolean
             if TRUE prints out information
        """

        # pandas read_csv can read either from a file or url.
        dftemp = pd.read_csv(efile, sep=',', index_col=False, header=0)
        columns = list(dftemp.columns.values)
        columns = self.columns_rename(columns, verbose)
        dftemp.columns = columns
        if verbose:
            print('Data available in CEMS file')
            print(columns)
        dfmt = get_date_fmt(dftemp['date'][0], verbose=verbose)

        # create column with datetime information
        # from column with month-day-year and column with hour.
        dftime = dftemp.apply(lambda x:
                              pd.datetime.strptime("{0} {1}".format(x['date'],
                                                                    x['hour']),
                                                   dfmt), axis=1)
        dftemp = pd.concat([dftime, dftemp], axis=1)
        dftemp.rename(columns={0: 'time local'}, inplace=True)
        dftemp.drop(['date', 'hour'], axis=1, inplace=True)

        # -------------Load supplmental data-----------------------
        # contains info on facility id, lat, lon, time offset from UTC.
        # allows transformation from local time to UTC.
        dftemp = self.add_info(dftemp)

        if ['year'] in columns:
            dftemp.drop(['year'], axis=1, inplace=True)
        if self.df.empty:
            self.df = dftemp
            if verbose:
                print('Initializing pandas dataframe. Loading ' + efile)
        else:
            self.df = self.df.append(dftemp)
            if verbose:
                print('Appending to pandas dataframe. Loading ' + efile)
        # if verbose: print(dftemp[0:10])
        return dftemp
