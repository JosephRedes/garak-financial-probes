"""
Unified enterprise CLI — garak-enterprise-assess.

Runs financial and/or legal (and future domain) probe suites against
an LLM endpoint with a single command. Each domain produces its own
report; a cross-domain summary is generated when multiple domains run.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from garak_financial.buffs.encoding import (
    Base64Buff,
    LeetSpeakBuff,
    MixedCaseBuff,
    ROT13Buff,
    UnicodeHomoglyphBuff,
)
from garak_financial.buffs.financial import (
    AmountVariationBuff,
    FinancialEntityBuff,
    TimeframeVariationBuff,
)
from garak_financial.buffs.jailbreak import (
    JailbreakPrefixBuff,
    JailbreakSuffixBuff,
    MultiTurnJailbreakBuff,
    ObfuscatedJailbreakBuff,
)
from garak_financial.buffs.persona import PersonaVariationBuff, RolePlayBuff, UrgencyBuff
from garak_financial.judges.financial import FinancialJudge, HybridJudge
from garak_financial.probes import (
    AdvancedCompliance,
    AdvancedDisclosure,
    AdvancedImpartiality,
    AdvancedMisconduct,
    AdvancedSycophancy,
    Calculation,
    Compliance,
    Disclosure,
    Hallucination,
    Impartiality,
    Leakage,
    Misconduct,
    Sycophancy,
)
from garak_financial.reporting import ReportGenerator, ResultAggregator
from garak_financial.utils import LLMClientError, SecureLLMClient, mask_url
from garak_legal.probes import LEGAL_PROBES

console = Console()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain registry
# ---------------------------------------------------------------------------

FINANCIAL_PROBES = {
    "impartiality": Impartiality,
    "advanced-impartiality": AdvancedImpartiality,
    "misconduct": Misconduct,
    "advanced-misconduct": AdvancedMisconduct,
    "disclosure": Disclosure,
    "advanced-disclosure": AdvancedDisclosure,
    "hallucination": Hallucination,
    "compliance": Compliance,
    "advanced-compliance": AdvancedCompliance,
    "calculation": Calculation,
    "leakage": Leakage,
    "sycophancy": Sycophancy,
    "advanced-sycophancy": AdvancedSycophancy,
}

DOMAIN_REGISTRY: dict[str, dict] = {
    "financial": {
        "probes": FINANCIAL_PROBES,
        "label": "Financial Services",
        "description": "Investment advice, misconduct, disclosure, compliance, hallucination",
    },
    "legal": {
        "probes": LEGAL_PROBES,
        "label": "Legal",
        "description": "Unauthorized legal advice, privilege leakage, fabrication, litigation",
    },
    # Planned — uncomment as each domain ships:
    # "risk":    {"probes": RISK_PROBES,    "label": "Risk",              "description": "..."},
    # "hr":      {"probes": HR_PROBES,      "label": "HR",                "description": "..."},
    # "corpfin": {"probes": CORPFIN_PROBES, "label": "Corporate Finance", "description": "..."},
}

# ---------------------------------------------------------------------------
# Buff registry (shared across all domains)
# ---------------------------------------------------------------------------

BUFFS = {
    "base64": Base64Buff,
    "rot13": ROT13Buff,
    "leetspeak": LeetSpeakBuff,
    "homoglyph": UnicodeHomoglyphBuff,
    "mixedcase": MixedCaseBuff,
    "persona": PersonaVariationBuff,
    "roleplay": RolePlayBuff,
    "urgency": UrgencyBuff,
    "entity": FinancialEntityBuff,
    "amount": AmountVariationBuff,
    "timeframe": TimeframeVariationBuff,
    "jailbreak_prefix": JailbreakPrefixBuff,
    "jailbreak_suffix": JailbreakSuffixBuff,
    "multiturn": MultiTurnJailbreakBuff,
    "obfuscated": ObfuscatedJailbreakBuff,
}

BUFF_PRESETS = {
    "none": [],
    "light": ["base64", "persona"],
    "standard": ["base64", "leetspeak", "persona", "jailbreak_prefix"],
    "full": list(BUFFS.keys()),
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _parse_domains(domain_str: str) -> list[str]:
    """Parse and validate comma-separated domain names."""
    domains = [d.strip().lower() for d in domain_str.split(",")]
    invalid = [d for d in domains if d not in DOMAIN_REGISTRY]
    if invalid:
        console.print(f"[red]Unknown domains: {invalid}[/red]")
        console.print(f"[yellow]Available: {list(DOMAIN_REGISTRY.keys())}[/yellow]")
        sys.exit(1)
    return domains


def _resolve_probes(probes_str: str, domain_probes: dict) -> list[str]:
    """Resolve probe selection for a given domain's probe dict."""
    p = probes_str.lower()
    if p == "all":
        return [k for k in domain_probes if not k.startswith("advanced-")]
    if p == "full":
        return list(domain_probes.keys())
    if p == "advanced":
        return [k for k in domain_probes if k.startswith("advanced-")]
    # Comma-separated
    selected = [k.strip() for k in probes_str.split(",")]
    invalid = [k for k in selected if k not in domain_probes]
    if invalid:
        console.print(f"[red]Invalid probes for this domain: {invalid}[/red]")
        console.print(f"[yellow]Available: {list(domain_probes.keys())}[/yellow]")
        sys.exit(1)
    return selected


