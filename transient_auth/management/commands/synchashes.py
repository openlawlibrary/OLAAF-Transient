from django.core.management.base import BaseCommand
from transient_auth.sync_hashes import sync_hashes

class Command(BaseCommand):
  help = 'Displays current time'

  def add_arguments(self, parser):
    parser.add_argument('path', type=str, help="Repository's path")

  def handle(self, *args, **kwargs):
    repo_path = kwargs['path']
    sync_hashes(repo_path)
