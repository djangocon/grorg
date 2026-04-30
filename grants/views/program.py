from __future__ import annotations

import collections
import csv

from django import forms
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import FormView, ListView, TemplateView, UpdateView, View

from ..forms import (
    AllocationForm,
    ApproveApplicantForm,
    BaseApplyForm,
    ProgramEditForm,
    ProgramForm,
    QuestionForm,
    RejectApplicantForm,
    ResourceForm,
    ScoreForm,
)
from ..models import Answer, Applicant, Program, Question, Resource, Score


def _parse_integer_range(value):
    """Parses a 'low-high' string from a filter query param into (int, int)."""
    if not value or "-" not in value:
        return None
    low_str, _, high_str = value.partition("-")
    try:
        return int(low_str), int(high_str)
    except (TypeError, ValueError):
        return None


def index(request):
    return render(
        request,
        "index.html",
        {
            "accessible_programs": Program.objects.filter(users__pk=request.user.pk).order_by("name"),
        },
    )


class CreateProgram(FormView):
    """
    Allows staff users to create a new program.
    """

    template_name = "program-create.html"
    form_class = ProgramForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("account_login")
        if not request.user.is_staff:
            raise Http404("Staff access required")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        program = form.save(commit=False)
        program.created_by = self.request.user
        program.save()
        program.users.add(self.request.user)
        return redirect(program.urls.view)


class ProgramMixin:
    """
    Generic view base class which does things in context of a Program.
    """

    login_required = True

    def dispatch(self, *args, **kwargs):
        self.program_slug = kwargs.pop("program")
        self.program = Program.objects.get(slug=self.program_slug)
        if self.login_required and not self.request.user.is_authenticated:
            return redirect("account_login")
        if self.login_required and not self.program.user_allowed(self.request.user):
            raise Http404("You don't have access to this program")
        return super().dispatch(*args, **kwargs)

    def render_to_response(self, context, **kwargs):
        context["program"] = self.program
        context["user_allowed_program"] = self.program.user_allowed(self.request.user)
        context["user_can_manage"] = self.program.user_can_manage(self.request.user)
        return super().render_to_response(context, **kwargs)


class ProgramHome(ProgramMixin, TemplateView):
    """
    Homepage for a Program.
    """

    template_name = "program-home.html"

    def get_context_data(self):
        active_applicants = self.program.applicants_visible_to(self.request.user).exclude(status="rejected")
        users = list(self.program.users.all())
        for user in users:
            user.num_votes = (
                user.scores.filter(
                    applicant__program=self.program,
                    applicant__status__in=["pending", "accepted"],
                )
                .exclude(applicant__email=user.email)
                .count()
            )
        return {
            "num_applicants": active_applicants.count(),
            "num_scored": self.request.user.scores.filter(
                applicant__program=self.program,
                applicant__status__in=["pending", "accepted"],
            )
            .exclude(applicant__email=self.request.user.email)
            .count(),
            "users": users,
        }


class EditProgram(ProgramMixin, UpdateView):
    """
    Allows staff users to edit program settings.
    """

    template_name = "program-edit.html"
    form_class = ProgramEditForm
    model = Program

    def dispatch(self, *args, **kwargs):
        result = super().dispatch(*args, **kwargs)
        # If we got a redirect (e.g., to login), return it
        if hasattr(result, "status_code") and result.status_code in (301, 302):
            return result
        if not self.request.user.is_staff:
            raise Http404("Staff access required")
        return result

    def get_object(self):
        return self.program

    def get_success_url(self):
        return self.program.urls.view


class ProgramQuestions(ProgramMixin, FormView):
    """
    Allows editing of questions on a Program.
    """

    template_name = "program-questions.html"
    form_class = QuestionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.program.questions.order_by("order")
        return context

    def form_valid(self, form):
        question = form.save(commit=False)
        question.program = self.program
        question.save()
        return redirect(".")


class ProgramQuestionEdit(ProgramMixin, UpdateView):
    """
    Allows editing of a single question on a Program.
    """

    template_name = "program-question-edit.html"
    model = Question
    form_class = QuestionForm
    pk_url_kwarg = "question_id"

    def get_success_url(self):
        return self.program.urls.questions

    def post(self, request, question_id):
        # Possible deletion?
        if "delete" in request.POST:
            Question.objects.filter(pk=question_id).delete()
            return redirect(self.program.urls.questions)
        return UpdateView.post(self, request, question_id)


