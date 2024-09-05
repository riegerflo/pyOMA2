"""
Frequency Domain Decomposition (FDD) Algorithm Module.
Part of the pyOMA2 package.
Authors:
Dag Pasca
Diego Margoni
"""

from __future__ import annotations

import logging
import typing

from pyoma2.algorithms.base import BaseAlgorithm
from pyoma2.algorithms.data.result import EFDDResult, FDDResult
from pyoma2.algorithms.data.run_params import EFDDRunParams, FDDRunParams
from pyoma2.functions import fdd, plot
from pyoma2.support.sel_from_plot import SelFromPlot

logger = logging.getLogger(__name__)


# =============================================================================
# SINGLE SETUP
# =============================================================================
# FREQUENCY DOMAIN DECOMPOSITION
class FDD(BaseAlgorithm[FDDRunParams, FDDResult, typing.Iterable[float]]):
    """
    Frequency Domain Decomposition (FDD) algorithm for operational modal analysis.

    This class implements the FDD algorithm, used to identify modal parameters such as
    natural frequencies, damping ratios, and mode shapes from ambient vibrations. The algorithm
    operates in the frequency domain and is suitable for output-only modal analysis.

    Attributes
    ----------
    RunParamCls : Type[FDDRunParams]
        Class of the run parameters specific to the FDD algorithm.
    ResultCls : Type[FDDResult]
        Class of the results generated by the FDD algorithm.
    data : Iterable[float]
        Input data for the algorithm, typically a time series of vibration measurements.
    """

    RunParamCls = FDDRunParams
    ResultCls = FDDResult

    def run(self) -> FDDResult:
        """
        Executes the FDD algorithm on the input data and computes modal parameters.

        Processes the input time series data to compute the spectral density matrix. It then
        extracts its singular values and vectors, which are crucial for modal parameter identification.

        Returns
        -------
        FDDResult
            An object containing frequency spectrum, spectral density matrix, singular values,
            and vectors as analysis results.
        """
        Y = self.data.T
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        pov = self.run_params.pov
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = fdd.SD_est(Y, Y, self.dt, nxseg, method=method, pov=pov)
        Sval, Svec = fdd.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )

    def mpe(self, sel_freq: typing.List[float], DF: float = 0.1) -> typing.Any:
        """
        Performs Modal Parameter Estimation (MPE) on selected frequencies using FDD results.

        Estimates modal parameters such as natural frequencies and mode shapes from the
        frequencies specified by the user.

        Parameters
        ----------
        sel_freq : List[float]
            List of selected frequencies for modal parameter estimation.
        DF : float, optional
            Frequency resolution for estimation. Default is 0.1.

        Returns
        -------
        None
            The method updates the results in the associated FDDResult object with the estimated
            modal parameters.
        """
        super().mpe(sel_freq=sel_freq, DF=DF)

        self.run_params.sel_freq = sel_freq
        self.run_params.DF = DF
        # Sy = self.result.Sy
        S_val = self.result.S_val
        S_vec = self.result.S_vec
        freq = self.result.freq

        # Get Modal Parameters
        Fn_FDD, Phi_FDD = fdd.FDD_mpe(
            Sval=S_val, Svec=S_vec, freq=freq, sel_freq=sel_freq, DF=DF
        )

        # Save results
        self.result.Fn = Fn_FDD
        self.result.Phi = Phi_FDD

    def mpe_from_plot(
        self, freqlim: typing.Optional[tuple[float, float]] = None, DF: float = 0.1
    ) -> typing.Any:
        """
        Extracts modal parameters interactively from a plot using selected frequencies.

        This method allows for interactive selection of frequencies from a plot, followed by
        MPE at those frequencies.

        Parameters
        ----------
        freqlim : Optional[tuple[float, float]], optional
            Frequency range for the interactive plot. Default is None.
        DF : float, optional
            Frequency resolution for estimation. Default is 0.1.

        Returns
        -------
        None
            Updates the results in the associated FDDResult object with the selected modal parameters.
        """
        super().mpe_from_plot(freqlim=freqlim)

        # Sy = self.result.Sy
        S_val = self.result.S_val
        S_vec = self.result.S_vec
        freq = self.result.freq

        self.run_params.DF = DF

        # chiamare plot interattivo
        SFP = SelFromPlot(algo=self, freqlim=freqlim, plot="FDD")
        sel_freq = SFP.result[0]

        # e poi estrarre risultati
        Fn_FDD, Phi_FDD = fdd.FDD_mpe(
            Sval=S_val, Svec=S_vec, freq=freq, sel_freq=sel_freq, DF=DF
        )

        # Save results
        self.result.Fn = Fn_FDD
        self.result.Phi = Phi_FDD

    def plot_CMIF(
        self,
        freqlim: typing.Optional[tuple[float, float]] = None,
        nSv: typing.Optional[int] = "all",
    ) -> typing.Any:
        """
        Plots the Complex Mode Indication Function (CMIF) for the FDD results.

        CMIF is used to identify modes in the frequency domain data. It plots the singular values
        of the spectral density matrix as a function of frequency.

        Parameters
        ----------
        freqlim : Optional[tuple[float, float]], optional
            Frequency range for the CMIF plot. Default is None.
        nSv : Optional[int], optional
            Number of singular values to include in the plot. Default is 'all'.

        Returns
        -------
        tuple
            A tuple containing the Matplotlib figure and axes objects for the CMIF plot.

        Raises
        ------
        ValueError
            If the algorithm has not been run and no results are available.
        """
        if not self.result:
            raise ValueError("Run algorithm first")
        fig, ax = plot.CMIF_plot(
            S_val=self.result.S_val, freq=self.result.freq, freqlim=freqlim, nSv=nSv
        )
        return fig, ax


