import numpy as np
import os
import scipy
from io import open
import time
import configparser
from pkg_resources import resource_filename

from ._loader import load_dict_from_pickle


class AbundanceGetter:
    def __init__(self, include_condensation=True):
        config = configparser.ConfigParser()
        config.read(resource_filename(__name__, "data/abundances/properties.cfg"))
        properties = config["DEFAULT"]
        self.min_temperature = float(properties["min_temperature"])
        self.logZs = np.linspace(float(properties["min_logZ"]),
                                 float(properties["max_logZ"]),
                                 int(properties["num_logZ"]))
        self.CO_ratios = eval(properties["CO_ratios"])
        self.included_species = eval(properties["included_species"])

        if include_condensation:
            filename = "with_condensation.npy"
        else:
            filename = "gas_only.npy"

        abundances_path = "data/abundances/{}".format(filename)

        self.log_abundances = np.log(np.load(
            resource_filename(__name__, abundances_path)))

    def get(self, logZ, CO_ratio=0.53, min_abundance=1e-99):
        '''Get an abundance grid at the specified logZ and C/O ratio.  This
        abundance grid can be passed to TransitDepthCalculator, with or without
        modifications.  The end user should not need to call this except in
        rare cases.

        Returns
        -------
        abundances : dict of np.ndarray
            A dictionary mapping species name to a 2D abundance array, specifying
            the number fraction of the species at a certain temperature and
            pressure.'''

        N_Z, N_CO, N_species, N_T, N_P = self.log_abundances.shape
        interp_abund = np.exp(scipy.interpolate.interpn(
            (self.logZs, np.log(self.CO_ratios)),
            self.log_abundances,
            [logZ, np.log(CO_ratio)])[0])
        interp_abund[np.isnan(interp_abund)] = min_abundance
        interp_abund[interp_abund < min_abundance] = min_abundance       
        
        abund_dict = {}
        for i, s in enumerate(self.included_species):
            abund_dict[s] = interp_abund[i]

        return abund_dict

    def is_in_bounds(self, logZ, CO_ratio, T):
        '''Check to see if a certain metallicity, C/O ratio, and temperature
        combination is within the supported bounds'''
        if T <= self.min_temperature:
            return False
        if logZ <= np.min(self.logZs) or logZ >= np.max(self.logZs):
            return False
        if CO_ratio <= np.min(self.CO_ratios) or \
           CO_ratio >= np.max(self.CO_ratios):
            return False
        return True

    @staticmethod
    def from_file(filename):
        '''Reads abundances file in the ExoTransmit format (called "EOS" files
        in ExoTransmit), returning a dictionary mapping species name to an
        abundance array of dimension'''
        line_counter = 0

        species = None
        temperatures = []
        pressures = []
        compositions = []
        abundance_data = dict()

        with open(filename) as f:
            for line in f:
                elements = line.split()
                if line_counter == 0:
                    assert(elements[0] == 'T')
                    assert(elements[1] == 'P')
                    species = elements[2:]
                elif len(elements) > 1:
                    elements = np.array([float(e) for e in elements])
                    temperatures.append(elements[0])
                    pressures.append(elements[1])
                    compositions.append(elements[2:])

                line_counter += 1

        temperatures = np.array(temperatures)
        pressures = np.array(pressures)
        compositions = np.array(compositions)

        N_temperatures = len(np.unique(temperatures))
        N_pressures = len(np.unique(pressures))

        for i in range(len(species)):
            c = compositions[:, i].reshape((N_pressures, N_temperatures)).T
            # This file has decreasing temperatures and pressures; we want
            # increasing temperatures and pressures
            c = c[::-1, ::-1]
            abundance_data[species[i]] = c
        return abundance_data
