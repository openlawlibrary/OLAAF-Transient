from django.core.management.base import BaseCommand
from olaaf_django.sync_hashes import sync_hashes

class Command(BaseCommand):
  help = '''Traverse through all commits that have not yet been loaded into the database
and calcule and insert/update hashes of added, modified and deleted files'''

  def add_arguments(self, parser):
    parser.add_argument('path', type=str, help="Repository's path")

  def handle(self, *args, **kwargs):
    repo_path = kwargs['path']
    sync_hashes(repo_path)
