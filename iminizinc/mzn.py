from __future__ import print_function
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython.utils.tempdir import TemporaryDirectory
from IPython.core.display import HTML
from notebook.services.config.manager import ConfigManager
import subprocess, os, sys
import json

@magics_class
class MznMagics(Magics):

    @cell_magic
    def minizinc(self, line, cell):
        "minizinc cell magic"
        if line=="gecode":
            fzncommand = "fzn-gecode"
            mznlib = "-Ggecode"
        elif line=="cbc":
            fzncommand = "mzn-cbc"
            mznlib = "-Glinear"
        else:
            fzncommand = "fzn-gecode"
            mznlib = "-Ggecode"            

        my_env = os.environ.copy()

        with TemporaryDirectory() as tmpdir:
            with open(tmpdir+"/model.mzn", "w") as modelf:
                modelf.write(cell)
                modelf.close()
                pipes = subprocess.Popen(["mzn2fzn",mznlib,"--model-interface-only",tmpdir+"/model.mzn"],
                                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                (output,erroutput) = pipes.communicate()
                if pipes.returncode != 0:
                    print(erroutput)
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
                    with open(tmpdir+"/data.json", "w") as dataf:
                        json.dump(bindings, dataf)
                        dataf.close()
                        pipes = subprocess.Popen(["mzn2fzn",mznlib,"--output-mode","json",tmpdir+"/model.mzn",tmpdir+"/data.json"],
                                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                        (output,erroutput) = pipes.communicate()
                        if pipes.returncode != 0:
                            print("Error in MiniZinc:\n"+erroutput)
                            return
                        if len(erroutput) != 0:
                            print(erroutput)
                        pipes = subprocess.Popen([fzncommand,tmpdir+"/model.fzn"],
                                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=my_env)
                        (fznoutput,erroutput) = pipes.communicate()
                        if pipes.returncode != 0:
                            print("Error in "+fzncommand+":\n"+erroutput)
                        if len(erroutput) != 0:
                            print(erroutput)
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
                            print("Error in solns2out:\n"+erroutput)
                            return
                        if len(erroutput) != 0:
                            print(erroutput)
                        solutions = json.loads("["+solns2output+"]")
                        if len(solutions)==0:
                            print("No solutions found")
                            return
                        solution = solutions[-1]
                        bindings = []
                        for var in solution:
                            self.shell.user_ns[var] = solution[var]
                            bindings.append(var+"="+str(solution[var]))
                        print("\n".join(bindings))
                        return
                        
        
        # print("Full access to the main IPython object:", self.shell)
        # print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return

def checkMzn():
    try:
        pipes = subprocess.Popen(["mzn2fzn","--version"],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (output,erroutput) = pipes.communicate()
        if pipes.returncode != 0:
            print("Error while initialising extension: cannot run mzn2fzn. Make sure it is on the PATH when you run the Jupyter server.")
            return False
        print(output)
    except OSError as e:
        print("Error while initialising extension: cannot run mzn2fzn. Make sure it is on the PATH when you run the Jupyter server.")
        return False
    return True
