from __future__ import print_function

import json
import os
import re
import subprocess

from IPython.core import magic_arguments
from IPython.core.magic import (Magics, magics_class, cell_magic, line_cell_magic)
from IPython.utils.tempdir import TemporaryDirectory

Solns2outArgs = [
    "--unsat-msg", "% The problem is infeasible",
    "--unbounded-msg", "",
    "--unsatorunbnd-msg", "",
    "--unknown-msg", "% No solution has been found",
    "--search-complete-msg", "",
    "--solution-comma", ",",
    "--soln-separator", ""
]

MznModels = {}


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
        choices=["return", "bind"],
        default="return",
        help='Whether to return solution(s) or bind them to variables'
    )
    @magic_arguments.argument(
        '-a',
        '--all-solutions',
        action='store_true',
        help='Return all solutions for satisfaction problems, intermediate solutions for optimisation problems. '
             'Implies -o. '
    )
    @magic_arguments.argument(
        '-t',
        '--time-limit',
        type=int,
        help='Time limit in milliseconds (includes compilation and solving)'
    )
    @magic_arguments.argument(
        '--solver',
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
        """MiniZinc magic"""
        mzn_proc = ["minizinc"]

        args = magic_arguments.parse_argstring(self.minizinc, line)
        if args.solver != "":
            mzn_proc.extend(["--solver", args.solver])
        else:
            print("No solver given")
            return

        mzn_test = mzn_proc[:]
        if args.verbose:
            mzn_proc.append("-v")
        if args.statistics:
            mzn_proc.append("-s")

        if args.statistics:
            mzn_proc.append("-s")
        if args.all_solutions:
            mzn_proc.append("-a")

        if args.time_limit:
            mzn_proc.append("--time-limit")
            mzn_proc.append(str(args.time_limit))

        my_env = os.environ.copy()

        with TemporaryDirectory() as tmpdir:
            with open(tmpdir + "/model.mzn", "w") as modelf:
                for m in args.model:
                    mzn = MznModels.get(m)
                    if mzn is not None:
                        args.model.remove(m)
                        modelf.write(mzn)
                if cell is not None:
                    modelf.write(cell)
                modelf.close()
                pipes = subprocess.Popen(
                    mzn_test + ["--model-interface-only", tmpdir + "/model.mzn"] + args.model + args.data,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)
                (output, erroutput) = pipes.communicate()
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
                        errors.append("Variable " + var + " is undefined")
                if len(errors) > 0:
                    print("\n".join(errors))
                    return
                else:
                    jsondata = []
                    if len(bindings) != 0:
                        with open(tmpdir + "/data.json", "w") as dataf:
                            json.dump(bindings, dataf)
                        dataf.close()
                        jsondata = [tmpdir + "/data.json"]
                    pipes = subprocess.Popen(mzn_proc
                                             + ["--output-mode", "json", tmpdir + "/model.mzn"]
                                             + args.model + Solns2outArgs
                                             + jsondata + args.data,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)
                    (mznoutput, erroutput) = pipes.communicate()
                    if pipes.returncode != 0:
                        print("Error in MiniZinc:\n" + erroutput.decode())
                        return
                    if len(erroutput) != 0:
                        print(erroutput.rstrip().decode())
                    # Remove comments from output
                    cleanoutput = []
                    commentsoutput = []
                    for l in mznoutput.decode().splitlines():
                        comment = re.search(r"^\s*%+\s*(.*)", l)
                        if comment:
                            commentsoutput.append(comment.group(1))
                        else:
                            cleanoutput.append(l)
                    solutions = json.loads("[" + "".join(cleanoutput) + "]")
                    if len(commentsoutput) > 0:
                        print("Solver output:")
                        print("\n".join(commentsoutput))
                    if args.solution_mode == "return":
                        if args.all_solutions:
                            return solutions
                        else:
                            if len(solutions) == 0:
                                return None
                            else:
                                return solutions[-1]
                    else:
                        if len(solutions) == 0:
                            print("No solutions found")
                            return None
                        else:
                            solution = solutions[-1]
                            for var in solution:
                                self.shell.user_ns[var] = solution[var]
                                if args.verbose:
                                    print(var + "=" + str(solution[var]))
                    return

        # print("Full access to the main IPython object:", self.shell)
        # print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return

    @cell_magic
    def mzn_model(self, line, cell):
        args = magic_arguments.parse_argstring(self.minizinc, line)
        if not args.model:
            print("No model name provided")
            return
        elif len(args.model) > 1:
            print("Multiple model names provided")
            return

        MznModels[args.model[0]] = cell
        return


def check_minizinc():
    try:
        pipes = subprocess.Popen(["minizinc", "--version"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, erroutput) = pipes.communicate()
        if pipes.returncode != 0:
            print("Error while initialising extension: cannot run minizinc. Make sure it is on the PATH when you run "
                  "the Jupyter server.")
            return False
        print(output.rstrip().decode())
    except OSError as _:
        print("Error while initialising extension: cannot run minizinc. Make sure it is on the PATH when you run the "
              "Jupyter server.")
        return False
    return True
