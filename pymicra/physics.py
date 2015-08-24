#!/usr/bin/python
"""
Author: Tomas Chor

Module that contains physical functions for general use

ADD PINT FUNCTIONALITY LATER
"""

class constants(object):
    """
    Defines some useful constants for physical calculations involving gases and miscelaneous things
    """
    def __init__(self):
        self.molar_mass={'dry_air' : 28.9645,
            'o3'  : 47.99820,
            'h2o' : 18.0153,
            'co2' : 44.0095,
            'co'  : 28.0101,
            'ch4' : 16.0425,
            'n2o' : 44.01280,
            'o' : 15.99940,
            'n' : 14.00670}
    
        self.R=8.3144621     #universal gas constant J/(mol.K)
        R_spec={}
        for key, val in self.molar_mass.iteritems():
            R_spec.update( {key : self.R/val} )
        self.R_spec=R_spec
        self.units={'molar_mass' : 'g/mol',
            'R' : 'J/(mol * K)',
            'R_spec' : 'J/(g * K)'}


def perfGas(p=None, rho=None, R=None, T=None, gas='dry_air'):
    """
    Returns the only value that is not provided in the ideal gas law
    """
    aux=constants()
    R_spec=aux.R_spec[gas]
    if p == None:
        return rho*Ri_spec*T
    elif rho == None:
        return p / (R_spec*T)
    elif T == None:
        return p / (R_spec*rho)
    elif R == None:
        return p / (rho*T)
    return

def wetAirDens(p=None, T=None, q=None):
    """
    From R. S. Davis, Equation for the Determination of the Density of Moist Air (1981/91).
    Available at http://www.nist.gov/calibrations/upload/metv29i1p67-2.pdf
    """
    aux=constants()
    R_spec=aux.R_spec
    R_dry=R_spec['dry_air']
    R_h2o=R_spec['h2o']
    rho_wet=(p/(R_dry*T)) * (1. - q*(1. - R_dry/R_h2o))
    return rho_wet

temp,e,p,eps=[1]*4
virt_temp=temp/(1. -(e/p)*(1.-eps))

