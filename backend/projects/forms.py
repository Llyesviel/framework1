from django import forms
from .models import Project, Stage, BuildObject

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description", "start_date", "end_date", "status", "members"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "members": forms.SelectMultiple(attrs={"class": "form-select"}),
        }
        labels = {
            "title": "Название",
            "description": "Описание",
            "start_date": "Дата начала",
            "end_date": "Дата окончания",
            "status": "Статус",
            "members": "Участники",
        }

class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
        }
        labels = {
            "title": "Название",
            "description": "Описание",
        }

class BuildObjectForm(forms.ModelForm):
    class Meta:
        model = BuildObject
        fields = ["title", "type", "address", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
        }
        labels = {
            "title": "Название объекта",
            "type": "Тип объекта",
            "address": "Адрес",
            "description": "Описание",
        }