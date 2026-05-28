from django.contrib import admin
from .models import Skill, Project


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at", "participants_count")
    list_filter = ("status", "created_at")
    search_fields = (
        "name",
        "description",
        "owner__email",
        "owner__name",
        "owner__surname",
    )
    filter_horizontal = ("participants", "skills")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def participants_count(self, obj):
        return obj.participants.count()

    participants_count.short_description = "Участников"
