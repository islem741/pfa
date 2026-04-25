"""
python manage.py seed_demo
One command to set up the entire demo environment.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command


class Command(BaseCommand):
    help = "Set up the full demo: superuser + knowledge items + prompt template + eval cases"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== QueryForge Demo Setup ==="))

        # 1. Create superuser
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("✓ Superuser created: admin / admin123"))
        else:
            self.stdout.write("  Superuser 'admin' already exists.")

        # 2. Seed knowledge items
        call_command("seed_knowledge", verbosity=0)
        self.stdout.write(self.style.SUCCESS("✓ Knowledge base seeded (20 items)"))

        # 3. Create and activate prompt template
        self._setup_prompt()

        # 4. Load eval cases
        self._load_eval_cases()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Demo ready! ==="))
        self.stdout.write("  Admin panel: http://localhost:8000/admin/")
        self.stdout.write("  Login: admin / admin123")
        self.stdout.write("  API: POST /api/token/ to get JWT, then POST /api/v1/query/")

    def _setup_prompt(self):
        from apps.prompts.models import PromptTemplate, PromptVersion
        from apps.prompts.versioning import PromptVersionManager

        template, created = PromptTemplate.objects.get_or_create(
            name="knowledge_assistant",
            defaults={"description": "Main Q&A assistant with knowledge base access"},
        )

        if not template.versions.filter(is_active=True).exists():
            manager = PromptVersionManager()
            template_body = (
                "You are a helpful research assistant for QueryForge.\n"
                "Answer the user's question using the provided context.\n"
                "If the context does not contain the answer, say so clearly.\n\n"
                "Context:\n{{ context }}\n\n"
                "Respond ONLY in valid JSON with this exact structure:\n"
                '{"answer": "your answer here", "confidence": 0.85, "sources": ["source1"]}'
            )
            manager.create_version(
                template=template,
                template_body=template_body,
                role="system",
                token_budget=4096,
                notes="Initial version — created by seed_demo",
                activate=True,
            )
            self.stdout.write(self.style.SUCCESS("✓ Prompt template created and activated"))
        else:
            self.stdout.write("  Prompt template already active.")

    def _load_eval_cases(self):
        import json
        from pathlib import Path
        from apps.instrumentation.models import EvalCase

        fixtures_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "instrumentation" / "eval" / "fixtures" / "golden_cases.json"
        )
        if not fixtures_path.exists():
            self.stdout.write(self.style.WARNING("  Eval fixtures not found — skipping."))
            return

        with open(fixtures_path) as f:
            cases = json.load(f)

        created = 0
        for case in cases:
            _, was_created = EvalCase.objects.get_or_create(
                name=case["name"],
                defaults={
                    "input_query":     case.get("input_query", ""),
                    "expected_answer": case.get("expected_answer", ""),
                    "expected_schema": case.get("expected_schema"),
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Eval cases loaded ({created} new)"))
