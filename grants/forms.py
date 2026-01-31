from __future__ import annotations

import secrets
import string

from django import forms
from django.utils.text import slugify

from .models import Allocation, Program, Question, Resource, Score


def generate_join_code():
    """Generate a random 8-character alphanumeric join code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


class QuestionForm(forms.ModelForm):
    class Meta:
        fields = ["question", "type", "required"]
        model = Question

    def clean_type(self):
        type = self.cleaned_data["type"]
        if (
            self.instance
            and type != self.instance.type
            and self.instance.answers.exists()
        ):
            raise forms.ValidationError("Cannot change once this question has answers")
        return type


class BaseApplyForm(forms.Form):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def __init__(self, program, *args, **kwargs):
        self.program = program
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if self.program.applicants.filter(email=email).exists():
            raise forms.ValidationError(
                "An application with that email address has already been submitted."
            )
        return email


class BulkLoadUploadForm(forms.Form):
    csv = forms.FileField(required=True)


class BulkLoadMapBaseForm(forms.Form):
    csv_id = forms.CharField(required=True, widget=forms.HiddenInput)

    def clean(self):
        # Ensure that no two mappings share the same column
        for name, value in self.cleaned_data.items():
            for name2, value2 in self.cleaned_data.items():
                if name == "csv_id" or name2 == "csv_id":
                    continue
                if name != name2 and value and value == value2:
                    raise forms.ValidationError(
                        "You cannot choose the same source ({}) for more than one question ({} and {}).".format(
                            value,
                            name,
                            name2,
                        )
                    )


class ScoreForm(forms.ModelForm):
    class Meta:
        fields = ["score", "comment"]
        model = Score

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score is not None and (score < 1 or score > 5):
            raise forms.ValidationError("Score must be between 1 and 5.")
        return score


class ResourceForm(forms.ModelForm):
    class Meta:
        fields = ["name", "type", "amount"]
        model = Resource


class AllocationForm(forms.ModelForm):
    class Meta:
        fields = ["resource", "amount"]
        model = Allocation

    def __init__(self, applicant, *args, **kwargs):
        self.applicant = applicant
        super().__init__(*args, **kwargs)
        self.fields["resource"].queryset = self.applicant.program.resources

    def clean_resource(self):
        resource = self.cleaned_data["resource"]
        if self.applicant.allocations.filter(resource=resource).exists():
            raise forms.ValidationError(
                "That resource is already allocated. Delete it if you wish to change it."
            )
        return resource


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["name"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-generate slug from name
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        while Program.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug
        # Auto-generate join code
        if not instance.join_code:
            instance.join_code = generate_join_code()
        if commit:
            instance.save()
        return instance
