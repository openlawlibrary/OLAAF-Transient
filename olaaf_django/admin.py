from django.contrib import admin
from .models import Repository, Edition, Commit, Hash, Path

# Register your models here.
admin.site.register(Repository)
admin.site.register(Edition)
admin.site.register(Commit)
admin.site.register(Hash)
admin.site.register(Path)
