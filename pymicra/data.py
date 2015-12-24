#!/usr/bin/python
"""
Author: Tomas Chor
Date: 2015-08-07
-------------------------

This module works with micrometeorological data using pandas, numpy, datetime and several other packages

-------------------------

Modifications:


"""
import algs
import physics
import pandas as pd
import numpy as np

def rotCoor(data, wind_vars=['u','v','w'], verbose=0):
    """
    Rotates the coordinates of wind data
    ----------------------

    Parameters
    ----------
    data: pandas DataFrame 
        the dataFrame to be rotated
    wind_vars: list
        a list with the names of columns which define the wind speed, typically ['u','v','w']
    """
    from numpy import cos,sin,zeros,dot
    from math import atan2, sqrt
    DC= np.zeros((3,3))
    wind_vec = data[wind_vars].mean().values
    m_u, m_v, m_w = wind_vec
    alpha = atan2(m_v,m_u)
    beta =-atan2(m_w, sqrt((m_u**2.)+(m_v**2.)))
    if verbose:
        print "alpha: ",alpha,"\nbeta: ",beta
    # definition of rotation matrix
    DC[0,0],DC[0,1],DC[0,2] = np.cos(alpha)*np.cos(beta), np.cos(beta)*np.sin(alpha),-np.sin(beta)
    DC[1,0],DC[1,1],DC[1,2] =-np.sin(alpha)          , np.cos(alpha)          , 0.
    DC[2,0],DC[2,1],DC[2,2] = np.cos(alpha)*np.sin(beta), np.sin(alpha)*np.sin(beta), np.cos(beta)
    if verbose:
        print "Rotation matrix is:\n", DC
    # application of rotation as a matrix product
    data[wind_vars] = np.dot(DC, data[wind_vars].values.T).T
    return data


def trend(data, mode='moving average', rule=None, window=None, **kwargs):
    """
    Wrapper to return the trend given data. Can be achieved using a moving avg, block avg or polynomial fitting
    -------------

    Parameters
    ----------

    data: pandas DataFrame 
        the dataFrame to be rotated
    mode: string
        mode of average to apply. Currently {'moving', 'block'}.
    rule: string
        pandas offset string to define the block in the block average. Default is "10min".
    """
    mode=mode.lower().replace('_',' ').replace('-','').replace(' ','')
    if any(w==mode for w in ['moving', 'movingaverage']):
        # performs moving average on the data with window equivalent to the rule
        if window==None:
            print('warning: approximating window size for moving average')
            window=int(len(data)/len(data.resample(rule)))
        return pd.rolling_mean(data, window=window, **kwargs)
    elif any(w==mode for w in ['block', 'blockaverage']):
        # performs block average on the data with the window being the rule. Assumes that frequency is constant
        if rule==None:
            return data.apply(lambda x: [np.mean(x)]*len(x), axis=0)
        else:
            print 'Warning. Might be bugged. Check results.'
            freq=data.index.inferred_freq
            return data.resample(rule, how='mean', **kwargs).resample(freq, fill_method='pad')
    elif any(w in mode for w in ['linear', 'polynomial', 'fit']):
        # performs a polynomial fit on the data in blocks of "rule"
        from algs import fitByDate
        return fitByDate(data, rule=rule, **kwargs)
    else:
        # if no mode can be identified
        raise KeyError('Mode defined is not correct. Options are "moving" and "block".')

def detrend(data, mode='moving average', rule=None, suffix="'", **kwargs):
    """
    Returns the detrended fluctuations of a given dataset

    Parameters
    ----------

    data: pandas.DataFrame, pandas.Series

    mode: string
        what method to use in order to identify the trend
    rule: pandas offset string
        the blocks for which the trends should be calculated
    suffix: string
        suffix to add to variable names after fluctuation is extracted
    """
    from algs import stripDown
    from scipy import signal
    mode=stripDown(mode.lower(), args='-_')
    df=data.copy()
    if mode=='linear' or mode=='constant':
        df=df.apply(signal.detrend, axis=0, type=mode)
    elif mode=='block':
        df=df.apply(signal.detrend, axis=0, type='constant')
    else:
        df=df-trend(df, mode=mode, rule=rule, **kwargs)
    return df.add_suffix(suffix)


