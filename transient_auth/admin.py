from django.contrib import admin
from .models import Commit, Hash

# Register your models here.
admin.site.register(Commit)
admin.site.register(Hash)
