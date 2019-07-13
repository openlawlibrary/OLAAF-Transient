import subprocess
from initialization.hashes_init import post_merge_add_hashes

def system(*args, **kwargs):
  kwargs.setdefault('stdout', subprocess.PIPE)
  proc = subprocess.Popen(args, **kwargs)
  out, err = proc.communicate()
  return out

repo_path = system('git', 'rev-parse', '--show-toplevel').decode().strip()
post_merge_add_hashes(repo_path)
