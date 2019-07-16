import subprocess
import os
from transient_auth.sync_hashes import sync_hashes


def system(*args, **kwargs):
  kwargs.setdefault('stdout', subprocess.PIPE)
  proc = subprocess.Popen(args, **kwargs)
  out, err = proc.communicate()
  return out

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authsite.settings")
repo_path = system('git', 'rev-parse', '--show-toplevel').decode().strip()
sync_hashes(repo_path)