class ProgramApply(ProgramMixin, FormView):
    """
    Lets you apply for a program.
    """

    login_required = False
    template_name = "program-apply.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["program"] = self.program
        return kwargs

    def get_form_class(self):
        fields = collections.OrderedDict()
        for question in self.program.questions.order_by("order"):
            widget = forms.Textarea if question.type == "textarea" else None
            fields["question-%s" % question.id] = {
                "boolean": forms.BooleanField,
                "text": forms.CharField,
                "textarea": forms.CharField,
                "integer": forms.IntegerField,
            }[question.type](required=question.required, widget=widget, label=question.question)
        return type("ApplicationForm", (BaseApplyForm,), fields)

    def form_valid(self, form):
        applicant = Applicant.objects.create(
            program=self.program,
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            applied=timezone.now(),
        )
        for question in self.program.questions.order_by("order"):
            value = form.cleaned_data.get("question-%s" % question.id, None) or None
            if value:
                Answer.objects.create(
                    applicant=applicant,
                    question=question,
                    answer=value,
                )
        return redirect(self.program.urls.apply_success)


class ProgramApplySuccess(ProgramMixin, TemplateView):
    """
    Shown after you've applied.
    """

    login_required = False
    template_name = "program-apply-success.html"


class ProgramApplicants(ProgramMixin, ListView):
    """
    Shows applications to the program.
    """

    template_name = "program-applicants.html"
    context_object_name = "applicants"

    def get_queryset(self):
        # Work out sort
        sort_param = self.request.GET.get("sort", None)
        if sort_param == "score":
            self.sort = "score"
        elif sort_param == "scores":
            self.sort = "scores"
        else:
            self.sort = "applied"
        # Managers can view rejected applicants via ?status=rejected
        can_manage = self.program.user_can_manage(self.request.user)
        self.viewing_rejected = can_manage and self.request.GET.get("status") == "rejected"
        qs = self.program.applicants_visible_to(self.request.user)
        if self.viewing_rejected:
            qs = qs.filter(status="rejected")
        else:
            qs = qs.exclude(status="rejected")

        # Question-based filters (managers only); opt-in via Question.filterable.
        self.filter_questions = list(
            self.program.questions.filter(filterable=True, type__in=["boolean", "integer"]).order_by("order")
        )
        self.active_filters = {}
        if can_manage:
            for fq in self.filter_questions:
                filter_val = self.request.GET.get(f"q{fq.id}")
                if not filter_val:
                    continue
                if fq.type == "boolean" and filter_val in ("yes", "no"):
                    self.active_filters[fq.id] = filter_val
                    answer_value = "True" if filter_val == "yes" else "False"
                    matching_applicant_ids = Answer.objects.filter(question=fq, answer=answer_value).values_list(
                        "applicant_id", flat=True
                    )
                    qs = qs.filter(pk__in=matching_applicant_ids)
                elif fq.type == "integer":
                    parsed = _parse_integer_range(filter_val)
                    if parsed is None:
                        continue
                    low, high = parsed
                    matching_applicant_ids = []
                    for ans in Answer.objects.filter(question=fq):
                        try:
                            v = int(ans.answer)
                        except (TypeError, ValueError):
                            continue
                        if low <= v <= high:
                            matching_applicant_ids.append(ans.applicant_id)
                    self.active_filters[fq.id] = filter_val
                    qs = qs.filter(pk__in=matching_applicant_ids)

        applicants = list(qs.prefetch_related("scores").order_by("-applied"))
        for applicant in applicants:
            applicant.score_count = len(applicant.scores.all())
            applicant.has_scored = any(s.user_id == self.request.user.pk for s in applicant.scores.all())
            if applicant.has_scored:
                applicant.average_score = applicant.average_score()
            else:
                applicant.average_score = -1
        if self.sort == "score":
            applicants.sort(key=lambda a: a.average_score, reverse=True)
        elif self.sort == "scores":
            applicants.sort(key=lambda a: a.score_count)
        return applicants

    def get_context_data(self):
        context = super().get_context_data()
        context["sort"] = self.sort
        context["viewing_rejected"] = self.viewing_rejected
        # Build filter UI data for each filterable question.
        # Clicking an active filter clears it (toggle off); clicking another
        # value replaces it.
        base_params = {k: v for k, v in self.request.GET.items()}
        for fq in self.filter_questions:
            fq.active_filter = self.active_filters.get(fq.id, "")
            param_key = f"q{fq.id}"
            other_params = {k: v for k, v in base_params.items() if k != param_key}
            base_query = "&".join(f"{k}={v}" for k, v in other_params.items())

            def url_for(value, _other=base_query, _key=param_key, _active=fq.active_filter):
                # If this value is already active, link clears the param.
                params = _other
                if value != _active:
                    params = f"{params}&{_key}={value}" if params else f"{_key}={value}"
                return "?" + params if params else "?"

            if fq.type == "boolean":
                fq.filter_options = [
                    ("yes", "Yes", url_for("yes")),
                    ("no", "No", url_for("no")),
                ]
            elif fq.type == "integer":
                fq.filter_options = []
                for low, high in fq.integer_filter_ranges():
                    val = f"{low}-{high}"
                    label = str(low) if low == high else f"{low}–{high}"
                    fq.filter_options.append((val, label, url_for(val)))
            else:
                fq.filter_options = []
        context["filter_questions"] = self.filter_questions
        context["active_filters"] = self.active_filters
        return context