# ------------------------------------------------------------------------------
# ENHANCED FREQUENCY DOMAIN DECOMPOSITION EFDD
class EFDD(FDD[EFDDRunParams, EFDDResult, typing.Iterable[float]]):
    """
    Enhanced Frequency Domain Decomposition (EFDD) Algorithm Class.

    This class implements the EFDD algorithm, an enhanced version of the basic FDD method.
    It provides more accurate modal parameters from ambient vibration data.

    Attributes
    ----------
    method : str
        The method used in the analysis. Set to "EFDD" for this class.
    RunParamCls : EFDDRunParams
        Class for the run parameters specific to the EFDD algorithm.
    ResultCls : EFDDResult
        Class for storing results obtained from the EFDD analysis.

    Note
    -----
    Inherits from `FDD` and provides specialized methods and functionalities
    for EFDD-specific analyses.
    """

    method: typing.Literal["EFDD", "FSDD"] = "EFDD"

    RunParamCls = EFDDRunParams
    ResultCls = EFDDResult

    def mpe(
        self,
        sel_freq: typing.List[float],
        DF1: float = 0.1,
        DF2: float = 1.0,
        cm: int = 1,
        MAClim: float = 0.85,
        sppk: int = 3,
        npmax: int = 20,
    ) -> typing.Any:
        """
        Performs Modal Parameter Estimation (MPE) on selected frequencies using EFDD results.

        Estimates modal parameters such as natural frequencies, damping ratios, and mode shapes
        from the frequencies specified by the user.

        Parameters
        ----------
        sel_freq : List[float]
            List of selected frequencies for modal parameter estimation.
        DF1 : float, optional
            Frequency resolution for the first stage of EFDD. Default is 0.1.
        DF2 : float, optional
            Frequency resolution for the second stage of EFDD. Default is 1.0.
        cm : int, optional
            Number of closely spaced modes. Default is 1.
        MAClim : float, optional
            Minimum acceptable Modal Assurance Criterion value. Default is 0.85.
        sppk : int, optional
            Number of peaks to skip for the fit. Default is 3.
        npmax : int, optional
            Maximum number of peaks to use in the fit. Default is 20.

        Returns
        -------
        None
            Updates the EFDDResult object with estimated modal parameters.
        """

        # Save run parameters
        self.run_params.sel_freq = sel_freq
        self.run_params.DF1 = DF1
        self.run_params.DF2 = DF2
        self.run_params.cm = cm
        self.run_params.MAClim = MAClim
        self.run_params.sppk = sppk
        self.run_params.npmax = npmax

        # Extract modal results
        Fn_FDD, Xi_FDD, Phi_FDD, forPlot = fdd.EFDD_mpe(
            self.result.Sy,
            self.result.freq,
            self.dt,
            sel_freq,
            self.run_params.method_SD,
            method=self.method,
            DF1=DF1,
            DF2=DF2,
            cm=cm,
            MAClim=MAClim,
            sppk=sppk,
            npmax=npmax,
        )

        # Save results
        self.result.Fn = Fn_FDD.reshape(-1)
        self.result.Xi = Xi_FDD.reshape(-1)
        self.result.Phi = Phi_FDD
        self.result.forPlot = forPlot

    def mpe_from_plot(
        self,
        DF1: float = 0.1,
        DF2: float = 1.0,
        cm: int = 1,
        MAClim: float = 0.85,
        sppk: int = 3,
        npmax: int = 20,
        freqlim: typing.Optional[tuple[float, float]] = None,
    ) -> typing.Any:
        """
        Performs Interactive Modal Parameter Estimation using plots in EFDD analysis.

        Allows interactive selection of frequencies from a plot for modal parameter estimation.
        The method enhances user interaction and accuracy in selecting the frequencies for analysis.

        Parameters
        ----------
        DF1 : float, optional
            Frequency resolution for the first stage of EFDD. Default is 0.1.
        DF2 : float, optional
            Frequency resolution for the second stage of EFDD. Default is 1.0.
        cm : int, optional
            Number of clusters for mode separation. Default is 1.
        MAClim : float, optional
            Minimum acceptable MAC value. Default is 0.85.
        sppk : int, optional
            Number of spectral peaks to consider. Default is 3.
        npmax : int, optional
            Maximum number of peaks. Default is 20.
        freqlim : Optional[tuple[float, float]], optional
            Frequency limit for interactive plot. Default is None.

        Returns
        -------
        None
            Updates the EFDDResult object with modal parameters selected from the plot.
        """

        # Save run parameters
        self.run_params.DF1 = DF1
        self.run_params.DF2 = DF2
        self.run_params.cm = cm
        self.run_params.MAClim = MAClim
        self.run_params.sppk = sppk
        self.run_params.npmax = npmax

        # chiamare plot interattivo
        SFP = SelFromPlot(algo=self, freqlim=freqlim, plot="FDD")
        sel_freq = SFP.result[0]

        # e poi estrarre risultati
        Fn_FDD, Xi_FDD, Phi_FDD, forPlot = fdd.EFDD_mpe(
            self.result.Sy,
            self.result.freq,
            self.dt,
            sel_freq,
            self.run_params.method_SD,
            method=self.method,
            DF1=DF1,
            DF2=DF2,
            cm=cm,
            MAClim=MAClim,
            sppk=sppk,
            npmax=npmax,
        )
        # Save results
        self.result.Fn = Fn_FDD.reshape(-1)
        self.result.Xi = Xi_FDD.reshape(-1)
        self.result.Phi = Phi_FDD
        self.result.forPlot = forPlot

    def plot_EFDDfit(
        self, freqlim: typing.Optional[tuple[float, float]] = None, *args, **kwargs
    ) -> typing.Any:
        """
        Plots Frequency domain Identification (FIT) results for EFDD analysis.

        Generates a FIT plot to visualize the quality and accuracy of modal identification in EFDD.

        Parameters
        ----------
        freqlim : Optional[tuple[float, float]], optional
            Frequency limit for the FIT plot. Default is None.
        *args, **kwargs
            Additional arguments and keyword arguments for plot customization.

        Returns
        -------
        tuple
            A tuple containing the Matplotlib figure and axes objects for the EFDD FIT plot.

        Raises
        ------
        ValueError
            If the algorithm has not been run and no results are available.
        """

        if not self.result:
            raise ValueError("Run algorithm first")

        fig, ax = plot.EFDD_FIT_plot(
            Fn=self.result.Fn,
            Xi=self.result.Xi,
            PerPlot=self.result.forPlot,
            freqlim=freqlim,
        )
        return fig, ax


