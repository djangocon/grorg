from django.core.management.base import BaseCommand
from django.utils import timezone

from grants.models import Applicant, Program


SAMPLE_APPLICANTS = [
    ("Ada Lovelace", "ada@example.com"),
    ("Grace Hopper", "grace@example.com"),
    ("Alan Turing", "alan@example.com"),
    ("Margaret Hamilton", "margaret@example.com"),
    ("Linus Torvalds", "linus@example.com"),
    ("Guido van Rossum", "guido@example.com"),
    ("Barbara Liskov", "barbara@example.com"),
    ("Donald Knuth", "donald@example.com"),
    ("Hedy Lamarr", "hedy@example.com"),
    ("Tim Berners-Lee", "tim@example.com"),
]


class Command(BaseCommand):
    help = "Create 10 sample applicants for a program"

    def add_arguments(self, parser):
        parser.add_argument("program_slug", type=str)

    def handle(self, *args, **options):
        program = Program.objects.get(slug=options["program_slug"])
        now = timezone.now()
        created = 0
        for name, email in SAMPLE_APPLICANTS:
            _, was_created = Applicant.objects.get_or_create(
                program=program,
                email=email,
                defaults={"name": name, "applied": now},
            )
            if was_created:
                created += 1
                self.stdout.write(f"Created: {name}")
            else:
                self.stdout.write(f"Already exists: {name}")
        self.stdout.write(
            self.style.SUCCESS(f"Done. Created {created} new applicants.")
        )