class ProgramApplicantsCsv(ProgramMixin, ListView):
    """
    Shows applications to the program.
    """

    context_object_name = "applicants"

    def get(self, request, *args, **kwargs):
        # Work out sort
        if self.request.GET.get("sort", None) == "score":
            self.sort = "score"
        else:
            self.sort = "applied"
        # Fetch applicants visible to this user, excluding rejected
        applicants = list(
            self.program.applicants_visible_to(self.request.user)
            .exclude(status="rejected")
            .prefetch_related("scores")
            .order_by("-applied")
        )
        for applicant in applicants:
            applicant.has_scored = applicant.scores.filter(user=self.request.user).exists()
            if applicant.has_scored:
                applicant.average_score = applicant.average_score()
            else:
                applicant.average_score = -1
        if self.sort == "score":
            applicants.sort(key=lambda a: a.average_score, reverse=True)

        # Prepare CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="applicants.csv"'

        writer = csv.writer(response)
        questions = self.program.questions.order_by("order")
        headers = ["Email", "Name", "Has Scored", "Average Score"]
        if self.request.user.is_staff:
            headers.append("Applied to Speak")
        headers += [question.question for question in questions.only("question")]
        writer.writerow(headers)

        for applicant in applicants:
            row = [
                applicant.email,
                applicant.name,
                applicant.has_scored,
                applicant.average_score,
            ]
            if self.request.user.is_staff:
                row.append(applicant.applied_to_speak)
            questions = self.program.questions.order_by("order")
            for question in questions:
                try:
                    value = (
                        Answer.objects.filter(
                            applicant=applicant,
                            question=question,
                        )
                        .only("answer")
                        .first()
                        .answer
                    )
                except Exception as e:
                    print(f"{e=}")
                    value = ""
                row += [value]

            writer.writerow(row)

        return response

    def get_context_data(self):
        context = super().get_context_data()
        context["sort"] = self.sort
        return context


class ProgramApplicantView(ProgramMixin, TemplateView):
    """
    Shows an individual application.
    """

    template_name = "applicant-view.html"

    def get(self, request, applicant_id):
        applicant = get_object_or_404(self.program.applicants_visible_to(self.request.user), pk=applicant_id)
        questions = list(self.program.questions.order_by("order"))
        for question in questions:
            question.answer = question.answers.filter(applicant=applicant).first()
        # See if we already scored this one
        score = Score.objects.filter(applicant=applicant, user=self.request.user).first()
        old_score = score.score if score else None
        if score:
            all_scores = Score.objects.filter(applicant=applicant)
            form = ScoreForm(instance=score)
        else:
            all_scores = None
        can_manage = self.program.user_can_manage(request.user)
        reject_form = RejectApplicantForm() if can_manage else None
        approve_form = ApproveApplicantForm() if can_manage else None
        if request.method == "POST":
            if "approve" in request.POST and can_manage:
                applicant.status = "accepted"
                applicant.save()
                return redirect(self.program.urls.applicants)
            elif "reject" in request.POST and can_manage:
                reject_form = RejectApplicantForm(request.POST)
                if reject_form.is_valid():
                    applicant.status = "rejected"
                    applicant.rejection_reason = reject_form.cleaned_data["rejection_reason"]
                    applicant.save()
                    return redirect(self.program.urls.applicants)
            else:
                form = ScoreForm(request.POST, instance=score)
                if form.is_valid():
                    new_score = form.save(commit=False)
                    new_score.applicant = applicant
                    new_score.user = self.request.user
                    if old_score and new_score.score != old_score:
                        new_score.score_history = ",".join(
                            [x.strip() for x in (new_score.score_history or "").split(",") if x.strip()]
                            + ["%.1f" % old_score]
                        )
                    new_score.save()
                    if "random_after" in request.POST:
                        return redirect(self.program.urls.score_random)
                    else:
                        return redirect(".")
        else:
            form = ScoreForm(instance=score)
        return self.render_to_response(
            {
                "applicant": applicant,
                "questions": questions,
                "all_scores": all_scores,
                "form": form,
                "reject_form": reject_form,
                "approve_form": approve_form,
            }
        )

    post = get


