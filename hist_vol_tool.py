import bsopt
import copy
import dateutil
SOLVER_ERROR_EPSILON = 1e-5
ITERATION_NUM = 100
ITERATION_STEP = 0.001
YEARLY_DAYS = 365.25
# Cash flow calculation for delta hedging.
# Inside the period, Vol is constant and hedging frequency is once per ndays
# bussinessDays is number of business days from the startD to expiryT

def delta_cashflow(df, vol, option_input, rehedge_period = 1, column = 'close'):
    CF = 0.0
    strike = option_input['strike']
    otype = option_input.get('otype', 1)
    expiry = option_input['expiry']
    rd = option_input['rd']
    rf = option_input.get('rf', rd)
    dfunc_name = option_input.get('delta_func', 'bsopt.BSDelta')
    delta_func = eval(dfunc_name)
    nlen = len(df.index)
    for pidx in range(int(nlen/rehedge_period)):
        idx = pidx * rehedge_period
        nxt_idx = min((pidx + 1) * rehedge_period, nlen)
        tau = (expiry - df.index[idx])/YEARLY_DAYS
        opt_delta = delta_func(otype, df[column][idx], strike, vol, tau, rd, rf)
        CF = CF + opt_delta * (df[column][nxt_idx] - df[column][idx])
    return CF

def realized_vol(df, option_input, calib_input, column = 'close'):
    strike = option_input['strike']
    otype = option_input.get('otype', 1)
    expiry = option_input['expiry']
    rd = option_input['rd']
    rf = option_input.get('rf', rd)
    
    ref_vol = calib_input.get('ref_vol', 0.5)
    opt_payoff = calib_input.get('opt_payoff', 0.0)
    rehedge_period = calib_input.get('rehedge_period', 1)
    fwd = df[column][0]
    is_dtime = calib_input.get('is_dtime', False)
    pricer_func = eval(option_input.get('pricer_func', 'bsopt.BSFwd'))

    if expiry < df.index[-1]:
        raise ValueError, 'Expiry time must be no earlier than the end of the time series'
    numTries = 0
    diff = 1000.0
    start_d = df.index[0]
    if is_dtime:
        start_d = startD.date()
    tau = (expiry - start_d).days/YEARLY_DAYS
    vol = ref_vol
    def func(x):
        return pricer_func(otype, fwd, strike, x, tau, rd, rf) + delta_cashflow(df, x, option_input, x, rehedge_period, column) - opt_payoff

    while diff >= SOLVER_ERROR_EPSILON and numTries <= ITERATION_NUM:
        current = func(vol)
        high = func(vol + ITERATION_STEP)
        low = func(vol - ITERATION_STEP)
        if high == low:
            volnext = max(vol -ITERATION_STEP, 1e-2)
        else:
            volnext = vol - 2* ITERATION_STEP * current/(high-low)
            if volnext < 1e-2:
                volnext = vol/2.0

        diff = abs(volnext - vol)
        vol = volnext
        numTries += 1

    if diff >= SOLVER_ERROR_EPSILON or numTries > ITERATION_NUM:
        return None
    else :
        return vol

def relative_date( ref_date, tenor):
    nlen = len(tenor)
    num = int(tenor[:-1])
    
    if tenor[-1] == 'm':
        key = 'months'
    elif tenor[-1] == 'y':
        key = 'years'
    elif tenor[-1] == 'w':
        key = 'weeks'
    elif tenor[-1] == 'd':
        key = 'days'
    input = { key: num }
    return ref_date + dateutil.relativedelta.relativedelta(**input)
            
def realized_termstruct(option_input, data):
    is_dtime = data.get('is_dtime', False)
    column = data.get('data_column', 'close')
    term_tenor = data.get('term_tenor', '1m')
    df = data['dataframe']
    calib_input = {'rehedge_period', data.get('rehedge_period', 1), }
                    
    expiry = option_input['expiry']
    otype = option_input.get('otype', 1)
    strike = option_input['strike']
    rd = option_input['rd']
    rf = option_input.get('rf', rd)    
    pricer_func = eval(option_input.get('pricer_func', 'bsopt.BSFwd'))
    if is_dtime:
        datelist = df['date']
        dexp = expiry.date()
    else:
        datelist = df.index
        dexp = expiry
    xdf = df[datelist <= dexp]
    datelist = datelist[datelist <= dexp]    
    end_d  = datelist[-1]
    final_value = 0.0
    vol_ts = pd.Series()
    while end_d > datelist[0]:
        start_d = relative_date(end_d, term_tenor)
        sub_df = xdf[(datelist <= end_d) & (datelist > start_d)]
        if len(sub_df) < 2:
            break
        if end_vol > 0:
            tau = (expiry - datelist[-1]).days/YEARLY_DAYS
            final_value = pricer_func(otype, sub_df[column][-1], strike, end_vol, tau, rd, rf)
            ref_vol = end_vol
        elif end_vol == 0:
            if otype:
                final_value = max((sub_df[column][-1] - strike), 0)
            else:
                final_value = max((strike - sub_df[column][-1]), 0)
            ref_vol = 0.5
        elif end_vol == None:
            raise ValueError, 'no vol is found to match PnL'
        calib_input['ref_vol'] = ref_vol
        calib_input['opt_payoff'] = final_value
        vol = realized_vol(sub_df, option_input, calib_input, column)
        vol_ts[sub_df.index[0]] = vol
        end_vol = vol
        end_d = start_d
    return vol_ts