# ------------------------------------------------------------------------------
# FREQUENCY SPATIAL DOMAIN DECOMPOSITION FSDD
class FSDD(EFDD):
    """
    Frequency-Spatial Domain Decomposition (FSDD) Algorithm Class.

    This class provides the implementation of the Frequency-Spatial Domain Decomposition (FSDD)
    algorithm, a variant of the Enhanced Frequency Domain Decomposition (EFDD) method.
    The FSDD approach extends the capabilities of EFDD enhancing the accuracy of modal parameter
    estimation in operational modal analysis.

    Attributes
    ----------
    method : str
        The method used in the analysis. Set to "FSDD" for this class.
    RunParamCls : Type[EFDDRunParams]
        Class for specifying run parameters unique to the FSDD algorithm.
    ResultCls : Type[EFDDResult]
        Class for storing results obtained from the FSDD analysis.

    Methods
    -------
    Inherits all methods from the EFDD class, with modifications for the FSDD approach.

    Note
    -----
    Inherits functionalities from the EFDD class while focusing on the unique
    aspects of the FSDD approach.
    """

    method: str = "FSDD"


# =============================================================================
# MULTI SETUP
# =============================================================================
# FREQUENCY DOMAIN DECOMPOSITION
class FDD_MS(FDD[FDDRunParams, FDDResult, typing.Iterable[dict]]):
    """
    Frequency Domain Decomposition (FDD) Algorithm for Multi-Setup Analysis.

    This class extends the standard FDD algorithm to handle data from multiple experimental setups.
    It's designed to merge and analyze data from different configurations.

    Attributes
    ----------
    RunParamCls : Type[FDDRunParams]
        Defines the run parameters specific to the FDD algorithm for multi-setup analysis.
    ResultCls : Type[FDDResult]
        Represents the class for storing results obtained from multi-setup FDD analysis.
    data : Iterable[dict]
        The input data for the algorithm, typically a collection of vibration measurements
        from multiple setups.

    Note
    -----
    Inherits the functionality from the standard FDD algorithm class, modifying it
    for application with multiple experimental setups.
    """

    RunParamCls = FDDRunParams
    ResultCls = FDDResult

    def run(self) -> FDDResult:
        """
        Executes the FDD algorithm on multi-setup data for operational modal analysis.

        Processes input data from multiple experimental setups to conduct frequency domain decomposition.
        The method computes spectral density matrices for each setup and then merges them to extract
        singular values and vectors.

        Returns
        -------
        FDDResult
            An object encapsulating the results of the FDD analysis for multi-setup data, including
            frequency spectrum, merged spectral density matrix, and associated singular values and vectors.
        """
        Y = self.data
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        pov = self.run_params.pov
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = fdd.SD_PreGER(Y, self.fs, nxseg=nxseg, method=method, pov=pov)
        Sval, Svec = fdd.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )


