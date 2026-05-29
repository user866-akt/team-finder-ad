from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("list/", views.ProjectListView.as_view(), name="project_list"),
    path("create-project/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="project_edit"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("skills/", views.SkillAutocompleteView.as_view(), name="skill_autocomplete"),
    path("<int:pk>/skills/add/", views.AddSkillToProjectView.as_view(), name="add_skill"),
    path(
        "<int:pk>/skills/<int:skill_pk>/remove/",
        views.RemoveSkillFromProjectView.as_view(),
        name="remove_skill",
    ),
    path(
        "<int:pk>/toggle-participate/",
        views.ToggleParticipateView.as_view(),
        name="toggle_participate",
    ),
    path(
        "<int:pk>/complete/",
        views.CompleteProjectView.as_view(),
        name="complete_project",
    ),
]
