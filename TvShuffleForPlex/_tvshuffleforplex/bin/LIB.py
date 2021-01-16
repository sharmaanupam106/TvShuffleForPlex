# !/usr/bin/python3

# imports
from datetime import datetime as dt
from datetime import timedelta as td
import time
import sys
import subprocess
import threading
import os
import multiprocessing as mp
import base64
import re
import shutil
import getpass
import string
import copy

# Multiprocessing shared memory manager
from typing import List

MANAGER = mp.Manager()


class Command:
    """
    Command object that is executed.

    :ivar bytes output: STDOUT of the command
    :ivar bytes error: STDERR of the command
    :ivar int status_code: Return Code of the command
    :ivar subprocess.Popen process: The process that is spawned to run the command
    :ivar str cmd: The command being run
    """

    def __init__(self, cmd: str = None):
        self.output: bytes = None
        self.error: bytes = None
        self.status_code: int = None
        self.process: subprocess.Popen = None
        self.cmd = cmd

    def run(self, timeout: int = 60):
        """
        The run function that will spawn a new thread and execute the given command. Thread time out is used to ensure the command exists at some point

        :param int timeout: Timeout value to be used to kill the process if still running. A value of 0 will indicate no timeout
        :return:
        """

        def target():
            """
            Target function that is being opened by the thread

            :return:
            """
            self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            stdin=subprocess.PIPE, shell=True)
            self.output, self.error = self.process.communicate()
            self.status_code = self.process.returncode

        thread = threading.Thread(target=target)
        thread.start()

        if timeout != 0:
            thread.join(timeout)
        else:
            thread.join()

        if thread.is_alive():
            self.process.terminate()
            thread.join()

    def get_done_values(self) -> [str, str, int]:
        """
        Returns the output, error, and status code of the executed command

        :return [str, str, int]: [STDOUT, STDERR, status_code]
        """
        return [self.output.decode(), self.error.decode(), self.status_code]


class File:
    """
    File Object Class, stores attributes about a given file.

    :param str name: Name of the file
    :param str permissions: Permission of the file
    :param int size: Size of the file
    :param str modified_time: Modified time of the file
    :param str path: Path of the file

    :ivar str name: Name of the file
    :ivar oct permissions: Permission's of the file
    :ivar int size: Size of the file
    :ivar float modified_time: Time last modified
    :ivar str path: Full path to the file
    :ivar str extension: Extension of the file
    :ivar bool is_directory: Indicate if the file is a directory
    """

    def __init__(self, name: str = None, permissions: oct = None, size: int = None, modified_time: float = None,
                 path: str = None):
        self.name: str = name
        self.permissions: oct = permissions
        self.size: int = size
        self.modified_time: float = modified_time
        self.path: str = os.path.join(*os.path.split(path)[:len(os.path.split(path))-1])
        filename, file_extension = os.path.splitext(path)
        self.extension: str = file_extension
        self.is_directory: bool = os.path.isdir(path)

    def to_string(self) -> str:
        """
        Return a dict string of all the attributes for this class

        :return: String dict of all attributes
        :rtype: String
        """
        return str(self.__dict__)

    def __str__(self) -> str:
        """
        Same as to_string function

        :return: String dict of all attributes
        :rtype: String
        """
        return str(self.__dict__)

    def get_abs_path(self) -> str:
        """
        Get the absolute path to the file with file name

        :return str: absolute path to the file
        """
        return os.path.join(self.path, self.name)


class Host:
    """
    Host object class, stores attributes about a host. Read from the hosts file.

    :param hostname (str): Hostname of the host
    :param ip (str): IP of the host
    :ivar [str] hostname: List of hostname's
    :ivar [str] ip: List of IP's
    """
    hostname = []
    '''List of hostname's'''
    ip = []
    '''List of IP's'''

    def __init__(self, hostname: [str] = None, ip: [str] = None):

        if hostname is not None:
            self.hostname = hostname
        else:
            self.hostname = []
        if ip is not None:
            self.ip = ip
        else:
            self.ip = []

    def to_string(self) -> str:
        """
        Return the dict representation of this object as a string

        :return: Dict as string
        """
        return str(self.__dict__)

    def __str__(self) -> str:
        """
        Return the dict representation of this object as a string

        :return: Dict as string
        """
        return str(self.__dict__)

    def add_hostname(self, hostname: str = None):
        """
        Add a hostname to the host.

        :param str hostname: Hostname of the host
        :return:
        """
        if hostname is None:
            return None
        else:
            self.hostname.append(hostname)

    def add_ip(self, ip: str = None):
        """
        Add a ip to the host

        :param str ip: IP of the host
        :return:
        """
        if ip is None:
            return None
        else:
            self.ip.append(ip)