def BS_VolSurf_TermStr(tsFwd, moneyness, expiryT, rd = 0.0, rf = 0.0, endVol = 0.0, termTenor="1m", rehedge_period ="1d", exceptionDateList=[]):
    ts =curve.Curve()
    rptTenor = '-' + termTenor


def BS_ConstDelta_VolSurf(tsFwd, moneynessList, expiryT, rd = 0.0, rf = 0.0, exceptionDateList=[]):
    ts = curve.Curve()
    rptTenor = '-1m'
    rehedge_period = '1d'
    IsCall = 1

    for d in tsFwd.Dates():
        if d not in exceptionDateList:
            ts[d] = tsFwd[d]

    DateList = [x for x in ts.Dates() if x not in exceptionDateList]
    TSstart = DateList[0]
    TSend = DateList[-1]

    date = copy.copy(TSend)
    endDate = tenor.RDateAdd('1d', date)
    startDate = tenor.RDateAdd(rptTenor, date, exceptionDateList)

    volTS = curve.GRCurve()
    while startDate >= TSstart:
        subTS = ts.Slice(startDate, endDate)
        vol = []
        if len(subTS) < 2:
            print 'No data in time series further than ', startDate
            break

        if 0.0 in subTS.Values():
            print 'Price is zero at some date from ', startDate, ' to ', endDate
            break

        # for the moment, consider ATM vol
        for m in moneynessList:
            strike = subTS.Values()[0] * m
            if IsCall:
                finalValue = max((subTS.Values()[-1] - strike), 0)
            else:
                finalValue = max((strike - subTS.Values()[-1]), 0)

        vol += [BSrealizedVol(IsCall, subTS, strike, expiryT, rd, rf, finalValue, rehedge_period, exceptionDateList)]
        if None in vol:
            print 'no vol is found to match PnL- strike:'+ str(m) + ' expiry:' + expiryT

        volTS[startDate] = vol
        startDate = tenor.RDateAdd(rptTenor, startDate, exceptionDateList)

    return volTS

def Spread_ATMVolCorr_TermStr(ts1, ts2, op, expiryT, r1 = 0, r2 = 0, termTenor="1m", exceptionDateList=[]):
    if op != '*' and op!= '/':
        raise ValueError, 'Operator has to be either * or / for Spread_ATMVolCorr_TermStr'

    dates = [ d for d in ts1.Dates() if d in ts2.Dates() and d <= expiryT]
    F1 = curve.Curve()
    F2 = curve.Curve()
    HR = curve.Curve()
    for d in dates:
        if ts1[d] > 0 and ts2[d]>0 :
            F1[d] = ts1[d]
            F2[d] = ts2[d]
            if op == '/':
                HR[d] = F1[d]/F2[d]
                r = r1 - r2
            else:
                HR[d] = F1[d] * F2[d]
                r = r1 + r2

    IsCall = 1
    HRVol= BS_ATMVol_TermStr(IsCall, HR, expiryT, rd = r, rf = 0.0, endVol = 0.0, termTenor=termTenor, rehedge_period ="1d", exceptionDateList=exceptionDateList)
    VolF1= BS_ATMVol_TermStr(IsCall, F1, expiryT, rd = r1, rf = 0.0, endVol = 0.0, termTenor=termTenor, rehedge_period ="1d", exceptionDateList=exceptionDateList)
    VolF2= BS_ATMVol_TermStr(IsCall, F2, expiryT, rd = r2, rf = 0.0, endVol = 0.0, termTenor=termTenor, rehedge_period ="1d", exceptionDateList=exceptionDateList)

    corr = curve.Curve()
    for d in HRVol.Dates():
        if op == '/':
            corr[d] = (VolF1[d]**2 + VolF2[d]**2 -HRVol[d]**2)/(2* VolF1[d] * VolF2[d])
        else:
            corr[d] = (HRVol[d]**2 - VolF1[d]**2 - VolF2[d]**2)/(2* VolF1[d] * VolF2[d])

    return HRVol, corr, VolF1, VolF2

def Crack_ATMVol_TermStr(tsList, weights, expiryT, termTenor="1m", exceptionDateList=[]):

    dates = []
    if len(tsList) != len(weights):
        raise ValueError, 'The number of elements of weights and time series should be equal'

    for ts in tsList:
        if dates == []:
            dates = ts.Dates()
        else:
            dates = [ d for d in ts.Dates() if d in dates]

    Crk = curve.Curve()
    undFwd = curve.Curve()

    for d in dates:
        Fwd = [ts[d] for ts in tsList]
        Crk[d] = sum([f*w for (f,w) in zip(Fwd, weights)])
        undFwd[d] = tsList[0][d]

    IsCall = 1
    CrkVol = BS_ATMVol_TermStr(IsCall, Crk, expiryT, rd = 0, rf = 0.0, endVol = 0.0, termTenor=termTenor, rehedge_period ="1d", exceptionDateList=exceptionDateList)
    undVol = BS_ATMVol_TermStr(IsCall, undFwd, expiryT, rd = 0, rf = 0.0, endVol = 0.0, termTenor=termTenor, rehedge_period ="1d", exceptionDateList=exceptionDateList)

    return CrkVol, undVol