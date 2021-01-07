# !/usr/bin/python3

'''
This is a lib file I've worked on since python2. It provides a lot of functions, not all useful all the time.
For this project, it is primary used for it's logging and config features.

You are more than welcome to go through it, and modify it should you need to.

IT HAS ONLY BEEN TESTED ON LINUX SYSTEMS.
'''

# imports
from datetime import datetime as DT
from datetime import timedelta as TD
import time
import sys
import subprocess
import os
import inspect
import multiprocessing as MP
import base64
import re
import shutil
import getpass
import string

#Multiprocessing shared memory manager
MANAGER = MP.Manager()

class File:
    """
    File Object Class, stores attributes about a given file.
    """
    def __init__(self,name=None, permissions=None, size=None, modified_time=None, path=None):
        self.name = name
        self.permissions = permissions
        self.size = size
        self.modified_time = modified_time
        self.path = path    #includes the name of the file
        filename, file_extension = os.path.splitext(self.path)
        self.extension = file_extension
        self.is_directory = os.path.isdir(self.path)

    def to_string(self):
        """
        Return a dict string of all the attributes for this class
        :return: String dict of all attributes
        :rtype: String
        """
        return str(self.__dict__)

    def __str__(self):
        """
        Same as to_string function
        :return:
        :rtype:
        """
        return str(self.__dict__)

