from __future__ import print_function
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython.utils.tempdir import TemporaryDirectory
from IPython.core.display import HTML
from IPython.core import magic_arguments
from notebook.services.config.manager import ConfigManager
import subprocess, os, sys
import json
import re
from datetime import timedelta

@magics_class
class MznMagics(Magics):

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    @magic_arguments.argument(
        '-s',
        '--statistics',
        action='store_true',
        help='Output statistics'
    )
    @magic_arguments.argument(
        '-m',
        '--solution-mode',
        choices=["return","bind"],
        default="return",
        help='Whether to return solution(s) or bind them to variables'
    )
    @magic_arguments.argument(
        '-a',
        '--all-solutions',
        action='store_true',
        help='Return all solutions for satisfaction problems, intermediate solutions for optimisation problems. Implies -o.'
    )
    @magic_arguments.argument(
        '-t',
        '--timeout',
        type=int,
        help='Timeout (in seconds)'
    )
    @magic_arguments.argument(
        '--solver',
        choices=["gecode","cbc"],
        default="gecode",
        help='Solver to run'
    )
    @magic_arguments.argument(
        '--data',
        nargs='*',
        default=[],
        help='Data files'
    )
    @magic_arguments.argument(
        'model',
        nargs='*',
        default=[],
        help='Model to solve'
    )

    @line_cell_magic
    def minizinc(self, line, cell=None):
        "MiniZinc magic"
        args = magic_arguments.parse_argstring(self.minizinc, line)
        solver = []
        if args.solver=="gecode":
            solver = ["fzn-gecode"]
            if args.timeout:
                solver.append("-time")
                solver.append(args.timeout*1000)
            mznlib = "-Ggecode"
        elif args.solver=="cbc":
            solver = ["mzn-cbc"]
            if args.timeout:
                solver.append("--timeout")
                solver.append(args.timeout)
            mznlib = "-Glinear"
        else:
            print("No solver given")
            return
        
        mzn2fzn = ["mzn2fzn",mznlib]
        if args.verbose:
            mzn2fzn.append("-v")
        if args.statistics:
            mzn2fzn.append("-s")
        
        if args.statistics:
            solver.append("-s")
        if args.all_solutions:
            solver.append("-a")
        
        my_env = os.environ.copy()

        cwd = os.getcwd()
        
        with TemporaryDirectory() as tmpdir:
            with open(tmpdir+"/model.mzn", "w") as modelf:
                if cell is not None:
                    modelf.write(cell)
                modelf.close()
                pipes = subprocess.Popen(mzn2fzn+["--model-interface-only",tmpdir+"/model.mzn"]+args.model+args.data,
                                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                (output,erroutput) = pipes.communicate()
                if pipes.returncode != 0:
                    print(erroutput.rstrip().decode())
                    return
                model_ifc = json.loads(output)
                errors = []
                bindings = {}
                for var in model_ifc["input"]:
                    if var in self.shell.user_ns.keys():
                        bindings[var] = self.shell.user_ns[var]
                    else:
                        errors.append("Variable "+var+" is undefined")
                if len(errors)>0:
                    print("\n".join(errors))
                    return
                else:
                    jsondata = []
                    if len(bindings)!=0:
                        with open(tmpdir+"/data.json", "w") as dataf:
                            json.dump(bindings, dataf)
                        dataf.close()
                        jsondata = [tmpdir+"/data.json"]
                    pipes = subprocess.Popen(mzn2fzn+["--output-mode","json",tmpdir+"/model.mzn"]+args.model+
                                             jsondata+args.data,
                                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                    (output,erroutput) = pipes.communicate()
                    if pipes.returncode != 0:
                        print("Error in MiniZinc:\n"+erroutput.decode())
                        return
                    if len(erroutput) != 0:
                        if args.statistics:
                            compiler_stats = erroutput.decode().splitlines()
                        else:
                            print(erroutput.rstrip().decode())
                    pipes = subprocess.Popen(solver+[tmpdir+"/model.fzn"],
                                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                    (fznoutput,erroutput) = pipes.communicate()
                    if pipes.returncode != 0:
                        print("Error in "+solver[0]+":\n"+erroutput.decode())
                    if len(erroutput) != 0:
                        if args.statistics and args.solver == "cbc":
                            solver_stats = erroutput.decode().splitlines()
                        else:
                            print(erroutput.rstrip().decode())
                    with open(tmpdir+"/model.ozn","r") as oznfile:
                        ozn = oznfile.read()
                    solns2outArgs = ["solns2out",
                                     "--unsat-msg","",
                                     "--unbounded-msg","",
                                     "--unsatorunbnd-msg","",
                                     "--unknown-msg","",
                                     "--error-msg","",
                                     "--search-complete-msg","",
                                     "--solution-comma",",",
                                     "--soln-separator","",
                                     tmpdir+"/model.ozn"]
                    pipes = subprocess.Popen(solns2outArgs,
                                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                    (solns2output,erroutput) = pipes.communicate(fznoutput)
                    if pipes.returncode != 0:
                        print("Error in solns2out:\n"+erroutput.decode())
                        return
                    if len(erroutput) != 0:
                        print(erroutput.rstrip().decode())
                    # Remove comments from output
                    cleanoutput = []
                    commentsoutput = []
                    for l in solns2output.decode().splitlines():
                        comment = re.search(r"^\s*%+\s*(.*)",l)
                        if comment:
                            commentsoutput.append(comment.group(1))
                        else:
                            cleanoutput.append(l)
                    solutions = json.loads("["+"".join(cleanoutput)+"]")
                    if args.statistics:
                        if args.solver == "gecode":
                            solver_stats = commentsoutput
                        statistics = self.parse_statistics(
                            args.solver,
                            compiler_stats,
                            solver_stats
                        )
                    if len(commentsoutput) > 0:
                        print("Solver output:")
                        print("\n".join(commentsoutput))
                    if args.solution_mode=="return":
                        ret = None
                        if args.all_solutions:
                            ret = solutions
                        else:
                            if len(solutions)==0:
                                ret = None
                            else:
                                ret = solutions[-1]
                        if args.statistics:
                            return (ret, statistics)
                        else:
                            return ret
                    else:
                        if args.statistics:
                            print("statistics=" + str(statistics))
                            self.shell.user_ns["statistics"] = statistics
                        if len(solutions)==0:
                            print("No solutions found")
                            return None
                        else:
                            solution = solutions[-1]
                            for var in solution:
                                self.shell.user_ns[var] = solution[var]
                                print(var+"="+str(solution[var]))
                    return
                    
        
        # print("Full access to the main IPython object:", self.shell)
        # print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return

    def parse_statistics(self, solver, compiler_out, solver_out):
        statistics = {"flatzinc": {}, "solver": {}}
        # Parse Flattening statistics
        for line in compiler_out:
            regex = re.search(r"Paths:\s*(\d+)", line)
            if regex:
                statistics["flatzinc"]["paths"] = int(regex.group(1))
                continue

            regex = re.search(r"Variables:\s*((\d+)\s*bool,?)?\s*((\d+)\s*int,?)?\s*((\d+)\s*float,?)?\s*((\d+)\s*set,?)?", line)
            if regex:
                if regex.group(2) is not None:
                    statistics["flatzinc"]["bool variables"] = int(regex.group(2))
                if regex.group(4) is not None:
                    statistics["flatzinc"]["int variables"] = int(regex.group(4))
                if regex.group(6) is not None:
                    statistics["flatzinc"]["float variables"] = int(regex.group(6))
                if regex.group(8) is not None:
                    statistics["flatzinc"]["set variables"] = int(regex.group(8))
                continue

            regex = re.search(r"Constraints:\s*((\d+)\s*bool,?)?\s*((\d+)\s*int,?)?\s*((\d+)\s*float,?)?\s*((\d+)\s*set,?)?", line)
            if regex:
                if regex.group(2) is not None:
                    statistics["flatzinc"]["bool constraints"] = int(regex.group(2))
                if regex.group(4) is not None:
                    statistics["flatzinc"]["int constraints"] = int(regex.group(4))
                if regex.group(6) is not None:
                    statistics["flatzinc"]["float constraints"] = int(regex.group(6))
                if regex.group(8) is not None:
                    statistics["flatzinc"]["set constraints"] = int(regex.group(8))
                continue

            regex = re.search(r"This\s+is\s+a\s+(.*)\s+problem.", line)
            if regex:
                statistics["flatzinc"]["method"] = regex.group(1)
                continue

        # Parse solver statistics
        if solver == "gecode":
            tmp = []
            while len(solver_out) > 0:
                line = solver_out.pop()
                # Parse times
                regex = re.search(r"(runtime|solvetime):\s+\d+.\d+\s+\((\d+).(\d+)\s+ms\)", line)
                if regex:
                    statistics["solver"][regex.group(1)] = timedelta(milliseconds=int(regex.group(2)), microseconds=int(regex.group(3)))
                    continue
                # Parse simple numbers
                regex = re.search(r"(solutions|variables|propagators|propagations|nodes|failures|restarts|peak depth):\s+(\d+)", line)
                if regex:
                    statistics["solver"][regex.group(1)] = int(regex.group(2))
                    continue

                tmp.append(line)

            tmp.reverse()
            solver_out.extend(tmp)
        elif solver == "cbc":
            for line in solver_out:
                # Parse Status
                regex = re.search(r"MIP Status:\s+(\w+)", line)
                if regex:
                    statistics["solver"]["status"] = regex.group(1).lower()
                    continue
                # Parse other statistics
                regex = re.search(r"obj, bound, CPU_time, nodes \(left\):\s*(\d+),\s*(\d+),\s*(\d+).(\d+),\s*(\d+)\s*\(\s*(-?\d+)\s*\)", line)
                if regex:
                    statistics["solver"]["objective"] = int(regex.group(1))
                    statistics["solver"]["bound"] = int(regex.group(2))
                    statistics["solver"]["CPU time"] = timedelta(seconds=int(regex.group(3)), milliseconds=int(regex.group(4)))
                    statistics["solver"]["nodes"] = int(regex.group(5))
                    statistics["solver"]["nodes left"] = int(regex.group(6))
                    continue
        else:
            print("Unknown solver statistics formatting")

        return statistics


def checkMzn():
    try:
        pipes = subprocess.Popen(["mzn2fzn","--version"],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (output,erroutput) = pipes.communicate()
        if pipes.returncode != 0:
            print("Error while initialising extension: cannot run mzn2fzn. Make sure it is on the PATH when you run the Jupyter server.")
            return False
        print(output.rstrip().decode())
    except OSError as e:
        print("Error while initialising extension: cannot run mzn2fzn. Make sure it is on the PATH when you run the Jupyter server.")
        return False
    return True
