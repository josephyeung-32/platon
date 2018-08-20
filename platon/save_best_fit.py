from __future__ import division
import numpy as np
from sys import stdout
import os, glob

def signiDigits(xMean,dx1Low,dx1Upp):
    if dx1Low>0:
        scaleOfUncertainty = np.log10(dx1Low)
        if np.isinf(scaleOfUncertainty) == False:
            n=-int(scaleOfUncertainty)+2
        else:
            n=3
    else:
        n=0
    if n<0:
        n=0
    return round(xMean,n),round(dx1Low,n),round(dx1Upp,n),n


def mcmcstats(samp,logl,fit_label):
    txt=''
    ind = logl.argmax()
    lnprobBestFit = logl[ind]
    txt = txt + 'Max lnprobability = ' + str(lnprobBestFit) + ' (index = %d)'%ind + '\n'
    bestFitlnlike = samp[ind]

    x50 = np.percentile(samp,50,axis=0)
    x16 = np.percentile(samp,16,axis=0)
    x84 = np.percentile(samp,84,axis=0)
    dx1Low = x50-x16
    dx1Upp = x84-x50

    nCol=x50.shape[0]
    for i in range(nCol):
        m,l,u,n=signiDigits(x50[i],dx1Low[i],dx1Upp[i])
        if dx1Low[i]<1e+6:
            fmt1='%1.'+str(n)+'f'
            fmt2='%+1.'+str(n)+'f'
        else:
            fmt1='%.3e'
            fmt2='%.3e'
        txt = txt + ('%30s :  '+fmt1+'  '+fmt2+'  '+fmt2+'  ('+ fmt1+')\n') % (fit_label[i], m, -l, u, bestFitlnlike[i])

    return txt

def pd2latex(samp,logl,fit_label):
    x50 = np.percentile(samp,50,axis=0)
    dxLow = x50-np.percentile(samp,16,axis=0)
    dxUpp = np.percentile(samp,84,axis=0)-x50
    #print str(sigma)+'-sigma bounds:'

    nCol=x50.shape[0]
    txt=''
    for i in range(nCol):
        m,l,u,n=signiDigits(x50[i],dxLow[i],dxUpp[i])
        if dxLow[i]<1e+6:
            fmt1='%1.'+str(n)+'f'
            fmt2='%+1.'+str(n)+'f'
        else:
            fmt1='%.3e'
            fmt2='%.3e'
        txt = txt + ('%30s :  '+fmt1+'_{'+fmt2+'}^{'+fmt2+'}\n') % (fit_label[i], m, -l, u)
    return txt

def calcParaEstimates(samples,logl,fit_label):
    txt1 = pd2latex(samples,logl,fit_label)+'\n'
    txt2 = mcmcstats(samples,logl,fit_label)
    print (txt1)
    print (txt2)
    text_file = open('BestFit.txt', 'w')
    text_file.write(txt1)
    text_file.write(txt2)
    text_file.close()