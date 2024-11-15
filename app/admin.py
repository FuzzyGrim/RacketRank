from django.contrib import admin

from app.models import Tournament, User

admin.site.register(User)
admin.site.register(Tournament)
