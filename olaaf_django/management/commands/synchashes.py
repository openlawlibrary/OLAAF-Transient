from django.core.management.base import BaseCommand

from olaaf_django.sync_hashes import sync_hashes


class Command(BaseCommand):
  help = """Traverse through all commits that have not yet been loaded into the database
and calculate and insert/update hashes of added, modified and deleted files"""

  def add_arguments(self, parser):
    parser.add_argument("library_root", type=str, help="Path to the library root")
    parser.add_argument("repos_data", type=str, help="json containing commits "
                        "sorted by branches and repositories which should be "
                        "inserted into the database")

  def handle(self, *args, **kwargs):
    library_root = kwargs["library_root"]
    repos_data = kwargs["repos_data"]
    sync_hashes(library_root, repos_data)
