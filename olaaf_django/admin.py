from django.contrib import admin

from .models import Commit, Hash, Path, Publication, Repository

# Register your models here.
admin.site.register(Repository)
admin.site.register(Publication)
admin.site.register(Commit)
admin.site.register(Hash)
admin.site.register(Path)