class LIB:
    """
    Lib Object Class. Contains functions that are most commonly used in a project for simplicity of use.
    Most commonly used for logging, config file reading, and system command execution

    :param str home: Working directory of the project. (bin directory contains this file)
    :param str cfg: Path to the config file
    :param str out_log: Name of the output log file
    :param str err_log: Name of the error log file

    :ivar [str] PUNCTUATION:
    :ivar str HOME:
    :ivar str LOG:
    :ivar str CFG_IN_USE:
    :ivar dict CFG:
    :ivar [str] ARGS:
    :ivar [process] PROCESSLIST:
    :ivar str OS:
    :ivar str OUT_LOG:
    :ivar str ERR_LOG:
    :ivar [Host] HOSTSLIST:
    :ivar bool LOGGING:
    :ivar str VERSION:
    :ivar File LASTFILEROTATE:
    """

    PUNCTUATION: [str] = ['"', '\'', '*']
    '''Punctuation list used in sanitize_string '''
    HOME: str = None
    '''Home path for the project'''
    LOGS_PATH: str = None
    '''Log path for the project'''
    CFGS_PATH: str = None
    '''Config files path'''
    CFG_IN_USE: str = None
    '''Config file name being used'''
    CFG: dict = MANAGER.dict()
    '''Config dictionary used to hold config keys and values'''
    ARGS: [str] = None
    '''System arguments passed to the program'''
    OS: str = None
    '''OS current program is being run on'''
    OUT_LOG: str = None
    '''Out log file name'''
    ERR_LOG: str = None
    '''Error log file name'''
    HOSTSLIST: [Host] = None
    '''Host's lists'''
    LOGGING: bool = True
    '''Logging is enabled'''
    VERSION: str = "1.0.1"
    '''Version of this LIB file'''
    LASTFILEROTATE: File = None
    '''Last log file that was rotated'''

    def __init__(self, home: str = None, cfg: str = None, out_log: str = None, err_log: str = None):
        if home is None:
            home = os.getcwd()
            parts = os.path.split(home)
            if parts[len(parts) - 1] == "bin":
                tmp_list = parts[:len(parts) - 1]
                home = os.path.join(*tmp_list)

        self.HOME = home
        # Check and/or create the project structure
        if not self.path_exists(self.HOME):
            if not self.make_path(self.HOME):
                return

        # Set the logs directory
        self.LOGS_PATH = os.path.join(self.HOME, "logs")
        if not self.path_exists(self.LOGS_PATH):
            if not self.make_path(self.LOGS_PATH):
                return

        # Get and store the sys arguments
        self.ARGS = sys.argv

        # Load the config file
        self.CFGS_PATH = os.path.join(self.HOME, 'config')
        if cfg is None:
            cfg = self.get_args_value('-cfg', os.path.join(self.CFGS_PATH, 'config.cfg'))

        tmp_cfg = self.read_config(cfg)
        if tmp_cfg is None:
            self.CFG = MANAGER.dict()
        else:
            for key in tmp_cfg:
                self.CFG[key] = tmp_cfg[key]

        # Set the output log file and error log file
        if out_log is None:
            self.OUT_LOG = self.get_config_value("outputlog", "output.log")
        else:
            self.OUT_LOG = out_log
        if err_log is None:
            self.ERR_LOG = self.get_config_value("errorlog", "error.log")
        else:
            self.ERR_LOG = err_log

        try:
            value = self.get_config_value("logging", True)
            if value == "false":
                self.LOGGING = False
        except Exception as e:
            self.write_error("ERROR\n###########\n{}\n###########\n".format(e))
            self.LOGGING = True

        self.write_log("Making lib instance: '{}'".format(home))
        self.write_log("ARGS: {}".format(self.ARGS))
        self.write_log("Using Config file: '{}'".format(cfg))
        self.write_log("Config: '{}'".format(self.CFG))

        # Set the current running OS
        self.OS = self.clean_string(str(sys.platform).lower())
        self.write_log("Using OS: {}".format(self.OS))

    """
    CONFIG
    """

    def read_config(self, in_cfg_file: str = None) -> [dict, None]:
        """
        Read the config file and generate a key value dict

        :param str in_cfg_file: Config file name
        :return {str, Any}: key value dict of file content
        """
        self.CFG_IN_USE = in_cfg_file
        tmp_cfg = {}
        data = self.read_file(in_cfg_file)
        if data in [-1, None]:
            return None
        for line in data:
            line = self.clean_string(line)
            if len(line) > 3:
                if line[0] == "#":
                    continue
                dic = line.split("=")
                if len(dic) > 2:
                    continue
                key = self.clean_string(dic[0].lower())
                value = self.clean_string(dic[1])

                if value[0] == '"':
                    value = self.clean_string(value.replace('"', ""))
                elif value[0] == '[':
                    tmp_list = value.replace("[", "").replace("]", "").split(",")
                    tmp_list = list(map(self.sanitize_string, tmp_list))
                    value = tmp_list
                else:
                    try:
                        value = int(value)
                    except Exception as e:
                        self.write_error("ERROR\n###########\n{}\n###########\n".format(e))
                        value = self.clean_string(value).lower()

                tmp_cfg[key] = value
        return tmp_cfg

    def get_config_value(self, key: str, default=None):
        """
        Get he config value for a given key

        :param str key: Key for the config value
        :param Any default: Default value to return if key is not found
        :return: Found value, default value, or None
        """
        try:
            data = self.CFG[key.lower()]
        except Exception as e:
            self.write_error("ERROR\n###########\n{}\n###########\n".format(e))
            data = default
        return data

    def reload_config(self):
        """
        Reload the config file into the CFG dict

        :return:
        """
        self.write_log("Reloading config '{}' from {}".format(self.CFG_IN_USE, os.getpid()))
        tmp_cfg = self.read_config(self.CFG_IN_USE)
        if tmp_cfg is not None:
            self.CFG.clear()
            for key in tmp_cfg:
                self.CFG[key] = tmp_cfg[key]
            self.write_log("New config values '{}'".format(self.CFG))
            self.write_log("Reloading done")

    def end(self):
        """
        Terminate this LIB instance

        :return:
        """
        self.write_log("Terminating LIB instance")
        del self

    """
    SYSTEM ARGUMENTS
    """

    def get_args(self) -> List[str]:
        """
        Get the arguments passed to the script

        :return [str]: list of strings
        """
        return self.ARGS

    def get_args_value(self, key: str = None, default=None):
        """
        Get and argument value given the key. (the value in this case is the next argument, {key_index+1})

        :param str key: String key to the value of.
        :param Any default: Default value to be returned is none is found
        :return Any: None or the value (argument index +1) of the given key
        """
        args = self.ARGS
        try:
            idx = args.index(key)
            value = args[idx + 1]
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            value = default
        return value

    def in_args(self, key: str = None) -> bool:
        """
        Test if the key is part of the arguments

        :param str key: Key to search for in arguments
        :return bool: True if key is present, False otherwise.
        """
        if key is None:
            return False
        args = self.ARGS
        if key in args:
            return True
        return False

    """
    IO
    """

    def read_string(self, message: str = "Enter a string: ") -> [str, None]:
        """
        Read a string from the user

        :param srt message: Message to be displayed when asking for input
        :return [str, None]: String value entered by the user, or None for input error
        """
        try:
            input_string = input(message)
            self.write_log("{} {}".format(message, input_string))
            return input_string
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None

    def read_password(self, message: str = "Enter a password: ") -> [str, None]:
        """
        Read a password from the user (not displayed in text)

        :param str message: Message to be displayed when asking for input
        :return [str, None]: String value entered by the user, or None for input error
        """
        try:
            input_string = getpass.getpass(prompt=message)
            return input_string
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None

    def read_int(self, message: str = "Enter an integer: ") -> [int, None]:
        """
        Read an integer from the user

        :param str message: Message to be displayed when asking for input
        :return [int, None]: Integer value entered by the user, or None for input error
        """
        try:
            value = self.read_string(message)
            self.write_log("{} {}".format(message, value))
            if value == -1:
                return None
            input_int = int(value)
            return input_int
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            self.write_log("Invalid int")
            return None

    def read_char(self, message: str = "Enter a character: ") -> [str, None]:
        """
        Read a char from the user

        :param str message: Message to be displayed when asking for input
        :return [str, None]: String value entered by the user, or None for input error
        """
        try:
            input_string = self.read_string(message)
            self.write_log("{} {}".format(message, input_string))
            if len(input_string) != 1:
                return None
            return input_string
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            self.write_log("Invalid char")
            return None

    def read_ip(self, message: str = "Entry an IPv4: ") -> [str, None]:
        """
        Read an IP from the user

        :param str message: Message to be displayed when asking for input
        :return [str, None]: String value of the IP entered by the user, or None for input error
        """
        value = None
        try:
            value = self.read_string(message=message)
            if self.is_ip(value) is False:
                return None
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
        self.write_log("{} {}".format(message, value))
        return value

    def read_file(self, in_file_name: str = None) -> [[str], None]:
        """
        Read given filename

        :param srt in_file_name: Name of the file to be read
        :return [[str], None]: List of strings for each line, or None for error
        """
        self.write_log("Reading file {}".format(in_file_name))
        try:
            in_file = open(in_file_name, "r+", errors='ignore')
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        try:
            data = []
            for line in in_file:
                data.append(line)
            in_file.close()
            return data
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            in_file.close()
            return None

    def write_log(self, in_string: str = None, mode: str = "a+") -> None:
        """
        Write a given string to the log file

        :param str in_string: String to be written to the log file
        :param str mode: The mode in which the log file is opened.
        :return None: None if there is an error
        """
        if in_string is None:
            return None
        if self.OUT_LOG is None:
            return
        try:
            out = open(os.path.join(self.LOGS_PATH, self.OUT_LOG), mode)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        msg = "{} ~ {}\n".format(self.get_now(), in_string)
        try:
            con = self.get_config_value("console", 0)
            if con in [1, 4]:
                print(msg)
            if self.LOGGING:
                out.write(msg)
            out.close()
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return

    def write_error(self, in_string: str = None, mode: str = "a+") -> None:
        """
        Write an string the error file.

        :param str in_string: String to be written to the error file
        :param srt mode: The mode in which hte lof file is opened
        :return None: None if there is an error
        """
        if in_string is None:
            return None
        if self.ERR_LOG is None:
            return
        try:
            out = open(os.path.join(self.LOGS_PATH, self.ERR_LOG), mode)
        except:
            return None
        msg = "{} ~ {}\n".format(self.get_now(), in_string)
        try:
            con = self.get_config_value("console", 0)
            if con in [2, 4]:
                print(msg)
            if self.LOGGING:
                out.write(msg)
            out.close()
        except:
            return None
        return

    def write_file(self, file_name: str = None, in_string: str = None, mode: str = "a+",
                   time_stamp: bool = False) -> None:
        """
        Write a given string to a given file

        :param str file_name: Name of the file where the string is to be written
        :param str in_string: String that is written to the file
        :param srt mode: Mode in which the file is to be written in
        :param bool time_stamp: Boolean a time stamp should be included
        :return None: None if an error is to occur
        """
        if file_name is None:
            return None
        if in_string is None:
            return None
        try:
            out = open(file_name, mode)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        if time_stamp:
            if in_string[len(in_string) - 1] == "\n":
                msg = "{} ~ {}".format(self.get_now(), in_string)
            else:
                msg = "{} ~ {}\n".format(self.get_now(), in_string)
        else:
            if in_string[len(in_string) - 1] == "\n":
                msg = "{}".format(in_string)
            else:
                msg = "{}\n".format(in_string)
        try:
            out.write(msg)
            con = self.get_config_value("console", 0)
            if con in [3, 4]:
                print(msg)
            out.close()
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            out.close()
            return None
        return

    def directory_listing(self, directory: str = None, recursive: bool = True) -> [[File], None]:
        """
        List the contents of a directory

        :param srt directory: Path to the directory
        :param bool recursive: Bool if the contents should be listed recursively
        :return [[File], None]: List of File objects, or None if error
        """
        if not self.path_exists(directory):
            self.write_log("No such path {}".format(directory))
            return None
        self.write_log("Listing directory {} Recursive = {}".format(directory, recursive))
        files = []
        if recursive:
            for root, dirs, dire_files in os.walk(directory, topdown=False):
                for name in dire_files:
                    try:
                        stats = os.stat(os.path.join(root, name))
                        files.append(File(name=name, path=os.path.join(root, name), size=stats.st_size,
                                          modified_time=stats.st_mtime, permissions=oct(stats.st_mode)))
                    except Exception as e:
                        self.write_error("Error:\n####\n{}\n####\n".format(e))
                        pass
                for name in dirs:
                    try:
                        stats = os.stat(os.path.join(root, name))
                        files.append(File(name=name, path=os.path.join(root, name), size=stats.st_size,
                                          modified_time=stats.st_mtime, permissions=oct(stats.st_mode)))
                    except Exception as e:
                        self.write_error("Error:\n####\n{}\n####\n".format(e))
                        pass
        if not recursive:
            for f in os.listdir(directory):
                try:
                    stats = os.stat(os.path.join(directory, f))
                    files.append(
                        File(name=f, path=os.path.join(directory, f), size=stats.st_size, modified_time=stats.st_mtime,
                             permissions=oct(stats.st_mode)))
                except Exception as e:
                    self.write_error("Error:\n####\n{}\n####\n".format(e))
                    pass
        return files

    def path_exists(self, path: str = None) -> bool:
        """
        Check if a given path exists

        :param str path: String of the full path to test
        :return bool: Bool of the test
        """
        self.write_log("Check path: {}".format(path))
        try:
            value = os.path.exists(path)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            value = False
        self.write_log("Path exists result: {}".format(value))
        return value

    def make_file(self, in_file: str = None, create: bool = False) -> [File, None]:
        """
        Create a new File Object

        :param srt in_file: Full path and name to file
        :param bool create: Create the file on the system
        :return [File, None]: File Object of None if error
        """
        if in_file is None:
            self.write_log("Need file path")
            return None
        if not self.file_exists(in_file):
            self.write_log("File does not exists")
            if create:
                self.write_log("Creating new file {}".format(in_file))
                try:
                    file = open(in_file, "w+")
                    file.close()
                    self.write_log("Creating new file {}".format(in_file))
                except Exception as e:
                    self.write_error("Error creating file: {}".format(e))
                    return None
        name = os.path.basename(in_file)
        path = os.path.abspath(in_file)
        stats = os.stat(in_file)
        return File(name=name, path=path, size=stats.st_size, modified_time=stats.st_mtime,
                    permissions=oct(stats.st_mode))

    def remove_file(self, in_file: [File, str] = None) -> bool:
        """
        Remove a file from the system

        :param [File, str] in_file: File object of full path to the file
        :return bool: Status of the removal
        """
        if in_file is None:
            self.write_log("Need a file path or name")
            return False
        file_name = None
        if type(in_file) is File:
            file_name = in_file.get_abs_path()
        elif type(in_file) is str:
            file_name = in_file

        if file_name is None:
            self.write_error("Error file")
            return False
        self.write_log("Removing file {}".format(file_name))
        try:
            os.remove(file_name)
            if self.file_exists(in_file=file_name):
                self.write_log("Could not remove file")
                return False
            else:
                self.write_log("File removed")
                return True
        except Exception as e:
            self.write_error("Error removing file: {}".format(e))
            return False

    def file_exists(self, in_file: [File, str] = None) -> bool:
        """
        Check if the file exists

        :param [File, str] in_file: File object of full path to the file
        :return bool: Status of file check
        """
        if in_file is None:
            self.write_log("Need file path")
            return False
        try:
            if type(in_file) is File:
                in_file = in_file.path
            value = os.path.isfile(in_file)
            if value:
                return True
            else:
                return False
        except Exception as e:
            self.write_error("Error: {}".format(e))
            return False

    def file_rotation(self, in_file: [File, str] = None, force_rotation: bool = False):
        """
        Check and rotate a given file

        :param [File, str] in_file: File object of full path to the file
        :param bool force_rotation: Ignore the size check and rotate the file anyways
        :return [bool, None]: Status of the rotation or None if error
        """
        if type(in_file) is not File:
            if type(in_file) is str:
                if self.file_exists(in_file):
                    working_file = self.make_file(in_file)
                else:
                    log_message = "File does not exist '{}'".format(in_file)
                    self.write_log(log_message)
                    return None
            else:
                log_message = "Unknown file type '{}'".format(in_file)
                self.write_log(log_message)
                return None
        else:
            working_file = in_file

        if working_file is None:
            log_message = "File is none"
            self.write_log(log_message)
            return None

        self.write_log("File Rotation started: '{}'".format(working_file.name))

        try:
            _sizelimit = float(self.get_config_value("LogRotationFileSize", 10))
            _filelimit = float(self.get_config_value("LogRotationFileLimit", 1))
        except Exception as e:
            self.write_error(f"Error {e}")
            log_message = "Unknown config value"
            self.write_log(log_message)
            _sizelimit = 10
            _filelimit = 1

        # Get all the files at this path
        dir_files = self.directory_listing(working_file.path, False)

        # If force_rotation is set, this is ignored
        if not force_rotation:
            # Ensure this file has a size grater than whats defined
            for dir_file in dir_files:
                if dir_file.name == working_file.name:
                    if float(dir_file.size) < float(((_sizelimit * 1000) * 1024)):
                        self.write_log("Size not at limit: '{}'".format(working_file.name))
                        return False
        else:
            self.write_log("Force Rotation")

        tmp_list = []
        # Remove files that are not an iteration of the file in question
        for dir_file in dir_files:
            if working_file.name in dir_file.name:
                tmp_list.append(dir_file)
        dir_files = tmp_list

        while int(len(dir_files)) > int(_filelimit):
            # Find the oldest files
            oldest = None
            for dir_file in dir_files:
                if dir_file.name != working_file.name:
                    if oldest is None:
                        oldest = dir_file
                    else:
                        if oldest.modified_time > dir_file.modified_time:
                            oldest = dir_file
            log_message = "Removing oldest file '{}'".format(oldest.name)
            self.write_log(log_message)
            if self.remove_file(oldest):
                dir_files.remove(oldest)
            else:
                self.write_log(f"Unable to remove {oldest}")

        # Rotate and make new files
        self.LASTFILEROTATE = working_file
        new_file = copy.deepcopy(working_file)
        new_file.name = "{}.{}".format(new_file.name, self.get_now().replace(" ", "-").replace(":", "-").split(".")[0])
        if self.move_file(working_file, new_file):
            self.write_log(f"Moved {working_file.name} to {new_file.name}")
        else:
            self.write_log(f"Error moving file")
            return False
        # Create an empty file to replace the old one with
        if self.make_file(working_file.get_abs_path(), create=True):
            self.write_log(f"New file {working_file.name} created")
        else:
            self.write_log(f"Error creating {working_file.name}")
            return False
        return True

    def make_path(self, path: str = None) -> bool:
        """
        Make the given absolute path

        :param str path: Absolute path that should be created
        :return bool: True if the path is created, False otherwise
        """
        if path is None:
            self.write_log("Need a path")
            return False
        self.write_log("Creating path: {}".format(path))
        try:
            if not self.path_exists(path):
                os.makedirs(path)
                self.write_log("Result: {}".format(True))
                return True
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return False
        return False

    def remove_path(self, path: str = None, force: bool = False) -> bool:
        """
        Remove the given absolute path

        :param str path: Absolute path that needs to be removed
        :param bool force: Force the removal of the path (if there is content in the directory)
        :return bool: True if the path was removed, False otherwise.
        """
        if path is None:
            self.write_log("Need a path")
            return False
        self.write_log("Removing path: {}".format(path))
        try:
            if self.path_exists(path):
                if force:
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
                self.write_log("Remove path result: {}".format(True))
                return True
            else:
                self.write_log("No such path: {}".format(True))
                return False
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return False

    def move_file(self, source: [File, str] = None, destination: [File, str] = None) -> bool:
        """
        Move the given source file to the given destination

        :param [File, str] source: Source File that needs to be moved
        :param [File, str] destination: Destination File where to move (must be a directory)
        :return bool: Status of the move
        """
        if (source is None) or (destination is None):
            return False

        if type(source) not in [File, str]:
            self.write_log(f"Invalid source file")
            return False
        if type(destination) not in [File, str]:
            self.write_log(f"Invalid destination file")
            return False

        if type(source) == str:
            source = self.make_file(in_file=source, create=False)
            if source is None:
                self.write_log(f"Error making source file")

        if type(destination) == str:
            destination = self.make_file(in_file=destination, create=False)
            if destination is None:
                self.write_log(f"Error making destination file")

        if not self.path_exists(source.path):
            self.write_log(f"Source path does not exist")
            return False

        if not self.path_exists(destination.path):
            self.write_log(f"Destination path does not exist")
            return False

        if not source.is_directory and destination.is_directory:
            tmp_source = source.get_abs_path()
            tmp_destination = os.path.join(destination.get_abs_path(), source.name)
            self.write_log("MOVE {} TO {}".format(tmp_source, tmp_destination))
            try:
                shutil.move(tmp_source, tmp_destination)
            except Exception as e:
                self.write_error("Error:\n####\n{}\n####\n".format(e))
                return False
            return True
        elif not source.is_directory and not destination.is_directory:
            tmp_source = source.get_abs_path()
            tmp_destination = destination.get_abs_path()
            self.write_log("MOVE {} TO {}".format(tmp_source, tmp_destination))
            try:
                shutil.move(tmp_source, tmp_destination)
            except Exception as e:
                self.write_error("Error:\n####\n{}\n####\n".format(e))
                return False
            return True
        elif source.is_directory and destination.is_directory:
            self.write_log(f"Source and destination are directories")
            return False
        elif source.is_directory and not destination.is_directory:
            self.write_log(f"Source is a directories")
            return False
        else:
            self.write_log(f"Unknown source and destination types")
            return False

    def copy_file(self, source: [File, str] = None, destination: [File, str] = None) -> bool:
        """
        Copy the given source file to the given destination

        :param [File, str] source: Source File that needs to be copied
        :param [File, str] destination: Destination File where to copy (must be a directory)
        :return bool: Status of the copy
        """
        if (source is None) or (destination is None):
            return False

        if type(source) not in [File, str]:
            self.write_log(f"Invalid source file")
            return False
        if type(destination) not in [File, str]:
            self.write_log(f"Invalid destination file")
            return False

        if type(source) == str:
            source = self.make_file(in_file=source, create=False)
            if source is None:
                self.write_log(f"Error making source file")

        if type(destination) == str:
            destination = self.make_file(in_file=destination, create=False)
            if destination is None:
                self.write_log(f"Error making destination file")

        if not self.path_exists(source.path):
            self.write_log(f"Source path does not exist")
            return False

        if not self.path_exists(destination.path):
            self.write_log(f"Destination path does not exist")
            return False

        if not source.is_directory and destination.is_directory:
            tmp_source = source.get_abs_path()
            tmp_destination = os.path.join(destination.get_abs_path(), source.name)
            self.write_log("COPY {} TO {}".format(tmp_source, tmp_destination))
            try:
                shutil.copy2(tmp_source, tmp_destination)
            except Exception as e:
                self.write_error("Error:\n####\n{}\n####\n".format(e))
                return False
            return True
        elif not source.is_directory and not destination.is_directory:
            tmp_source = source.get_abs_path()
            tmp_destination = destination.get_abs_path()
            self.write_log("COPY {} TO {}".format(tmp_source, tmp_destination))
            try:
                shutil.copy2(tmp_source, tmp_destination)
            except Exception as e:
                self.write_error("Error:\n####\n{}\n####\n".format(e))
                return False
            return True
        elif source.is_directory and destination.is_directory:
            self.write_log(f"Source and destination are directories")
            return False
        elif source.is_directory and not destination.is_directory:
            self.write_log(f"Source is a directories")
            return False
        else:
            self.write_log(f"Unknown source and destination types")
            return False

    def run_os_cmd(self, cmd: str = None) -> [[str, str, int], [None, None, int]]:
        """
        Run a given OS command

        :param str cmd: OS command to be run
        :return [[str, str , str], None]: List of [command.output, command.error, command.return_code] or None if error

        :ivar Command command: The command object that runs the given command
        """

        if cmd is None:
            return [None, None, 127]

        tout = self.get_config_value("CmdTimeout", 60)
        if type(tout) is not int:
            tout: int = 60

        self.write_log("Running cmd: '{}'".format(cmd))
        command = Command(cmd)
        command.run(tout)

        return command.get_done_values()

    """
    TIME BASE
    """

    @staticmethod
    def get_now() -> str:
        """
        String representation of datetime.now()

        :return:
        """
        return str(dt.now())

    @staticmethod
    def timestamp_to_date(stamp: float = None) -> [str, None]:
        """
        Convert time stamp to human readable date

        :param str stamp: Timestamp that needs to be converted
        :return [str, None]: String of the human readable format, None if error
        """
        if stamp is not None:
            return str(dt.utcfromtimestamp(stamp)).split(".")[0]
        return None

    def sleep(self, duration: int = 0):
        """
        Program sleep for the given duration

        :param int duration: Duration for the sleep to take place
        :return:
        """
        self.write_log("Sleeping for {}".format(duration))
        try:
            time.sleep(duration)
        except Exception as e:
            tmp_string = "Sleep error: '{}'".format(e)
            self.write_error(tmp_string)
        return

    def time_delta(self, delta: int = None, measure: str = None) -> [str, None]:
        """
        Return string representation of time after shifting delta from now()

        :param int delta: Duration to delta the time
        :param str measure: The measure in which to do the delta
        :return [str, None]: String representation of the delta time

        :ivar [str] _measure: ['days', 'weeks', 'hours', 'minutes', 'seconds']
        """
        if (delta is None) or (measure is None):
            self.write_error("Invalid delta or measure")
            return None
        _measure = ['days', 'weeks', 'hours', 'minutes', 'seconds']
        if measure not in _measure:
            self.write_error("Invalid measure {}".format(measure))
            self.write_error("OPTIONS: {}".format(_measure))
            return None
        if type(delta) is not int:
            self.write_error("Delta must be an integer")
            return None
        self.write_log("Time delta {} {}".format(delta, measure))
        now = dt.now()
        future = False
        if delta > 0:
            future = True
        delta = abs(delta)
        measure = measure.lower()
        return_value = None
        if future:
            if measure == "seconds":
                return_value = str(now + td(seconds=delta)).split(".")[0]
            if measure == "minutes":
                return_value = str(now + td(minutes=delta)).split(".")[0]
            if measure == "hours":
                return_value = str(now + td(hours=delta)).split(".")[0]
            if measure == "days":
                return_value = str(now + td(days=delta)).split(".")[0]
            if measure == "weeks":
                return_value = str(now + td(weeks=delta)).split(".")[0]
        if not future:
            if measure == "seconds":
                return_value = str(now - td(seconds=delta)).split(".")[0]
            if measure == "minutes":
                return_value = str(now - td(minutes=delta)).split(".")[0]
            if measure == "hours":
                return_value = str(now - td(hours=delta)).split(".")[0]
            if measure == "days":
                return_value = str(now - td(days=delta)).split(".")[0]
            if measure == "weeks":
                return_value = str(now - td(weeks=delta)).split(".")[0]
        return return_value

    '''
    HOSTS FUNCTIONS
    '''

    def remove_comments_from_hosts_file_entry_list(self, hostsfile: [str] = None) -> [[str], None]:
        """
        Remove comments from hosts files line entries

        :param [str] hostsfile: List of lines from the hosts file
        :return [[srt], None]: Sanitized list of lines
        """
        self.write_log("Cleaning hosts file")
        if hostsfile is None:
            return None
        new_host = []
        # for each line the hosts file
        for line in hostsfile:
            # string any leading and trailing spaces, and the new line at the end
            line = line.strip().replace("\n", "")
            if line != "":
                # if the line starts with "#" or "*" ignore it
                if (line[0] != "#") and (line[0] != "*"):
                    # if the line has "#" in is parse out all the data after it
                    if "#" in line:
                        tmp = line[:line.index("#")]
                        new_host.append(tmp.replace("\t", " "))
                    else:
                        new_host.append(line.replace("\t", " "))
        return new_host

    def generate_hosts_list(self, in_hostsfile: [str] = None) -> [[Host], None]:
        """
        Generate a list of hosts from hosts file

        :param [str] in_hostsfile: List of lines from the hosts file
        :return:
        """
        tmp_string = "Generating hosts list"
        self.write_log(tmp_string)
        # remove comments from file
        hosts = self.remove_comments_from_hosts_file_entry_list(in_hostsfile)
        my_hosts = []
        for h in hosts:
            hostname = []
            tmp_list = h.split(" ")
            if len(tmp_list) > 1:
                ip = tmp_list[0]
                for i in range(len(tmp_list)):
                    if (i != 0) and (tmp_list[i] != ""):
                        # for each hostname assigned to ip
                        hostname.append(tmp_list[i].strip().replace("\n", "").replace("\r", ""))
                my_hosts.append(Host(hostname, ip))
        tmp_string = "Generation Done. Got %s hosts" % (len(my_hosts))
        self.write_log(tmp_string)
        return my_hosts

    def get_hosts(self, hosts_file: str = None) -> [[Host], None]:
        """
        Gets a list of Hosts object from a given hosts file

        :param str hosts_file: Path to the hosts file
        :return [[Host], None]: List of Host's or None if error
        """
        if hosts_file is None:
            if self.OS.lower() in ['linux']:
                hosts_file = os.path.join('/', 'etc', 'hosts')
            elif self.OS.lower() in ['windows', 'win', 'win32', 'win64']:
                hosts_file = os.path.join('C:', 'Windows', 'System32', 'drivers', 'etc', 'hosts')
        hostsfile = self.read_file(hosts_file)
        if hostsfile is None:
            return None
        self.HOSTSLIST = self.generate_hosts_list(hostsfile)
        return self.HOSTSLIST

    @staticmethod
    def name_in_hostnames(host: Host = None, name: str = None) -> bool:
        """
        Search for a given name in the given Host.

        :param Host host: Host object in which to search for the name
        :param str name: Name to search for in the Host object
        :return bool: True if the name is found, False otherwise
        """
        if (host is None) or (name is None):
            return False
        for h_name in host.hostname:
            if name.lower() == h_name.lower():
                return True
        return False

    @staticmethod
    def ip_in_host(host: Host = None, ip: str = None) -> bool:
        """
        Check if a given IP is in a given Host

        :param Host host: Host in which to search for the IP
        :param str ip: The IP which is being searched
        :return bool: True if the IP is found, False otherwise
        """
        if (ip is None) or (host is None):
            return False
        for host_ip in host.ip:
            if host_ip == ip:
                return True
        return False

    def host_in_hosts_list(self, in_host: Host = None) -> bool:
        """
        Check if a given host is in the hosts list
        
        :param Host in_host: Host to search for 
        :return bool: True if the host is found, false otherwise 
        """
        if in_host is None:
            return False
        for host in self.HOSTSLIST:
            if host is in_host:
                return True
        return False

    @staticmethod
    def make_host(name: str = None, ip: str = None) -> Host:
        """
        Make a host object given the name and ip

        :param str name: Name of the host
        :param str ip: IP of the host
        :return Host: The Host object
        """
        return Host(hostname=[name], ip=[ip])

    """
    GENERAL FUNCTIONS
    """

    def get_version(self) -> str:
        """
        Return the version of this LIB

        :return str: Version of this LIB
        """
        return self.VERSION

    def clean_string_list(self, in_list: [str] = None) -> [str]:
        """
        Clear a list of strings

        :param [str] in_list: List of string to be cleaned
        :return [str]: Cleaned list of string, same list return if error
        """
        try:
            m_list = []
            for m in in_list:
                if (m != "") or (len(m) >= 1):
                    m_list.append(self.clean_string(m))
            return m_list
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return in_list

    def clean_string(self, in_string: str = None) -> str:
        """
        Clean a given string

        :param str in_string: String to be cleaned
        :return str: Cleaned string
        """
        try:
            m_string = in_string.replace("\n", "").replace("\r", "").strip()
            m_string = re.sub('\s+', ' ', m_string).strip()
            return m_string
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return in_string

    def sanitize_string(self, in_string: str = None, black_list: [str] = None):
        """
        Sanitized a given string. Removes punctuations, and back listed words from string

        :param str in_string: String to be sanitized
        :param [str] black_list: List of blacklisted words to remove
        :return str:
        """
        words = in_string.split()
        if black_list is not None:
            tmp = []
            for word in words:
                if word not in black_list:
                    tmp.append(word)
            words = tmp

        m_string = []
        for word in words:
            m_word = []
            for char in word:
                if char not in self.PUNCTUATION:
                    m_word.append(char)
            m_string.append("".join(m_word))
        clean_string = self.clean_string(" ".join(m_string))
        self.write_log("Sanitized string: {}".format(clean_string))
        return clean_string

    @staticmethod
    def remove_char_from_string(in_string: str = None, white_list: [str] = None) -> [str, None]:
        """
        Remove non-ascii letters and non-white-list chars from string

        :param str in_string: String to be cleaned
        :param [str] white_list: List of chars not to remove
        :return [str, None]: Cleaned string

        :ivar [str] _valid_chars: List of valid chars or None if error
        """
        if in_string is None:
            return in_string
        if type(in_string) is not str:
            return in_string
        _valid_chars = string.ascii_letters + string.digits + white_list
        tmp_string = ""
        for char in in_string:
            if char in _valid_chars:
                tmp_string = "{}{}".format(tmp_string, char)
        return tmp_string

    @staticmethod
    def is_legal_string(in_string: str = None, white_list: [str] = None) -> bool:
        """
        Checks if the string is legal. Only ascii chars and white list chars

        :param str in_string: String to be checked
        :param [str] white_list: List of valid chars
        :return bool: True if the string is valid, False otherwise
        """
        if in_string is None:
            return False
        if type(in_string) is not str:
            return False
        _valid_chars = string.ascii_letters + string.digits + white_list
        for char in in_string:
            if char not in _valid_chars:
                return False
        return True

    def encode(self, value: str = None, key: str = "secret") -> [str, None]:
        """
        Encode a given value using base64. A key can be given to further secure the encoding
        NOTE: THIS IS NOT SECURE ENCRYPTION.. BUT ATLEAST ITS NOT PLAIN TEXT

        :param str value: Value to be encoded
        :param str key: Salt value when encoding
        :return [str, None]: Encoded string
        """
        self.write_log("Encoding: {}".format(value))
        encoded_value = None
        if value is None:
            return encoded_value
        try:
            encoded_key = base64.b64encode(key.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(
                self.get_config_value('CharEncoding', 'utf-8'))
            value_length = len(value)
            m_value = "{}{}{}".format(value[:int(value_length / 2)], encoded_key, value[int(value_length / 2):])
            encoded_value = base64.b64encode(m_value.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(
                self.get_config_value('CharEncoding', 'utf-8'))
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return encoded_value

    def decode(self, value: str = None, key: str = "secret") -> [str, None]:
        """
        Decode a given value using base64. A key has to be given if it was encoded using one
        NOTE: THIS IS NOT SECURE ENCRYPTION... BUT ALTEAST ITS NOT PLAIN TEXT

        :param str value: String to decode
        :param str key: Salt value when decoding
        :return [str, None]: Decoded string
        """
        self.write_log("Decoding: {}".format(value))
        m_value = None
        if value is None:
            return m_value
        try:
            encoded_key = base64.b64encode(key.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(
                self.get_config_value('CharEncoding', 'utf-8'))
            decoded_value = base64.b64decode(value.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(
                self.get_config_value('CharEncoding', 'utf-8'))
            m_value = decoded_value.replace(encoded_key, "")
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return m_value

    def is_ip(self, in_string: str = None) -> bool:
        """
        Check if a string is ipV4
        
        :param str in_string: IP being tested 
        :return bool: True is the string is an IP, False otherwise 
        """
        return_value = True
        if in_string is None:
            return_value = False
            self.write_log("{} is ip: {}".format(in_string, return_value))
            return return_value
        parts = in_string.split(".")
        if len(parts) != 4:
            return_value = False
            self.write_log("{} is ip: {}".format(in_string, return_value))
            return return_value
        for part in parts:
            try:
                int_val = int(part)
                if (int_val > 255) or (int_val < 0):
                    return_value = False
            except:
                return_value = False
        self.write_log("{} is ip: {}".format(in_string, return_value))
        return return_value

"""
####################################################################################################


    MySQL Database


####################################################################################################
"""


class MySQL:
    """
    MySQL object

    :param str host: Hostname of the DB host
    :param str username: DB Username
    :param str password: DB user password
    :param str database: DB name to connect to
    :param LIB lib: Lib used as a reference to create a local copy

    :ivar mysql.connector.MySQLConnection CONN: Connection object to the database
    :ivar CUR: Cursor object to retrieve data
    :ivar LIB lib: Local Lib object for logging and config
    :ivar str config: DB connection configs
    """

    CONN = None
    """
    Connection to the DB
    """

    CUR = None
    """
    Cursor used to interact with the DB
    """

    lib: LIB = None
    """
    Lib used for logging and config file
    """

    config: dict = None
    """
    MySQL DB connection configs
    """

    def __init__(self, host: str = None, username: str = None, password: str = None, database: str = None,
                 lib: LIB = None):
        # Import the mysql connector return if it's not installed
        try:
            import mysql.connector
        except:
            return

        # Make sure all the values are given
        if (host is None) or (username is None) or (password is None) or (database is None):
            return

        # Make a lib instance for itself
        if (lib is None) and (self.lib is None):
            self.lib = LIB(out_log="mysql_{}_{}_output.log".format(host, database),
                           err_log="mysql_{}_{}_error.log".format(host, database))
        else:
            self.lib = LIB(home=lib.HOME)
            self.lib.OUT_LOG = "mysql_{}_{}_output.log".format(host, database)
            self.lib.ERR_LOG = "mysql_{}_{}_error.log".format(host, database)

        # Make the config dict for mysql conn
        self.config = {
            'user': username,
            'password': password,
            'host': host,
            'database': database
        }
        # Try to make the mysql connection
        try:
            self.CONN: mysql.connector.MySQLConnection = mysql.connector.connect(**self.config)
        except Exception as e:
            tmp_string = "Could not connect '{}'".format(self.config)
            self.lib.write_log(tmp_string)
            self.lib.write_error(tmp_string)
            self.lib.write_error("Error: {}".format(e))
            self.end()
            return
        # Get the cursor
        self.CUR = self.CONN.cursor(dictionary=True)

        self.lib.write_log("Connected {}".format(self.config))

    def end(self):
        """
        Terminate the MySQL object

        :return:
        """
        self.close_connection()
        self.lib.write_log("Terminating")
        self.lib.end()
        del self

    def close_connection(self):
        """
        Close a database connection

        :return:
        """
        self.lib.write_log("Closing {}".format(self.config))
        if self.CUR is not None:
            self.CUR.close()
        if self.CONN is not None:
            self.CONN.close()

    def reconnect(self):
        """
        Reconnect to the DB

        :return:
        """
        self.lib.write_log("Attempting to re-connect {}".format(self.config))
        # import the mysql connector return if it's not installed
        try:
            import mysql.connector
        except:
            return
        try:
            self.CONN = mysql.connector.connect(**self.config)
        except Exception as e:
            tmp_string = "Could not re-connect '{}'".format(self.config)
            self.lib.write_log(tmp_string)
            self.lib.write_error(tmp_string)
            self.lib.write_error("Error: {}".format(e))
            self.end()

    def select(self, query: str = None, variables: () = None):
        """
        Run a select query

        :param str query: Select query
        :param () variables: Tuple of values to map into the query
        :return [(), None]: List of tuples with results or None if error
        """
        # Ensure a query is given
        if query is None:
            self.lib.write_log("Query is None")
            return None
        # Ensure the query is a select statement
        if query.lower().split(" ")[0] != "select":
            self.lib.write_log("Query not select statement")
            return None
        self.lib.write_log("Running '{}'".format(query))
        # There are no variables in this query
        if variables is None:
            try:
                self.CUR.execute(query)
                results = self.CUR.fetchall()
                self.lib.write_log("Result count {}".format(self.CUR.rowcount))
                return results
            except Exception as e:
                tmp_string = "Query execution error"
                self.lib.write_log(tmp_string)
                self.lib.write_error(tmp_string)
                self.lib.write_error("Error: {}".format(e))
                return None
        # There are variables in this query
        elif variables is not None:
            # Ensure the variables are given as tuples
            if type(variables) is not tuple:
                self.lib.write_log("Variables need to be a tuple")
                return None
            try:
                self.CUR.execute(query, variables)
                results = self.CUR.fetchall()
                self.lib.write_log("Result count {}".format(self.CUR.rowcount))
                return results
            except Exception as e:
                tmp_string = "Query execution error"
                self.lib.write_log(tmp_string)
                self.lib.write_error(tmp_string)
                self.lib.write_error("Error: {}".format(e))
                return None

    def create_table(self, table_definition: str = None) -> bool:
        """
        Create a new table

        :param str table_definition: Create table query
        :return bool: Status of the table creation
        """
        if table_definition is None:
            self.lib.write_log("Need table definition")
            return False
        # ensure the table definition is a create table statement
        if table_definition.lower().split(" ")[0] != "create":
            self.lib.write_log("Query not select statement")
            return False
        self.lib.write_log("Creating table definition: '{}'".format(table_definition))
        try:
            self.CUR.execute(table_definition)
            self.lib.write_log("Affected rows {}".format(self.CUR.rowcount))
            return True
        except Exception as e:
            string = "Create table error"
            self.lib.write_log(string)
            self.lib.write_error(string)
            self.lib.write_error("Error: {}".format(e))
            return False

    def insert(self, query: str = None, values: () = None) -> [int, None]:
        """
        Insert query to add data to DB

        :param str query: Insert query
        :param () values: Tuple of values to map to query
        :return [int, None]: Inserted row_count or None if error
        """
        if (query is None) or (values is None):
            self.lib.write_log("Need both query and values")
            return None
        if type(values) is not list:
            self.lib.write_log("Values need to be list of tuples")
            return None
        self.lib.write_log("Running {}".format(query))
        self.lib.write_log("With {} entries".format(len(values)))
        try:
            self.CUR.executemany(query, values)
            self.CONN.commit()
            self.lib.write_log("Affected rows {}".format(self.CUR.rowcount))
            return self.CUR.rowcount
        except Exception as e:
            self.CONN.rollback()
            tmp_string = "Insert error"
            self.lib.write_log(tmp_string)
            self.lib.write_error(tmp_string)
            self.lib.write_error("Error: {}".format(e))
            return None

    def update(self, query: str = None, values: () = None) -> [int, None]:
        """
        Update multiple rows in DB

        :param str query: Update query
        :param () values: Tuple of values to map to query
        :return [int, None]: Updated row_count or None if error
        """
        if (query is None) or (values is None):
            self.lib.write_log("Need both query and values")
            return None
        if type(values) is not list:
            self.lib.write_log("Values need to be list of tuples")
            return None
        self.lib.write_log("Running {}".format(query))
        self.lib.write_log("With {} entries".format(len(values)))
        try:
            self.CUR.executemany(query, values)
            self.CONN.commit()
            self.lib.write_log("Affected rows {}".format(self.CUR.rowcount))
            return self.CUR.rowcount
        except Exception as e:
            self.CONN.rollback()
            tmp_string = "Update error"
            self.lib.write_log(tmp_string)
            self.lib.write_error(tmp_string)
            self.lib.write_error("Error: {}".format(e))
            return None

    def delete(self, query: str = None, values: str = None) -> [int, None]:
        """
        Delete query

        :param str query: Delete query
        :param () values: Tuple of values to map to query
        :return [int, None]: Deleted row_count or None if error
        """
        if query is None:
            self.lib.write_log("Need query")
            return None
        if type(values) is not list:
            self.lib.write_log("Values need to be list of tuples")
            return None
        self.lib.write_log("Running {}".format(query))
        self.lib.write_log("With {} entries".format(len(values)))
        try:
            self.CUR.executemany(query, values)
            self.CONN.commit()
            self.lib.write_log("Affected rows {}".format(self.CUR.rowcount))
            return self.CUR.rowcount
        except Exception as e:
            self.CONN.rollback()
            tmp_string = "Delete error"
            self.lib.write_log(tmp_string)
            self.lib.write_error(tmp_string)
            self.lib.write_error("Error: {}".format(e))
            return None
