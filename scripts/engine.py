"""Engine.py

This program is the command line interface of the engine
"""
from optparse import OptionParser
from engine import load_project, run_command

if __name__ == "__main__":
    usage = "Usage: %prog [options]"
    oparser = OptionParser(usage=usage)
    
    oparser.add_option("-p", "--project", type="string", help="project configuration file", dest="proj_config")
    oparser.add_option("-c", "--command", type="string", help="command to be executed on the project", dest="command")
    
    option, args = oparser.parse_args()
    
    if option.proj_config is not None and option.command is not None:
        project = load_project(option.proj_config)
        run_command(option.command, project)

    