from django import forms
from .models import Defect, Attachment, Comment

class DefectForm(forms.ModelForm):
    class Meta:
        model = Defect
        fields = ["project", "stage", "title", "description", "priority", "status", "performer", "deadline"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "performer": forms.Select(attrs={"class": "form-select"}),
            "deadline": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "project": "Проект",
            "stage": "Этап",
            "title": "Название",
            "description": "Описание",
            "priority": "Приоритет",
            "status": "Статус",
            "performer": "Исполнитель",
            "deadline": "Срок выполнения",
        }

class DefectStatusForm(forms.Form):
    status = forms.ChoiceField(label="Статус", choices=Defect.STATUS_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {"file": "Файл"}

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"class": "form-control"}),
        }
        labels = {"text": "Комментарий"}