def _parse_buffs(buff_str: str) -> list[str]:
    buff_str = buff_str.lower().strip()
    if buff_str in BUFF_PRESETS:
        return BUFF_PRESETS[buff_str]
    selected = [b.strip() for b in buff_str.split(",")]
    invalid = [b for b in selected if b not in BUFFS]
    if invalid:
        console.print(f"[red]Invalid buffs: {invalid}[/red]")
        sys.exit(1)
    return selected


@click.command()
@click.option(
    "--domain",
    required=True,
    help=f"Domain(s) to assess: comma-separated from {list(DOMAIN_REGISTRY.keys())}.",
)
@click.option("--target-url", envvar="TARGET_LLM_URL", required=True,
              help="Target model endpoint (OpenAI-compatible).")
@click.option("--target-model", envvar="TARGET_LLM_MODEL", required=True,
              help="Target model name.")
@click.option("--judge-url", envvar="JUDGE_LLM_URL",
              help="Judge model endpoint. Defaults to target URL.")
@click.option("--judge-model", envvar="JUDGE_LLM_MODEL",
              help="Judge model name. Defaults to target model.")
@click.option("--output-dir", type=click.Path(), default="./assessment-reports",
              help="Output directory for reports.")
@click.option("--probes", default="all",
              help="all (standard), full (all incl. advanced), advanced, or comma-separated.")
@click.option("--buffs", "buff_selection", default="none",
              help="Buff preset: none, light, standard, full, or comma-separated.")
@click.option("--max-prompts", type=int, default=None,
              help="Limit total prompts per domain (useful for testing).")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.option("--dry-run", is_flag=True,
              help="Show what would be tested without making API calls.")
@click.option(
    "--format", "output_format",
    type=click.Choice(["markdown", "html", "both"], case_sensitive=False),
    default="markdown", show_default=True,
    help="Report output format.",
)
@click.option("--auth-header", default="Authorization", show_default=True,
              help="HTTP header name for API key authentication.")
