"""Bounded acceptance helpers: retain process identity and stop descendants on timeout."""
import subprocess
import psutil

def stop_tree(process):
    try:
        children=process.children(recursive=True)
    except psutil.NoSuchProcess:
        return
    owned=[*reversed(children),process]
    for item in owned:
        try:item.terminate()
        except psutil.NoSuchProcess:pass
    _,alive=psutil.wait_procs(owned,timeout=5)
    for item in alive:
        try:item.kill()
        except psutil.NoSuchProcess:pass
    _,alive=psutil.wait_procs(alive,timeout=5)
    if alive:raise RuntimeError('Test descendants did not terminate')

def run_bounded(command, *, env, timeout):
    child=subprocess.Popen(command,env=env)
    identity=psutil.Process(child.pid)
    try:
        return child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop_tree(identity)
        child.wait(timeout=5)
        raise
    except BaseException:
        stop_tree(identity)
        raise