def spectrumDF(data, frequency=10, T_minutes=30, out_index='frequency', anti_aliasing=False):
    """
    Calculates the spectrum for a set of data

    Parameters
    ----------

    data: pandas.DataFrame
        dataframe with one (will return the spectrum) or two (will return to cross-spectrum) columns
    frequency: float
        frequency of measurement of signal to pass to numpy.fft.rfftfreq
    T_minutes: float
        period in minutes
    """
    T=T_minutes*60.     # convert from minutes to seconds
    N = len(data)
    co=False
    if type(data)==pd.DataFrame:
        if len(data.columns)==1:
            pass
        elif len(data.columns)==2:
            co=True
        else:
            raise Exception('Too many columns of data. Chose one (spectrum) or two (cross-spectrum')
    else:
        raise Exception('Input has to be pandas.DataFrame')

    cols=list(data.columns)
    spec = np.fft.rfft(data.iloc[:,0])
    spec = np.conj(spec)*np.fft.rfft(data.iloc[:,-1])
    spec*= 2./(frequency*N)
    freq = np.fft.rfftfreq(len(data), d=1./frequency)
    if co:
        varname='cross-spectrum_{}_{}'.format(*cols)
#        corr=np.correlate(data.iloc[:,0], data.iloc[:,-1], mode='same')
#        spec=(2./T)*np.fft.rfft(corr)
    else:
        varname='spectrum_{}'.format(cols[0])

    if out_index=='frequency':
        aux=pd.DataFrame( data={ varname : spec }, index=freq )
        aux.index.name='frequencies'
    else:
        raise NameError
    return aux


def bulkCorr(data):
    if type(data)==pd.DataFrame:
        a,b=data.columns
        a,b=data[a], data[b]
    else:
        a,b=data
    r=np.mean(a*b)
    r/=np.sqrt(np.nanmean(a*a))*np.sqrt(np.nanmean(b*b))
    return r


def mu_var(N):
    """
    from Bendat&Piersol
    """
    mu=N*(N-1.)/4.
    variance=N*(2.*N + 5.)*(N - 1.)/72.
    return mu, variance


def reverse_arrangement(array, points_number=None, alpha=0.05):
    '''
    Performs the reverse arrangement test
    according to Bendat and Piersol - Random Data - 4th edition, page 96

    Parameters
    ----------

    Array: np.array, list, tuple, generator
    array which to test for the reverse arrangement test

    points_number: integer
    number of chunks to consider to the test. Maximum is the length of the array.
    If it is less, then the number of points will be reduced by application of a mean

    alpha: float
    Significance level for which to apply the test

    WARNING! This fuction approximates table A.6 from Bendat&Piersol as a normal distribution.
    This may no be true, since they do not express which distribution they use to construct
    their table. However, in the range 9<N<101, this approximation is as good as 5% at N=10
    and 0.1% at N=100.
    '''
    if points_number==None:
        points_number=len(array)
        xarray=array
    elif points_number==len(array):
        xarray=array
    else:
        pts = len(array)//points_number
        xarray = []
        for j in range(0,points_number):
            xarray.append( np.mean(array[(j*pts):((j+1)*pts)]) ) # Calculo a media de cada um dos 50 intervalos

    A = []
    for i in range(len(xarray)-1):
        h = []
        for j in range(i,len(xarray)):
            if(xarray[i] > xarray[j]):
                h.append(1)
        A.append(sum(h))
    Atot = sum(A)
    N=len(xarray)
    mu,variance=mu_var(N)
    f=algs.inverse_normal_cdf(mu, np.sqrt(variance))
    phi1=1.-alpha/2.
    phi2=alpha/2.
    A1=f(phi1)
    A2=f(phi2)
    if A1 < Atot < A2:
        return True
    else:
        return False

def recspe(slow_spec, freqs, T):
    """
    Applied a correction factor to the spectrum of a slow-measured variable
    based on the response-time T

    Parameters:
    -----------
    freqs: numpy.array
        frequencies
    slow_spec: numpy.array
        the spectrum
    T: float
        the response-time
    """
    assert len(slow_spec)==len(freqs)
    return slow_spec*(1.0 + 4.*(np.pi**2.)*(freqs**2.) * (T**2.))
