import os
import shutil
import sys
from logging import getLogger
from typing import Dict

import pandas as pd

logger = getLogger(__name__)


def is_powergadget_available():
    try:
        IntelPowerGadget()
        return True
    except Exception as e:
        logger.debug(
            f"Exception occurred while instantiating IntelPowerGadget : {e}",
            exc_info=True,
        )
        print(e)
        return False


class IntelPowerGadget:
    _osx_exec = "PowerLog"
    _osx_exec_backup = "/Applications/Intel Power Gadget/PowerLog"
    _windows_exec = "PowerLog.exe"
    _linux_exec = "power_gadget"

    def __init__(self, output_dir: str = ".", duration=1, resolution=100):
        self._log_file_path = os.path.join(output_dir, "intel_power_gadget_log.csv")
        self._system = sys.platform.lower()
        self._duration = duration
        self._resolution = resolution
        self._cli = None

        if self._system.startswith("linux"):
            if shutil.which(IntelPowerGadget._linux_exec):
                self._cli = IntelPowerGadget._linux_exec
            else:
                raise Exception(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        elif self._system.startswith("windows"):
            if shutil.which(IntelPowerGadget._windows_exec):
                self._cli = IntelPowerGadget._windows_exec
            else:
                raise Exception(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        elif self._system.startswith("darwin"):
            if shutil.which(IntelPowerGadget._osx_exec):
                self._cli = IntelPowerGadget._osx_exec
            elif shutil.which(IntelPowerGadget._osx_exec_backup):
                self._cli = IntelPowerGadget._osx_exec_backup
            else:
                raise Exception(
                    f"Intel Power Gadget executable not found on {self._system}"
                )
        else:
            raise Exception("Platform not supported by Intel Power Gadget")

    def _log_values(self):
        """
        Logs output from Intel Power Gadget command line to a file
        """
        if self._system.startswith("linux"):
            os.system(
                f"{self._cli} -d {self._duration} -e {self._resolution} > {self._log_file_path}"
            )
        elif self._system.startswith("windows"):
            os.system(
                f"{self._cli} -duration {self._duration} -resolution {self._resolution} -file {self._log_file_path} > NUL 2>&1"
            )
        elif self._system.startswith("darwin"):
            os.system(
                f"'{self._cli}' -duration {self._duration} -resolution {self._resolution} -file {self._log_file_path} > /dev/null"
            )
        return

    def get_cpu_details(self) -> Dict:
        """
        Fetches the CPU Power Details by fetching values from a logged csv file in _log_values function
        :return:
        """
        self._log_values()
        cpu_details = dict()
        try:
            cpu_data = pd.read_csv(self._log_file_path).dropna()
            for col_name in cpu_data.columns:
                if col_name in ["System Time", "Elapsed Time (sec)", "RDTSC"]:
                    continue
                if "Cumulative" in col_name:
                    cpu_details[col_name] = cpu_data[col_name].iloc[-1]
                else:
                    cpu_details[col_name] = cpu_data[col_name].mean()
        except FileNotFoundError:
            logger.debug(
                f"Intel Power Gadget logged file not found at {self._log_file_path}"
            )

        return cpu_details