# ------------------------------------------------------------------------------
# ENHANCED FREQUENCY DOMAIN DECOMPOSITION EFDD
class EFDD_MS(EFDD[EFDDRunParams, EFDDResult, typing.Iterable[dict]]):
    """
    Enhanced Frequency Domain Decomposition (EFDD) Algorithm for Multi-Setup Analysis.

    This class extends the EFDD algorithm to accommodate operational modal analysis
    across multiple experimental setups.

    Attributes
    ----------
    method : str
        The method employed for multi-setup analysis ("EFDD").
    RunParamCls : EFDDRunParams
        Class for specifying run parameters unique to the EFDD algorithm for multi-setups.
    ResultCls : EFDDResult
        Class for storing results obtained from the multi-setup EFDD analysis.
    data : Iterable[dict]
        The input data, consisting of vibration measurements from multiple setups.

    Note
    -----
    This class adapts the EFDD algorithm's functionality for multiple experimental setups.
    """

    method = "EFDD"
    RunParamCls = EFDDRunParams
    ResultCls = EFDDResult

    def run(self) -> FDDResult:
        """
        Executes the Enhanced Frequency Domain Decomposition (EFDD) algorithm on multi-setup data.

        Processes input data from multiple experimental setups for operational modal analysis using the EFDD
        method. The method computes spectral density matrices for each setup and then merges them to extract
        singular values and vectors.

        Returns
        -------
        EFDDResult
            An object encapsulating the results of the EFDD analysis for multi-setup data, including enhanced
            frequency spectrum, merged spectral density matrices, and associated singular values and vectors.
        """
        Y = self.data
        nxseg = self.run_params.nxseg
        method = self.run_params.method_SD
        pov = self.run_params.pov
        # self.run_params.df = 1 / dt / nxseg

        freq, Sy = fdd.SD_PreGER(Y, self.fs, nxseg=nxseg, method=method, pov=pov)
        Sval, Svec = fdd.SD_svalsvec(Sy)

        # Return results
        return self.ResultCls(
            freq=freq,
            Sy=Sy,
            S_val=Sval,
            S_vec=Svec,
        )