class RandomUnscoredApplicant(ProgramMixin, View):
    """
    Redirects to a random applicant that the user hasn't scored yet,
    or to the main list if they've scored everyone.
    """

    def get(self, request):
        applicant = (
            self.program.applicants_visible_to(self.request.user)
            .exclude(Q(scores__user=self.request.user) | Q(status="rejected"))
            .order_by("?")
            .first()
        )
        if applicant:
            return redirect(applicant.urls.view)
        else:
            return redirect(self.program.urls.applicants)


class ApplicantAllocations(ProgramMixin, FormView):
    """
    Allows editing of resources allocated to an applicant
    """

    form_class = AllocationForm
    template_name = "applicant-allocations.html"

    def dispatch(self, request, *args, **kwargs):
        applicant_id = kwargs.pop("applicant_id")
        self.program = get_object_or_404(Program, slug=kwargs["program"])
        self.applicant = get_object_or_404(self.program.applicants_visible_to(request.user), pk=applicant_id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["applicant"] = self.applicant
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["applicant"] = self.applicant
        context["allocations"] = self.applicant.allocations.order_by("resource__name")
        return context

    def form_valid(self, form):
        question = form.save(commit=False)
        question.applicant = self.applicant
        question.save()
        return redirect(".")

    def post(self, request, *args, **kwargs):
        # Possible deletion?
        if "delete" in request.POST:
            self.applicant.allocations.filter(pk=request.POST["delete_id"]).delete()
            return redirect(self.applicant.urls.allocations)
        return super().post(request, *args, **kwargs)


class ProgramResources(ProgramMixin, FormView):
    """
    Allows editing of resources available for a program.
    """

    form_class = ResourceForm
    template_name = "program-resources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resources"] = self.program.resources.order_by("name")
        return context

    def form_valid(self, form):
        question = form.save(commit=False)
        question.program = self.program
        question.save()
        return redirect(".")


class ProgramResourceEdit(ProgramMixin, UpdateView):
    """
    Allows editing of a single resource on a Program.
    """

    template_name = "program-resource-edit.html"
    model = Resource
    form_class = ResourceForm
    pk_url_kwarg = "resource_id"

    def get_success_url(self):
        return self.program.urls.resources

    def post(self, request, resource_id):
        # Possible deletion?
        if "delete" in request.POST:
            Resource.objects.filter(pk=resource_id).delete()
            return redirect(self.program.urls.resources)
        return UpdateView.post(self, request, resource_id)


class BulkUpdateSpeakerStatus(ProgramMixin, View):
    """
    Allows staff users to bulk update applied_to_speak status for applicants.
    """

    def dispatch(self, *args, **kwargs):
        result = super().dispatch(*args, **kwargs)
        if hasattr(self, "request") and not self.request.user.is_staff:
            raise Http404("Staff access required")
        return result

    def post(self, request):
        applicant_ids = request.POST.getlist("applicant_ids")
        action = request.POST.get("action")

        if applicant_ids and action in ("mark_speaker", "unmark_speaker"):
            new_status = action == "mark_speaker"
            Applicant.objects.filter(
                program=self.program,
                pk__in=applicant_ids,
            ).update(applied_to_speak=new_status)

        return redirect(self.program.urls.applicants)


class BulkRejectApplicants(ProgramMixin, View):
    """
    Allows superusers and program creators to bulk reject applicants.
    """

    def dispatch(self, *args, **kwargs):
        result = super().dispatch(*args, **kwargs)
        if hasattr(self, "request") and not self.program.user_can_manage(self.request.user):
            raise Http404("Access denied")
        return result

    def post(self, request):
        applicant_ids = request.POST.getlist("applicant_ids")
        action = request.POST.get("action", "reject")

        if applicant_ids:
            new_status = "pending" if action == "restore_pending" else "rejected"
            Applicant.objects.filter(
                program=self.program,
                pk__in=applicant_ids,
            ).update(status=new_status)

        if action == "restore_pending":
            return redirect(self.program.urls.applicants + "?status=rejected")
        return redirect(self.program.urls.applicants)


class BulkApproveApplicants(ProgramMixin, View):
    """
    Allows superusers and program creators to bulk approve applicants.
    """

    def dispatch(self, *args, **kwargs):
        result = super().dispatch(*args, **kwargs)
        if hasattr(self, "request") and not self.program.user_can_manage(self.request.user):
            raise Http404("Access denied")
        return result

    def post(self, request):
        applicant_ids = request.POST.getlist("applicant_ids")

        if applicant_ids:
            Applicant.objects.filter(
                program=self.program,
                pk__in=applicant_ids,
            ).update(status="accepted")

        return redirect(self.program.urls.applicants)
