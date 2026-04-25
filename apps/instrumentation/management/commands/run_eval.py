# run_eval.py
# Commande Django pour lancer l'évaluation depuis le terminal.
# Usage : python manage.py run_eval
#         python manage.py run_eval --prompt knowledge_assistant --version 2

from django.core.management.base import BaseCommand
from apps.instrumentation.eval.harness import EvalHarness


class Command(BaseCommand):
    help = "Lance l'évaluation du LLM sur les cas de test"

    def add_arguments(self, parser):
        parser.add_argument("--prompt",  default="knowledge_assistant")
        parser.add_argument("--version", type=int, default=1)

    def handle(self, *args, **options):
        name    = options["prompt"]
        version = options["version"]

        self.stdout.write(f"\n Evaluation : {name} v{version}\n")

        run = EvalHarness().run(prompt_name=name, version=version)

        if run is None:
            self.stdout.write(self.style.WARNING(
                "Aucun cas de test. Lance : python manage.py seed_demo"
            ))
            return

        pct = run.pass_rate * 100
        if pct >= 80:
            style = self.style.SUCCESS
        elif pct >= 60:
            style = self.style.WARNING
        else:
            style = self.style.ERROR

        self.stdout.write(style(
            f"\n  Reussis  : {run.passed_cases} / {run.total_cases}\n"
            f"  Taux     : {pct:.0f}%\n"
            f"  Latence  : {run.avg_latency_ms:.0f} ms\n"
            f"  Cout     : ${run.total_cost_usd:.6f}\n"
        ))