def main(
    domain: str,
    target_url: str,
    target_model: str,
    judge_url: Optional[str],
    judge_model: Optional[str],
    output_dir: str,
    probes: str,
    buff_selection: str,
    max_prompts: Optional[int],
    verbose: bool,
    dry_run: bool,
    output_format: str,
    auth_header: str,
) -> None:
    """
    Run enterprise LLM security assessment across one or more domains.

    \b
    Examples:
      # Legal domain assessment
      garak-enterprise-assess --domain legal \\
        --target-url http://localhost:11434/v1 --target-model llama3:70b

      # Multi-domain with a cloud judge
      garak-enterprise-assess --domain financial,legal \\
        --target-url http://localhost:11434/v1 --target-model llama3:70b \\
        --judge-url https://api.openai.com/v1 --judge-model gpt-4o

      # Advanced probes only, HTML report
      garak-enterprise-assess --domain legal \\
        --target-url ... --target-model ... \\
        --probes advanced --format html
    """
    _setup_logging(verbose)

    domains = _parse_domains(domain)
    judge_url = judge_url or target_url
    judge_model = judge_model or target_model
    selected_buffs = _parse_buffs(buff_selection)
    output_path = Path(output_dir)

    # Display configuration
    _display_config(domains, target_url, target_model, judge_url, judge_model,
                    probes, selected_buffs, output_dir)

    if dry_run:
        _display_dry_run(domains, probes, selected_buffs)
        return

    # Run each domain sequentially
    domain_reports: dict[str, Path] = {}
    try:
        target_client = SecureLLMClient(
            base_url=target_url, api_key_env_var="TARGET_API_KEY",
            auth_header=auth_header,
        )
        judge_client = SecureLLMClient(
            base_url=judge_url, api_key_env_var="JUDGE_API_KEY",
            auth_header=auth_header,
        )
        llm_judge = FinancialJudge(client=judge_client, model=judge_model)
        hybrid_judge = HybridJudge(llm_judge=llm_judge)
        buff_instances = [BUFFS[b]() for b in selected_buffs]

        for domain_name in domains:
            domain_info = DOMAIN_REGISTRY[domain_name]
            domain_probes = domain_info["probes"]
            selected_probe_keys = _resolve_probes(probes, domain_probes)

            console.print(f"\n[bold cyan]── {domain_info['label']} Domain ──[/bold cyan]")

            report_path = _run_domain_assessment(
                domain_name=domain_name,
                domain_label=domain_info["label"],
                probe_keys=selected_probe_keys,
                domain_probes=domain_probes,
                target_client=target_client,
                target_model=target_model,
                hybrid_judge=hybrid_judge,
                buff_instances=buff_instances,
                output_dir=output_path,
                max_prompts=max_prompts,
                output_format=output_format,
            )
            domain_reports[domain_name] = report_path

        target_client.close()
        judge_client.close()

    except LLMClientError as e:
        console.print(f"[red]LLM API Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)

    # Cross-domain summary
    if len(domains) > 1:
        _display_cross_domain_summary(domain_reports)


def _display_config(
    domains: list[str], target_url: str, target_model: str,
    judge_url: str, judge_model: str, probes: str,
    buffs: list[str], output_dir: str,
) -> None:
    table = Table(title="Enterprise Assessment Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Domains", ", ".join(
        DOMAIN_REGISTRY[d]["label"] for d in domains
    ))
    table.add_row("Target Endpoint", mask_url(target_url))
    table.add_row("Target Model", target_model)
    table.add_row("Judge Endpoint", mask_url(judge_url))
    table.add_row("Judge Model", judge_model)
    table.add_row("Probes", probes)
    table.add_row("Buffs", ", ".join(buffs) if buffs else "none")
    table.add_row("Output Directory", output_dir)
    console.print(table)


def _display_dry_run(domains: list[str], probes: str, buffs: list[str]) -> None:
    for domain_name in domains:
        domain_info = DOMAIN_REGISTRY[domain_name]
        domain_probes = domain_info["probes"]
        selected = _resolve_probes(probes, domain_probes)

        table = Table(title=f"Dry Run — {domain_info['label']} Domain")
        table.add_column("Probe", style="cyan")
        table.add_column("Prompts", justify="right", style="green")

        total = 0
        for key in selected:
            probe_class = domain_probes[key]
            probe = cast(object, probe_class())
            count = len(probe.prompts)  # type: ignore[attr-defined]
            table.add_row(key, str(count))
            total += count

        table.add_row("", "")
        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")
        console.print(table)

    if buffs:
        console.print("\n[cyan]Buffs to apply:[/cyan]")
        for buff in buffs:
            console.print(f"  • {buff}")

    console.print("\n[yellow]Dry run complete. No API calls were made.[/yellow]")


def _run_domain_assessment(
    domain_name: str,
    domain_label: str,
    probe_keys: list[str],
    domain_probes: dict,
    target_client: SecureLLMClient,
    target_model: str,
    hybrid_judge: HybridJudge,
    buff_instances: list,
    output_dir: Path,
    max_prompts: Optional[int],
    output_format: str,
) -> Path:
    """Run assessment for a single domain and return the primary report path."""
    from garak_financial.cli import apply_buffs

    aggregator = ResultAggregator(
        model_name=target_model,
        endpoint=target_client.base_url,
        judge_model="",
    )

    # Collect prompts
    all_prompts = []
    for key in probe_keys:
        probe_class = domain_probes[key]
        probe = cast(object, probe_class())
        for base_prompt in probe.prompts:  # type: ignore[attr-defined]
            if buff_instances:
                for aug_prompt, buff_name in apply_buffs(base_prompt, buff_instances):
                    all_prompts.append((key, aug_prompt, buff_name))
            else:
                all_prompts.append((key, base_prompt, "original"))

    if max_prompts and len(all_prompts) > max_prompts:
        all_prompts = all_prompts[:max_prompts]

    console.print(f"[green]  {len(all_prompts)} prompts to test[/green]")

    # Run prompts
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"  Assessing {domain_label}...", total=len(all_prompts))

        for probe_key, prompt, buff_name in all_prompts:
            progress.update(task, description=f"  {probe_key} [{buff_name}]")
            try:
                response = target_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=target_model,
                )
                judgment = hybrid_judge.evaluate(
                    prompt=prompt, response=response.content, category=probe_key,
                )
                aggregator.add_judgment(
                    category=probe_key, prompt=prompt,
                    response=response.content, judgment=judgment,
                )
            except LLMClientError as e:
                logger.warning("Error on prompt: %s", e)
                aggregator.result.errors.append(str(e))
            progress.advance(task)

    result = aggregator.finalize()
    generator = ReportGenerator(result)
    domain_output = output_dir / domain_name
    domain_output.mkdir(parents=True, exist_ok=True)

    primary_path: Path
    if output_format in ("markdown", "both"):
        primary_path = generator.save(domain_output)
    if output_format in ("html", "both"):
        primary_path = generator.save_html(domain_output)
    if output_format == "markdown":
        primary_path = generator.save(domain_output)

    generator.save_json(domain_output)

    console.print(f"  [green]✓ Report saved: {primary_path}[/green]")
    return primary_path


def _display_cross_domain_summary(domain_reports: dict[str, Path]) -> None:
    console.print()
    table = Table(title="Cross-Domain Assessment Summary")
    table.add_column("Domain", style="cyan")
    table.add_column("Report", style="green")

    for domain_name, report_path in domain_reports.items():
        label = DOMAIN_REGISTRY[domain_name]["label"]
        table.add_row(label, str(report_path))

    console.print(table)
    console.print(Panel(
        "[bold green]All domain assessments complete.[/bold green]\n\n"
        "Review each domain report for detailed findings.",
        title="Done",
    ))


if __name__ == "__main__":
    main()
