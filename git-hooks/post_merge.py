import subprocess
from initialization.hashes_init import sync_hashes

def system(*args, **kwargs):
  kwargs.setdefault('stdout', subprocess.PIPE)
  proc = subprocess.Popen(args, **kwargs)
  out, err = proc.communicate()
  return out

repo_path = system('git', 'rev-parse', '--show-toplevel').decode().strip()
sync_hashes(repo_path)