class Host:
    """
    Host object class, stores attributes about a host. Read from the hosts file.
    """
    hostname = []
    ip = "None"
    def __init__(self, hostname, ip):
        if hostname is not None:
            self.hostname = hostname
        else:
            self.hostname = "None"
        if ip is not None:
            self.ip = ip
        else:
            self.ip = []

    def toString(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

class LIB:
    """
    Lib Object Class. Contains functions that are most commonly used in a project for simplicity of use.
    Most commonly used for logging, config file reading, and system command execution
    """
    PUNCTUATION = ['"', '\'', '*']
    HOME = None
    LOG = None
    CFG_IN_USE=None
    CFG = MANAGER.dict()
    ARGS = None
    MSGLIST = []
    PROCESSLIST = []
    OS = None
    OUT_LOG = None
    ERR_LOG = None
    HOSTSLIST= None
    LOGGING = True
    VERSION = 0.6

    LASTFILEROTATE=None

    def __init__(self, home=None, cfg=None, out_log = None, err_log = None):
        #find out home if none is given. lib location is used.
        self.PROCESSLIST = []
        if home is None:
            home = os.getcwd()
            parts = home.split("/")
            if parts[len(parts) - 1] == "bin":
                home = "/".join(parts[:len(parts) - 1])

        self.HOME = home
        # check and/or create the project structure
        if not self.path_exists(self.HOME):
            if not self.make_path(self.HOME):
                return

        #set the logs directory
        self.LOG = "{}/logs".format(self.HOME)
        if not self.path_exists(self.LOG):
            if not self.make_path(self.LOG):
                return

        #get and store the sys arguments
        self.ARGS = sys.argv

        #load the config file
        if cfg is None:
            cfg = self.get_args_value("-cfg", "{}/config/config.cfg".format(self.HOME))

        tmp_CFG = self.read_config(cfg)
        if tmp_CFG is None:
            self.CFG = MANAGER.dict()
        else:
            for key in tmp_CFG:
                self.CFG[key] = tmp_CFG[key]

        #set the output log file and error log file
        if out_log is None:
            self.OUT_LOG = self.get_config_value("outputlog","output.log")
        else:
            self.OUT_LOG = out_log
        if err_log is None:
            self.ERR_LOG = self.get_config_value("errorlog","error.log")
        else:
            self.ERR_LOG = err_log

        try:
            value = self.get_config_value("logging", True)
            if value == "false":
                self.LOGGING = False
        except:
            self.LOGGING = True

        self.write_log("Making lib instance: '{}'".format(home))
        self.write_log("ARGS: {}".format(self.ARGS))
        self.write_log("Using Config file: '{}'".format(cfg))
        self.write_log("Config: '{}'".format(self.CFG))

        #set the current running OS
        self.OS = self.clean_string(str(sys.platform).lower())
        self.write_log("Using OS: {}".format(self.OS))

        # Start the config file reload thread
        if self.get_config_value("ConfigReloadInterval", 0) != 0:
            confi_reloader = MP.Process(name = "ConfigReloader", target=self.auto_reload_config, args=(self.CFG,))
            confi_reloader.start()
            self.write_log("Starting config reload process with pid: {}".format(confi_reloader.pid))
            self.PROCESSLIST.append(confi_reloader)

    """
    CONFIG
    """

    # Read the file in config file format, and populate the CFG dictionary
    # Input  : config file
    # Output : CFG dict
    def read_config(self, cfgFile=None):
        self.CFG_IN_USE = cfgFile
        tmp_cfg = {}
        data = self.read_file(cfgFile)
        if (data == -1) or (data is None):
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
                    mList = value.replace("[", "").replace("]", "").split(",")
                    mList = list(map(self.sanitize_string, mList))
                    value = mList
                else:
                    try:
                        value = int(value)
                    except:
                        value = self.clean_string(value).lower()

                tmp_cfg[key] = value
        return tmp_cfg

    # Get a config key value, if no key exists, the given default value is returned
    # Input  : key, default value
    # Output : value
    def get_config_value(self, key, default=None):
        try:
            data = self.CFG[key.lower()]
        except:
            data = default
        return data

    # Auto-Reload the config file
    # input: String config file, to be executed once.
    # output: None
    def auto_reload_config(self, m_cfg=None, one_run=False):
        while True:
            #Ensure the parent process is still running. (1 means its been taken over by the kernal)
            if os.getppid() == 1:
                return 0

            if m_cfg is None:
                string = "Main config not provided"
                self.write_log(string)
                return 0

            self.write_log("Reloading confing '{}' from {}".format(self.CFG_IN_USE,os.getpid()))
            #read the config file into a temp var
            tmp_cfg = self.read_config(self.CFG_IN_USE)
            if tmp_cfg is not None:
                #clear out the config file.
                for key in m_cfg.keys():
                    if key in tmp_cfg:
                        self.write_log("Updating {}".format(key))
                        m_cfg[key] =  tmp_cfg[key]
                    else:
                        self.write_log("Removing {}".format(key))
                        del m_cfg[key]
                for key in tmp_cfg.keys():
                    if key not in m_cfg.keys():
                        self.write_log("Adding {}".format(key))
                        m_cfg[key] = tmp_cfg[key]
                self.write_log("New config values '{}'".format(m_cfg))
                self.write_log("Reloading done")
                self.sleep(self.get_config_value("ConfigReloadInterval", 60))
            else:
                self.sleep(2)
            if one_run:
                return

    # Reload the given lib with the given config file
    # input: String config file
    # output: None
    def reload_config(self):
        self.write_log("Reloading confing '{}' from {}".format(self.CFG_IN_USE, os.getpid()))
        tmp_cfg = self.read_config(self.CFG_IN_USE)
        if tmp_cfg is not None:
            self.CFG.clear()
            for key in tmp_cfg:
                self.CFG[key] = tmp_cfg[key]
            self.write_log("New config values '{}'".format(self.CFG))
            self.write_log("Reloading done")

    # Destroy this lib instance... it will become unusable if this is called
    # Input: None
    # Output: None
    def end(self):
        self.write_log("{} processes to terminate".format(len(self.PROCESSLIST)))
        for process in self.PROCESSLIST:
            if process.is_alive():
                self.write_log("Stopping process: {}".format(process.name))
                self.force_kill_process(process.pid)
        self.write_log("Terminating LIB instance")
        del self

    # Force kill a process
    # Input: pid of the process
    # Output: boolean
    def force_kill_process(self, in_pid=None):
        if in_pid is None:
            self.write_log("Need a process id")
            return False
        if type(in_pid) is not int:
            self.write_log("Process id must be an integer")
            return False
        if in_pid is os.getpid():
            self.write_log("Can't kill self")
            return False
        if in_pid == 1:
            self.write_log("Can't kill root process")
            return False
        if in_pid is os.getppid():
            self.write_log("Can't kill parent process")
            return False
        self.write_log("Killing pid : {}".format(in_pid))
        cmd = "kill -9 {}".format(in_pid)
        result = self.run_os_cmd(cmd)
        if result is None:
            self.write_log("CMD run error")
            return False
        if result[2] != 0:
            self.write_log("Return code for kill not normal")
            self.write_error("ERROR\n###########\n{}\n###########\n".format(result[1]))
        else:
            self.write_log("Successfully killed pid : {}".format(in_pid))
            return True

    # Get the name of the parent script that called lib
    # Input: None
    # Output: String
    def get_script(self):
        # Index definition for stack object
        FILENAME_INDEX = 1
        FUNCTIONAME_INDEX = 3

        # Get python stack
        try:
            stack = inspect.stack()
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None

        # Remove all python imports. (this in theory will only show usr writen scripts)
        m_stack = []
        for entry in stack:
            try:
                if ("python" not in entry[FILENAME_INDEX]) and ("__" not in entry[FUNCTIONAME_INDEX]):
                    m_stack.append(entry)
            except Exception as e:
                self.write_error("Error:\n####\n{}\n####\n".format(e))
                return None

        # reverse the stack (starting of the script is at the bottom, must bring it top)
        m_stack.reverse()
        try:
            for entry in m_stack:
                name = entry[FILENAME_INDEX]
                function = entry[FUNCTIONAME_INDEX]
                idx = m_stack.index(entry)
                # if this is the last entry in the last return script and function name
                if idx is len(m_stack) - 1:
                    if self.HOME in name:
                        name = name.split("/")[-1]
                    return "{}/{}".format(name, function)
                # get the next entry
                next_entry = m_stack[idx + 1]
                # if this is the first entry, and the next entry does not have the same name return script (this is pobably the main script)
                if (idx == 0) and (next_entry[FILENAME_INDEX] is not name):
                    if self.HOME in name:
                        name = name.split("/")[-1]
                    return "{}".format(name)
                # if the next entry is not the same return script and function name
                if (next_entry[FILENAME_INDEX] is not name):
                    if self.HOME in name:
                        name = name.split("/")[-1]
                    return "{}/{}".format(name, function)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None

    """
    SYSTEM ARGUMENTS
    """

    # Get the system argumnets
    # Input  : None
    # Output : list
    def get_args(self):
        return self.ARGS

    # Get a system key value, if no key exists, the given default value is returned. value is key index + 1
    # Input  : None
    # Output : list
    def get_args_value(self, key, default=None):
        args = self.ARGS
        try:
            idx = args.index(key)
            value = args[idx + 1]
        except Exception as e:
            value = default
        return value

    # Ket in system arguments
    # Input  : key
    # Output : boolean
    def in_args(self, key):
        args = self.ARGS
        if key in args:
            return True
        return False

    """
    IO
    """

    # Read string from user
    # Input: String message
    # Output: String user_input
    def read_string(self,message = "Enter a string: "):
        try:
            input_string = input(message)
            self.write_log("{} {}".format(message, input_string))
            return input_string
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None

    # Read password from user
    # Input: String message
    # Output: String user_input
    def read_password(self, message="Enter a password: "):
        try:
            input_string = getpass.getpass(prompt=message)
            return input_string
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None

    # Read int from user
    # Input: String message
    # Output: int user_input
    def read_int(self, message="Enter an integer: "):
        try:
            value = self.read_string(message)
            self.write_log("{} {}".format(message,value))
            if value == -1:
                return None
            intput_int = int(value)
            return intput_int
        except Exception as e:
            self.write_log("Invalid int")
            return None

    # Read int from user
    # Input: String message
    # Output: String user_input
    def read_char(self, message="Enter a character: "):
        try:
            input_string = self.read_string(message)
            self.write_log("{} {}".format(message, input_string))
            if len(input_string) != 1:
                return None
            return input_string
        except Exception as e:
            self.write_log("Invalid char")
            return None

    # Get a Ipv4 from the user
    # input: string
    # output: string
    def read_ip(self, message="Entry an IPv4: "):
        try:
            value = self.read_string(message=message)
            if self.is_ip(value) is False:
                return None
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
        self.write_log("{} {}".format(message, value))
        return value

    # Read the given file name, retuns a list of lines
    # Input  : filename
    # Output : list
    def read_file(self, fileName):
        self.write_log("Reading file {}".format(fileName))
        try:
            inFile = open(fileName, "r+", errors='ignore')
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        try:
            data = []
            for line in inFile:
                data.append(line)
            inFile.close()
            return data
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            inFile.close()
            return None

    # Write out put to the log file
    # Input  : string
    # Output : None
    def write_log(self, string, mode="a+"):
        if self.OUT_LOG is None:
            return
        try:
            out = open("{}/{}".format(self.LOG,self.OUT_LOG), mode)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        msg = "{} ~ {} ~ {}\n".format(self.get_now(), self.get_script(), string)
        try:
            con = self.get_config_value("console", 0)
            if (con == 1) or (con == 4):
                print(msg)
            if self.LOGGING:
                out.write(msg)
            out.close()
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return 0

    # Write out put to the error file
    # Input  : string
    # Output : None
    def write_error(self, string, mode="a+"):
        if self.ERR_LOG is None:
            return
        try:
            out = open("{}/{}".format(self.LOG,self.ERR_LOG), mode)
        except:
            return None
        msg = "{} ~ {} ~ {}\n".format(self.get_now(), self.get_script(), string)
        try:
            con = self.get_config_value("console", 0)
            if (con == 2) or (con == 4):
                print(msg)
            if self.LOGGING:
                out.write(msg)
            out.close()
        except:
            return None
        return 0

    # Write output to a specified file
    # Input: filename, string
    # Output: None
    def write_file(self, file_name, string=None, mode="a+", time_stamp=True):
        try:
            out = open(file_name, mode)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        if time_stamp:
            if string[len(string) - 1] == "\n":
                msg = "{} ~ {}".format(self.get_now(), string)
            else:
                msg = "{} ~ {}\n".format(self.get_now(), string)
        else:
            if string[len(string)-1] == "\n":
                msg = "{}".format(string)
            else:
                msg = "{}\n".format(string)
        try:
            out.write(msg)
            con = self.get_config_value("console", 0)
            if (con == 3) or (con == 4):
                print(msg)
            out.close()
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            out.close()
            return None
        return 0

    # List all the files and directories in a given path
    # Input: String path
    # Output: list of Files
    def directory_listing(self, directory=None, recursive = True):
        if not self.path_exists(directory):
            self.write_log("No such path {}".format(directory))
            return None
        self.write_log("Listing directory {} Recursive = {}".format(directory,recursive))
        files = []
        if recursive:
            for root, dirs, dire_files in os.walk(directory, topdown=False):
                for name in dire_files:
                    try:
                        stats = os.stat(os.path.join(root,name))
                        files.append(File(name=name, path=os.path.join(root, name), size=stats.st_size, modified_time=stats.st_mtime, permissions=oct(stats.st_mode)))
                    except:
                        pass
                for name in dirs:
                    try:
                        stats = os.stat(os.path.join(root, name))
                        files.append(File(name=name, path=os.path.join(root, name), size=stats.st_size, modified_time=stats.st_mtime, permissions=oct(stats.st_mode)))
                    except:
                        pass
        if not recursive:
            for f in os.listdir(directory):
                try:
                    stats = os.stat("{}/{}".format(directory,f))
                    files.append(File(name=f,path="{}/{}".format(directory,f), size=stats.st_size, modified_time=stats.st_mtime, permissions=oct(stats.st_mode)))
                except:
                    pass
        return files

    # Check if the given path already exists
    # Input: absolute path TODO: Make relative safe
    # Output: boolean
    def path_exists(self, path):
        self.write_log("Check path: {}".format(path))
        try:
            value = os.path.exists(path)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            value = False
        self.write_log("Path exists result: {}".format(value))
        return value

    # Make file, make the File object
    # Input: path to the file
    # Output: File object
    def make_file(self,in_file=None,create=None):
        if in_file is None:
            self.write_log("Need file path")
            return None
        if not self.file_exists(in_file):
            self.write_log("File does not exists")
            if create is not None:
                self.write_log("Creating new file {}".format(in_file))
                try:
                    file = open(in_file, "w+")
                    file.close()
                    self.write_log("Creating new file {}".format(in_file))
                except Exception as e:
                    self.write_error("Error creating file: {}".format(e))
                    return None
            else:
                return None
        name = os.path.basename(in_file)
        path = os.path.abspath(in_file)
        stats = os.stat(in_file)
        return File(name=name, path=path, size=stats.st_size, modified_time=stats.st_mtime,
                    permissions=oct(stats.st_mode))

    # Remove file, remove the given file
    # Input: path to the file or the file object
    # Output: boolean
    def remove_file(self,in_file=None):
        if in_file is None:
            self.write_log("Need a file path or name")
            return False
        file_name = None
        if type(in_file) is File:
            file_name = in_file.path
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

    # Check if the file exists
    # Input: Path to the file
    # Output: Boolean
    def file_exists(self,in_file=None):
        if in_file is None:
            self.write_log("Need file path")
            return False
        try:
            value = os.path.isfile(in_file)
            if value:
                return True
            else:
                return False
        except Exception as e:
            self.write_error("Error: {}".format(e))
            return False

    # File Rotation, rotate the given file, if it meets the
    # Input: File name / path
    # Output: Boolean
    def file_rotation(self, in_file=None, force_rotation=False):
        if type(in_file) is not File:
            if type(in_file) is str:
                if self.file_exists(in_file):
                    working_file = self.make_file(in_file)
                else:
                    logMessage = "File does not exist '{}'".format(in_file)
                    self.write_log(logMessage)
                    return None
            else:
                logMessage = "Unknown file type '{}'".format(in_file)
                self.write_log(logMessage)
                return None
        else:
            working_file = in_file

        if working_file is None:
            logMessage = "File is none"
            self.write_log(logMessage)
            return None

        self.write_log("File Rotation started: '{}'".format(working_file.path))

        list = os.path.split(working_file.path)
        dir = os.path.join(*list[:len(list) - 1])

        try:
            SIZELIMIT = float(self.get_config_value("LogRotationFileSize", 10))
            FILELIMIT = float(self.get_config_value("LogRotationFileLimit", 1))
        except Exception as e:
            logMessage = "Unknown config value"
            self.write_log(logMessage)
            SIZELIMIT = 10
            FILELIMIT = 1

        # get all the files at this path
        dirFiles = self.directory_listing(dir,False)

        # if force_rotation is set, this is ignored
        if not force_rotation:
            # ensure this file has a size grater than whats defined
            for dirFile in dirFiles:
                if dirFile.path == working_file.path:
                    print(float((SIZELIMIT * 1000) * 1024))
                    print(float(dirFile.size))
                    if float(dirFile.size) < float(((SIZELIMIT * 1000) * 1024)):
                        self.write_log("Size not at limit: '{}'".format(working_file.path))
                        return False
        else:
            self.write_log("Force Rotation")

        tmpList = []
        # remove files that are not an iteration of the file in question
        for dirFile in dirFiles:
            if working_file.name in dirFile.name:
                tmpList.append(dirFile)
        dirFiles = tmpList

        while int(len(dirFiles)) > int(FILELIMIT):
            # find the oldest files
            oldest = None
            for dirFile in dirFiles:
                if dirFile.name != working_file.name:
                    if (oldest is None):
                        oldest = dirFile
                    else:
                        if oldest.modified_time > dirFile.modified_time:
                            oldest = dirFile
            logMessage = "Removing oldest file '{}'".format(oldest.path)
            self.write_log(logMessage)
            cmd = "rm -f {}".format(oldest.path)
            out, err, return_code = self.run_os_cmd(cmd)
            if return_code != 0:
                logMessage = "Could not remove file '{}'".format(oldest.path)
                self.write_log(logMessage)
            dirFiles.remove(oldest)

        # rotate and make new files
        logMessage = "Copying file file '{}'".format(working_file.path)
        self.write_log(logMessage)
        new_name = "{}.{}".format( working_file.path,self.get_now().replace(" ", "-").replace(":", "-").split(".")[0])
        self.LASTFILEROTATE = new_name
        cmd = "mv {} {}".format(working_file.path,new_name)

        out, err, return_code = self.run_os_cmd(cmd)
        if return_code != 0:
            logMessage = "Could not move '{}'".format(working_file.path)
            self.write_log(logMessage)
            return False
        cmd = "touch {}".format(working_file.path)
        out, err, return_code = self.run_os_cmd(cmd)
        if return_code != 0:
            logMessage = "Could not create file '{}'".format(working_file.path)
            self.write_log(logMessage)
        self.write_log("File Rotation done: '{}.{}'".format(working_file.path,self.get_now().replace(" ", "-").replace(":", "-").split(".")[0]))
        return True

    # Create the given path. This is a recursive operation.
    # Input: absolute path TODO: Make relative safe
    # Output: boolean
    def make_path(self, path=None):
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

    # Remove the given path. This is a recursive operation.
    # Input: absolute path, force deletion
    # Output: boolean
    def remove_path(self, path=None,force=False):
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

    # Copy file
    # Input: String source, String destination
    # Output: None
    def copy_file(self,source=None, destination=None):
        if (source is None) or (destination is None):
            return None
        if not self.path_exists(source):
            return None
        self.write_log("COPY {} TO {}".format(source, destination))
        if not self.path_exists(destination):
            parts = destination.split("/")
            make_path = "/".join(parts[:len(parts)-1])
            self.make_path(make_path)
        try:
            shutil.copy2(source,destination)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return None

    # Run the given os command
    # Input: string (system command)
    # Output: [command.output, command.error, command.returncode]
    def run_os_cmd(self, cmd):
        tout = self.get_config_value("cmdtimeout", 60)
        if tout != 0:
            cmd = "timeout {} {}".format(tout, cmd)
        self.write_log("Running cmd: '{}'".format(cmd))
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
            p.wait()
            out, error = p.communicate()
            returnCode = p.poll()
            self.write_log("Code:{}\n==OUT==\n{}\n==OUT==\n==ERR==\n{}\n==ERR==".format(returnCode, out, error))
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return [out, error, returnCode]

    # Start the given os command as it's on process
    # Input: string (system command)
    # Output: subprocess.Popen obejct
    def start_process(self, cmd):
        self.write_log("Starting process cmd: '{}'".format(cmd))
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return p

    """
    TIME BASE
    """

    # Get the time now
    # Input: None
    # Output: string
    def get_now(self):
        return str(DT.now())

    # Convert time stamp to human readable date
    # Input: string (timestamp)
    # Output: string (human readable format)
    def timestamp_to_date(self, stamp):
        if stamp is not None:
            return str(DT.utcfromtimestamp(stamp)).split(".")[0]
        return None

    # Sleep for a given duration
    # Input: int (duration)
    # Output: none
    def sleep(self, duration):
        self.write_log("Sleeping for {}".format(duration))
        try:
            time.sleep(duration)
        except Exception as e:
            string = "Sleep error: '{}'".format(e)
            self.write_log("Sleep error")
            self.write_error(string)
        return

    # Delta time +/-
    # Input: Integer delta, String measure
    def time_delta(self, delta=None, measure=None):
        if (delta is None) or (measure is None):
            self.write_error("Invalid delta or measure")
            return None
        MEASURE = ['days','weeks','hours','minutes','seconds']
        if measure not in MEASURE:
            self.write_error("Invalid measure {}".format(measure))
            self.write_error("OPTIONS: {}".format(MEASURE))
            return None
        if type(delta) is not int:
            self.write_error("Delta must be an integer")
            return None
        self.write_log("Time delta {} {}".format(delta, measure))
        now = DT.now()
        future = False
        if delta >0:
            future = True
        delta = abs(delta)
        measure = measure.lower()
        return_value = None
        if future:
            if measure == "seconds":
                return_value = str(now + TD(seconds=delta)).split(".")[0]
            if measure == "minutes":
                return_value = str(now + TD(minutes=delta)).split(".")[0]
            if measure == "hours":
                return_value = str(now + TD(hours=delta)).split(".")[0]
            if measure == "days":
                return_value = str(now + TD(days=delta)).split(".")[0]
            if measure == "weeks":
                return_value = str(now + TD(weeks=delta)).split(".")[0]
        if not future:
            if measure == "seconds":
                return_value = str(now - TD(seconds=delta)).split(".")[0]
            if measure == "minutes":
                return_value = str(now - TD(minutes=delta)).split(".")[0]
            if measure == "hours":
                return_value = str(now - TD(hours=delta)).split(".")[0]
            if measure == "days":
                return_value = str(now - TD(days=delta)).split(".")[0]
            if measure == "weeks":
                return_value = str(now - TD(weeks=delta)).split(".")[0]
        return return_value

    '''
    HOSTS FUNCTIONS
    '''

    def remove_comments(self, hostsfile):
        self.write_log("Cleaning hosts file")
        newHosts = []
        # for each line the hosts file
        for line in hostsfile:
            # string any leading and tralling spaces, and the new line at the end
            line = line.strip().replace("\n", "")
            if line != "":
                # if the line starts with "#" or "*" ignore it
                if (line[0] != "#") and (line[0] != "*"):
                    # if the line has "#" in is parse out all the data after it
                    if "#" in line:
                        tmp = line[:line.index("#")]
                        newHosts.append(tmp.replace("\t", " "))
                    else:
                        newHosts.append(line.replace("\t", " "))
        return newHosts

    # Read the host file and convert them in to  hostsfile objects (hostFileClass.py)
    # input  : hostfile
    # output : list of hosts objects (hostFileClass.py)
    def generate_hosts_list(self, hostsfile):
        str = "Generating hosts list"
        self.write_log(str)
        # remove comments from file
        hosts = self.remove_comments(hostsfile)
        myHosts = []
        for h in hosts:
            ip = "None"
            hostname = []
            list = h.split(" ")
            if len(list) > 1:
                ip = list[0]
                for i in range(len(list)):
                    if (i != 0) and (list[i] != ""):
                        # for each hostname assigned to ip
                        hostname.append(list[i].strip().replace("\n", "").replace("\r", ""))
                myHosts.append(Host(hostname, ip))
        str = "Generation Done. Got %s hosts" % (len(myHosts))
        self.write_log(str)
        return myHosts

    # get the hostfile from /etc/hosts
    # input  : none
    # output : list of hosts objects (hostFileClass.py)
    def get_hosts(self, hosts_file = None):
        if hosts_file is None:
            hostsfile = self.read_file("/etc/hosts")
        else:
            hostsfile = self.read_file(hosts_file)
        if hostsfile is None:
            return None
        self.HOSTSLIST = self.generate_hosts_list(hostsfile)
        return self.HOSTSLIST

    # check to see if the name is assigned to host as one of its hostnames
    # input  : hosts object, name
    # output : 0 = false, 1 = true
    def name_in_hostnames(self, host, name):
        for hName in host.hostname:
            if name.lower() == hName.lower():
                return 1
        return 0

    # check to see if the ip given is the same as the ip for the host.
    # input  : hosts object, ip
    # output : 0 = false, 1 = true
    def isIp(self, host, ip):
        if (ip == "None") or (ip is None) or (ip == "0.0.0.0"):
            return 0
        if host.ip == ip:
            return 1
        return 0

    # check to see if the node (nodeClass) given is in hostfile
    # input  : node object
    # output : 0 = false, 1 = true
    def in_hosts_list(self, node):
        for host in self.HOSTSLIST:
            if self.name_in_hostnames(host, node.name):
                if len(node.ip) >= 1:
                    if not (self.isIp(host, node.ip)):
                        return 0
                return 1
        return 0

    def get_hostnames(self, ip=None):
        if ip is None:
            return None
        if not self.is_ip(ip):
            return None
        for host in self.HOSTSLIST:
            if host.ip == ip:
                string = ",".join(host.hostname)
                return string

    # return the nodename syntex from the hostsfile
    # input  : node object
    # output : name OR None
    def get_host_name_syntax(self, node):
        for host in self.HOSTSLIST:
            for hName in host.hostname:
                if node.name.lower() == hName.lower():
                    return hName
        return None

    """
    GENERAL FUNCTIONS
    """

    #Get the version number of this liberary
    #input: none
    #output: version number (string)
    def get_version(self):
        return str(self.VERSION)

    # Clean the given list of strings. Errors result in the same list being returned
    # Input: list (of strings)
    # Output: list (of string)
    def clean_string_list(self, list):
        try:
            mlist = []
            for m in list:
                if (m != "") or (len(m) >= 1):
                    mlist.append(self.clean_string(m))
            return mlist
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return list

    # Clean the given string. Remove newline characters, and strip whitespaces. Errors result in the same string being returned
    # Input: string
    # Output: string
    def clean_string(self, string):
        try:
            mstring = string.replace("\n", "").replace("\r", "").strip()
            mstring = re.sub('\s+', ' ', mstring).strip()
            return mstring
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return string

    # Sanitize string, remove all punctuations (defined at the top), newlines, and whitespaces
    # Input: string
    # Output: string
    def sanitize_string(self, instring, black_list=None):
        words = instring.split()

        if black_list != None:
            tmp = []
            for word in words:
                if word not in black_list:
                    tmp.append(word)
            words = tmp

        mstring = []
        for word in words:
            mword = []
            for char in word:
                if char not in self.PUNCTUATION:
                    mword.append(char)
            mstring.append("".join(mword))
        string = self.clean_string(" ".join(mstring))
        self.write_log("Sanitized string: {}".format(string))
        return string

    # Remove characters from string
    # Input: string
    # Output: string
    def remove_char_from_string(self, in_string=None, white_list=None):
        if in_string is None:
            return None
        if type(in_string) is not str:
            return None
        VALID_CHARS = string.ascii_letters + string.digits + white_list
        tmp_string = ""
        for char in in_string:
            if char in VALID_CHARS:
                tmp_string = "{}{}".format(tmp_string, char)
        return tmp_string

    # Return if letts and number are in the string, + any white list you define.
    # Input: string
    # Output: Boolean
    def is_legal_string(self, in_string=None, white_list=None):
        if in_string is None:
            return None
        if type(in_string) is not str:
            return None
        VALID_CHARS = string.ascii_letters + string.digits + white_list
        for char in in_string:
            if char not in VALID_CHARS:
                return False
        return True

    # Encode a given value using base64. A key can be given to further secure the encoding
    #  NOTE: THIS IS NOT SECURE ENCRIPTION... BUT ALTEAST ITS NOT PLAIN TEXT
    # Input: String value, String key
    # Output: String encoded_value
    def encode(self, value = None, key="secret"):
        self.write_log("Encoding: {}".format(value))
        encoded_value = None
        if value is None:
                return encoded_value
        try:
            encoded_key = base64.b64encode(key.encode(self.get_config_value('CharEncoding','utf-8'))).decode(self.get_config_value('CharEncoding','utf-8'))
            value_lenght = len(value)
            m_value = "{}{}{}".format(value[:int(value_lenght/2)],encoded_key,value[int(value_lenght/2):])
            encoded_value = base64.b64encode(m_value.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(self.get_config_value('CharEncoding', 'utf-8'))
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return encoded_value

    # Decode a given value using base64. A key has to be given if it was encoded using one
    #  NOTE: THIS IS NOT SECURE ENCRIPTION... BUT ALTEAST ITS NOT PLAIN TEXT
    # Input: String value, String key
    # Output: String decoded_value
    def decode(self, value = None, key="secret"):
        self.write_log("Decoding: {}".format(value))
        m_value = None
        if value is None:
            return m_value
        try:
            encoded_key = base64.b64encode(key.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(self.get_config_value('CharEncoding', 'utf-8'))
            decoded_value = base64.b64decode(value.encode(self.get_config_value('CharEncoding', 'utf-8'))).decode(self.get_config_value('CharEncoding', 'utf-8'))
            m_value = decoded_value.replace(encoded_key,"")
        except Exception as e:
            self.write_error("Error:\n####\n{}\n####\n".format(e))
            return None
        return m_value

    # Determines if string is ip v4
    # Input: string
    # Output: boolean
    def is_ip(self, string):
        return_value = True
        if string is None:
            return_value = False
            self.write_log("{} is ip: {}".format(string,return_value))
            return return_value
        parts = string.split(".")
        if len(parts) != 4:
            return_value = False
            self.write_log("{} is ip: {}".format(string,return_value))
            return return_value
        for part in parts:
            try:
                int_val = int(part)
                if (int_val > 255) or (int_val < 0):
                    return_value = False
            except:
                return_value = False
        self.write_log("{} is ip: {}".format(string,return_value))
        return return_value


"""
####################################################################################################


    MySQL Database


####################################################################################################
"""

class MySQL:
    CONN = None
    CUR = None
    lib = None
    config = None

    # Create a MySQL object (and connection)
    # Input: String host, String username, String password, String database, LIB lib)
    # Output: None
    def __init__(self,host=None,username=None,password=None,database=None, lib = None):
        #import the mysql connector return if it's not installed
        try:
            import mysql.connector
        except:
            return

        #make sure all the values are given
        if (host is None) or (username is None) or (password is None) or (database is None):
            return

        #make a lib instance for itself
        if (lib is None) and (self.lib is None):
            self.lib = LIB(home="/tmp",out_log="mysql_{}_{}_output.log".format(host,database),err_log="mysql_{}_{}_error.log".format(host,database))
        else:
            self.lib = LIB(home=lib.HOME)
            self.lib.OUT_LOG = "mysql_{}_{}_output.log".format(host,database)
            self.lib.ERR_LOG = "mysql_{}_{}_error.log".format(host,database)

        #make the config dict for mysql conn
        self.config = {
            'user': username,
            'password': password,
            'host': host,
            'database': database
        }
        #try to make the mysql connection
        try:
            self.CONN = mysql.connector.connect(**self.config)
        except Exception as e:
            string = "Could not connect '{}'".format(self.config)
            self.lib.write_log(string)
            self.lib.write_error(string)
            self.lib.write_error("Error: {}".format(e))
            self.end()
            return
        #get the cursor
        self.CUR = self.CONN.cursor(dictionary=True)

        self.lib.write_log("Connected {}".format(self.config))

    # Terminate this entire instance
    # Input: None
    # Output: None
    def end(self):
        self.close_connection()
        self.lib.write_log("Terminating")
        self.lib.end()
        del self

    # Close this mysql connection
    # Input: None
    # Output: None
    def close_connection(self):
        self.lib.write_log("Closing {}".format(self.config))
        if self.CUR is not None:
            self.CUR.close()
        if self.CONN is not None:
            self.CONN.close()

    # Reconnect using the config
    # Input: None
    # Output: None
    def reconnect(self):
        self.lib.write_log("Attempting to re-connect {}".format(self.config))
        # import the mysql connector return if it's not installed
        try:
            import mysql.connector
        except:
            return
        try:
            self.CONN = mysql.connector.connect(**self.config)
        except Exception as e:
            string = "Could not re-connect '{}'".format(self.config)
            self.lib.write_log(string)
            self.lib.write_error(string)
            self.lib.write_error("Error: {}".format(e))
            self.end()

    # Run select query
    # Input: String query, Tuples (values)
    # Output: list rows (as dictionaries)
    def select(self,query=None, variables=None):
        #ensure a query is given
        if query is None:
            self.lib.write_log("Query is None")
            return None
        #ensure the query is a select statement
        if query.lower().split(" ")[0] != "select":
            self.lib.write_log("Query not select statement")
            return None
        self.lib.write_log("Running '{}'".format(query))
        #there are no variables in this query
        if variables is None:
            try:
                self.CUR.execute(query)
                results = self.CUR.fetchall()
                self.lib.write_log("Result count {}".format(self.CUR.rowcount))
                return results
            except Exception as e:
                string = "Query execution error"
                self.lib.write_log(string)
                self.lib.write_error(string)
                self.lib.write_error("Error: {}".format(e))
                return None
        #there are variables in this query
        elif variables is not None:
            #ensure the variables are given as tuples
            if type(variables) is not tuple:
                self.lib.write_log("Variables need to be a tuple")
                return None
            try:
                self.CUR.execute(query,variables)
                results = self.CUR.fetchall()
                self.lib.write_log("Result count {}".format(self.CUR.rowcount))
                return results
            except Exception as e:
                string = "Query execution error"
                self.lib.write_log(string)
                self.lib.write_error(string)
                self.lib.write_error("Error: {}".format(e))
                return None

    # Create a new table
    # Input: tuple's of definitions
    # Output: boolean
    def create_table(self, table_definition=None):
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

    # Insert multiple rows into database
    # Input: String insert query, List of tuples (value, or values that need to be inserted)
    # Output: Int number of affected rows
    def insert(self, query=None, values=None):
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
            string = "Insert error"
            self.lib.write_log(string)
            self.lib.write_error(string)
            self.lib.write_error("Error: {}".format(e))
            return None

    # Update multiple rows into database
    # Input: String update query, List of tuples (value, or values that need to be inserted)
    # Output: Int number of affected rows
    def update(self, query=None, values=None):
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
            string = "Update error"
            self.lib.write_log(string)
            self.lib.write_error(string)
            self.lib.write_error("Error: {}".format(e))
            return None

    # Delete row from database
    # Input: Delete query
    # Output: Int number of affected rows
    def delete(self, query=None, values=None):
        if (query is None):
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
            string = "Delete error"
            self.lib.write_log(string)
            self.lib.write_error(string)
            self.lib.write_error("Error: {}".format(e))
            return None
