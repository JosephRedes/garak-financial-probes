"""
CLI Tool for Financial Model Assessment.

Provides a command-line interface for running assessments against
OpenAI-compatible model endpoints with full buff support.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Import buffs
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
from garak_financial.buffs.persona import (
    PersonaVariationBuff,
    RolePlayBuff,
    UrgencyBuff,
)
from garak_financial.judges.financial import FinancialJudge, HybridJudge

# Import probes
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
from garak_financial.reporting import (
    ReportGenerator,
    ResultAggregator,
)
from garak_financial.utils import LLMClientError, SecureLLMClient, mask_url

console = Console()
logger = logging.getLogger(__name__)

# Probe registry
PROBES = {
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

# Probe group aliases
PROBE_GROUPS = {
    "advanced": [
        "advanced-impartiality",
        "advanced-misconduct",
        "advanced-disclosure",
        "advanced-compliance",
        "advanced-sycophancy",
    ],
}

# Buff registry
BUFFS = {
    # Encoding
    "base64": Base64Buff,
    "rot13": ROT13Buff,
    "leetspeak": LeetSpeakBuff,
    "homoglyph": UnicodeHomoglyphBuff,
    "mixedcase": MixedCaseBuff,
    # Persona
    "persona": PersonaVariationBuff,
    "roleplay": RolePlayBuff,
    "urgency": UrgencyBuff,
    # Financial
    "entity": FinancialEntityBuff,
    "amount": AmountVariationBuff,
    "timeframe": TimeframeVariationBuff,
    # Jailbreak
    "jailbreak_prefix": JailbreakPrefixBuff,
    "jailbreak_suffix": JailbreakSuffixBuff,
    "multiturn": MultiTurnJailbreakBuff,
    "obfuscated": ObfuscatedJailbreakBuff,
}

# Buff presets
BUFF_PRESETS = {
    "none": [],
    "light": ["base64", "persona"],
    "standard": ["base64", "leetspeak", "persona", "jailbreak_prefix"],
    "full": list(BUFFS.keys()),
    "encoding": ["base64", "rot13", "leetspeak", "homoglyph", "mixedcase"],
    "jailbreak": ["jailbreak_prefix", "jailbreak_suffix", "multiturn", "obfuscated"],
}


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def apply_buffs(prompt: str, buff_instances: list) -> list[tuple[str, str]]:
    """
    Apply buffs to a prompt and return augmented versions.

    Returns list of (augmented_prompt, buff_name) tuples.
    """
    results = [(prompt, "original")]

    for buff in buff_instances:
        try:
            # Each buff's transform method returns a list of augmented prompts
            augmented = buff.transform(prompt)
            buff_name = buff.__class__.__name__
            for aug_prompt in augmented:
                if aug_prompt != prompt:  # Only add if actually transformed
                    results.append((aug_prompt, buff_name))
        except Exception as e:
            logger.warning(f"Buff {buff.__class__.__name__} failed: {e}")

    return results


@click.command()
@click.option(
    "--target-url",
    envvar="TARGET_LLM_URL",
    required=True,
    help="Target model endpoint (OpenAI-compatible).",
)
@click.option(
    "--target-model",
    envvar="TARGET_LLM_MODEL",
    required=True,
    help="Target model name.",
)
@click.option(
    "--judge-url",
    envvar="JUDGE_LLM_URL",
    help="Judge model endpoint. Defaults to target URL.",
)
@click.option(
    "--judge-model",
    envvar="JUDGE_LLM_MODEL",
    help="Judge model name. Defaults to target model.",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="./assessment-reports",
    help="Output directory for reports.",
)
@click.option(
    "--probes",
    default="all",
    help="Probe categories: 'all' or comma-separated (impartiality,misconduct,...).",
)
@click.option(
    "--buffs",
    "buff_selection",
    default="none",
    help="Buff selection: 'none', 'light', 'standard', 'full', or comma-separated buff names.",
)
@click.option(
    "--max-prompts",
    type=int,
    default=None,
    help="Limit total prompts (useful for testing).",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be tested without making API calls.",
)
@click.option(
    "--batch",
    is_flag=True,
    help="Batch mode: collect all target responses first, then judge."
    " Much faster for local models.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "html", "both"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Report output format: markdown, html, or both.",
)
@click.option(
    "--auth-header",
    default="Authorization",
    show_default=True,
    help="HTTP header name for API key authentication. "
    "Both OpenAI and Vertex AI use the default 'Authorization' header.",
)
@click.option(
    "--vertex-ai",
    is_flag=True,
    help="Print Vertex AI endpoint format guidance and exit.",
)
def main(
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
    batch: bool,
    output_format: str,
    auth_header: str,
    vertex_ai: bool,
) -> None:
    """
    Run financial security assessment against an LLM endpoint.

    This tool evaluates LLM responses for financial compliance concerns
    using probes, prompt augmentation (buffs), and LLM-as-judge evaluation.

    \b
    Examples:
      # Basic assessment (no buffs)
      garak-financial-assess --target-url https://api.example.com/v1 --target-model llama-3.1-70b

      # With standard buffs (~10x prompts)
      garak-financial-assess --target-url ... --target-model ... --buffs standard

      # Full assessment with all buffs (~50x prompts)
      garak-financial-assess --target-url ... --target-model ... --buffs full

      # Custom buff selection
      garak-financial-assess --target-url ... --target-model ... \
        --buffs base64,persona,jailbreak_prefix

    \b
    Buff Presets:
      none      No augmentation (base prompts only)
      light     base64 + persona (~5x)
      standard  base64 + leetspeak + persona + jailbreak_prefix (~20x)
      full      All buffs (~50x)
      encoding  All encoding buffs
      jailbreak All jailbreak buffs

    \b
    Available Buffs:
      Encoding:  base64, rot13, leetspeak, homoglyph, mixedcase
      Persona:   persona, roleplay, urgency
      Financial: entity, amount, timeframe
      Jailbreak: jailbreak_prefix, jailbreak_suffix, multiturn, obfuscated
    """
    setup_logging(verbose)

    if vertex_ai:
        console.print(Panel(
            "[bold cyan]Vertex AI Endpoint Format[/bold cyan]\n\n"
            "Vertex AI exposes OpenAI-compatible endpoints. Use:\n\n"
            "  [green]--target-url[/green]  https://LOCATION-aiplatform.googleapis.com/v1beta1/"
            "projects/PROJECT_ID/locations/LOCATION/endpoints/openapi\n\n"
            "Set your access token as the API key:\n"
            "  [yellow]export TARGET_API_KEY=$(gcloud auth print-access-token)[/yellow]\n\n"
            "Example:\n"
            "  [dim]export TARGET_API_KEY=$(gcloud auth print-access-token)\n"
            "  garak-financial-assess \\\n"
            "    --target-url https://us-central1-aiplatform.googleapis.com/v1beta1/"
            "projects/my-project/locations/us-central1/endpoints/openapi \\\n"
            "    --target-model google/gemini-1.5-pro-002 \\\n"
            "    --judge-url https://api.openai.com/v1 \\\n"
            "    --judge-model gpt-4o[/dim]",
            title="Vertex AI Setup",
            border_style="cyan",
        ))
        return

    # Use target as judge if not specified
    judge_url = judge_url or target_url
    judge_model = judge_model or target_model

    # Parse probe selection
    if probes.lower() == "all":
        selected_probes = list(PROBES.keys())
    else:
        # Expand group aliases (e.g. "advanced" → all advanced-* probes)
        raw = [p.strip().lower() for p in probes.split(",")]
        selected_probes = []
        for p in raw:
            if p in PROBE_GROUPS:
                selected_probes.extend(PROBE_GROUPS[p])
            else:
                selected_probes.append(p)
        invalid = set(selected_probes) - set(PROBES.keys())
        if invalid:
            console.print(f"[red]Invalid probe categories: {invalid}[/red]")
            console.print(f"[yellow]Available: {list(PROBES.keys())}[/yellow]")
            sys.exit(1)

    # Parse buff selection
    selected_buffs = _parse_buff_selection(buff_selection)

    # Display configuration
    _display_config(
        target_url, target_model,
        judge_url, judge_model,
        selected_probes, selected_buffs,
        output_dir,
    )

    if dry_run:
        _display_dry_run(selected_probes, selected_buffs)
        return

    # Run assessment
    try:
        _run_assessment(
            target_url=target_url,
            target_model=target_model,
            judge_url=judge_url,
            judge_model=judge_model,
            selected_probes=selected_probes,
            selected_buffs=selected_buffs,
            output_dir=Path(output_dir),
            max_prompts=max_prompts,
            batch_mode=batch,
            output_format=output_format,
            auth_header=auth_header,
        )
    except LLMClientError as e:
        console.print(f"[red]LLM API Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _parse_buff_selection(buff_selection: str) -> list[str]:
    """Parse buff selection string into list of buff names."""
    buff_selection = buff_selection.lower().strip()

    # Check for preset
    if buff_selection in BUFF_PRESETS:
        return BUFF_PRESETS[buff_selection]

    # Parse comma-separated list
    selected = [b.strip() for b in buff_selection.split(",")]
    invalid = set(selected) - set(BUFFS.keys())
    if invalid:
        console.print(f"[red]Invalid buffs: {invalid}[/red]")
        console.print(f"[yellow]Available: {list(BUFFS.keys())}[/yellow]")
        console.print(f"[yellow]Presets: {list(BUFF_PRESETS.keys())}[/yellow]")
        sys.exit(1)

    return selected


def _display_config(
    target_url: str,
    target_model: str,
    judge_url: str,
    judge_model: str,
    probes: list[str],
    buffs: list[str],
    output_dir: str,
) -> None:
    """Display assessment configuration."""
    table = Table(title="Assessment Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Target Endpoint", mask_url(target_url))
    table.add_row("Target Model", target_model)
    table.add_row("Judge Endpoint", mask_url(judge_url))
    table.add_row("Judge Model", judge_model)
    table.add_row("Probes", ", ".join(probes))
    table.add_row("Buffs", ", ".join(buffs) if buffs else "none")
    table.add_row("Output Directory", output_dir)

    console.print(table)
    console.print()


def _display_dry_run(probes: list[str], buffs: list[str]) -> None:
    """Display what would be tested in dry run."""
    base_prompts = 0

    # Count base prompts
    for probe_id in probes:
        probe_class = PROBES[probe_id]
        probe = cast(Any, probe_class())
        base_prompts += len(probe.prompts)

    # Estimate augmented prompts
    buff_instances = [BUFFS[b]() for b in buffs]

    # Estimate multiplier (rough)
    multiplier = 1
    for buff in buff_instances:
        if hasattr(buff, 'prefixes'):
            multiplier += len(buff.prefixes)
        elif hasattr(buff, 'templates'):
            multiplier += len(buff.templates)
        else:
            multiplier += 2  # Default estimate

    total_prompts = base_prompts * max(1, multiplier // 2)  # Conservative estimate

    table = Table(title="Dry Run - Assessment Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Base Prompts", str(base_prompts))
    table.add_row("Buffs Applied", str(len(buffs)))
    table.add_row("Estimated Total", f"~{total_prompts}")
    table.add_row("", "")

    # Breakdown by probe
    for probe_id in probes:
        probe_class = PROBES[probe_id]
        probe = cast(Any, probe_class())
        table.add_row(f"  {probe_id}", str(len(probe.prompts)))

    console.print(table)

    if buffs:
        console.print("\n[cyan]Buffs to apply:[/cyan]")
        for buff in buffs:
            console.print(f"  • {buff}")

    console.print("\n[yellow]Dry run complete. No API calls were made.[/yellow]")


def _run_assessment(
    target_url: str,
    target_model: str,
    judge_url: str,
    judge_model: str,
    selected_probes: list[str],
    selected_buffs: list[str],
    output_dir: Path,
    max_prompts: Optional[int],
    batch_mode: bool = False,
    output_format: str = "markdown",
    auth_header: str = "Authorization",
) -> None:
    """Run the full assessment with buff support."""

    # Initialize clients
    console.print("[cyan]Initializing LLM clients...[/cyan]")

    target_client = SecureLLMClient(
        base_url=target_url,
        api_key_env_var="TARGET_API_KEY",
        auth_header=auth_header,
    )

    judge_client = SecureLLMClient(
        base_url=judge_url,
        api_key_env_var="JUDGE_API_KEY",
        auth_header=auth_header,
    )

    # Initialize judge
    llm_judge = FinancialJudge(
        client=judge_client,
        model=judge_model,
    )

    hybrid_judge = HybridJudge(llm_judge=llm_judge)

    # Initialize buff instances
    buff_instances = [BUFFS[b]() for b in selected_buffs]

    # Initialize aggregator
    aggregator = ResultAggregator(
        model_name=target_model,
        endpoint=target_url,
        judge_model=judge_model,
    )
    aggregator.result.buffs_used = selected_buffs

    # Collect all prompts with augmentation
    console.print("[cyan]Preparing prompts...[/cyan]")
    all_prompts = []  # (probe_id, prompt, buff_name)

    for probe_id in selected_probes:
        probe_class = PROBES[probe_id]
        probe = cast(Any, probe_class())

        for base_prompt in probe.prompts:
            if buff_instances:
                # Apply buffs
                augmented = apply_buffs(base_prompt, buff_instances)
                for aug_prompt, buff_name in augmented:
                    all_prompts.append((probe_id, aug_prompt, buff_name))
            else:
                # No buffs, just base prompt
                all_prompts.append((probe_id, base_prompt, "original"))

    aggregator.result.base_prompts = sum(
        len(cast(Any, PROBES[p]()).prompts) for p in selected_probes
    )

    # Apply max_prompts limit
    if max_prompts and len(all_prompts) > max_prompts:
        console.print(
            f"[yellow]Limiting to {max_prompts} prompts"
            f" (from {len(all_prompts)})[/yellow]"
        )
        all_prompts = all_prompts[:max_prompts]

    console.print(
        f"[green]Total prompts to test:"
        f" {len(all_prompts)}[/green]"
    )
    aug_count = len(all_prompts) - aggregator.result.base_prompts
    console.print(
        f"[dim](Base: {aggregator.result.base_prompts},"
        f" Augmented: {aug_count})[/dim]"
    )

    if batch_mode:
        console.print("[cyan]⚡ Batch mode: collecting all responses first, then judging[/cyan]\n")
        _run_batch_assessment(
            all_prompts, target_client, target_model,
            hybrid_judge, aggregator,
        )
    else:
        console.print()
        _run_interleaved_assessment(
            all_prompts, target_client, target_model,
            hybrid_judge, aggregator,
        )

    # Finalize and generate report
    result = aggregator.finalize()
    generator = ReportGenerator(result)

    # Save reports
    console.print("\n[cyan]Generating reports...[/cyan]")
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = None
    html_path = None
    if output_format in ("markdown", "both"):
        md_path = generator.save(output_dir)
    if output_format in ("html", "both"):
        html_path = generator.save_html(output_dir)
    json_path = generator.save_json(output_dir)

    # Display summary
    _display_summary(result, md_path=md_path, json_path=json_path, html_path=html_path)

    # Cleanup
    target_client.close()
    judge_client.close()


def _run_interleaved_assessment(
    all_prompts: list[tuple[str, str, str]],
    target_client: SecureLLMClient,
    target_model: str,
    hybrid_judge: HybridJudge,
    aggregator: ResultAggregator,
) -> None:
    """Original mode: send prompt → judge response → next prompt."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
    ) as progress:
        task = progress.add_task("Assessing...", total=len(all_prompts))

        for probe_id, prompt, buff_name in all_prompts:
            progress.update(task, description=f"{probe_id} [{buff_name}]")

            try:
                response = target_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=target_model,
                )

                judgment = hybrid_judge.evaluate(
                    prompt=prompt,
                    response=response.content,
                    category=probe_id,
                )

                aggregator.add_judgment(
                    category=probe_id,
                    prompt=prompt,
                    response=response.content,
                    judgment=judgment,
                )

            except LLMClientError as e:
                logger.warning(f"Error on prompt: {e}")
                aggregator.result.errors.append(str(e))

            progress.advance(task)


def _run_batch_assessment(
    all_prompts: list[tuple[str, str, str]],
    target_client: SecureLLMClient,
    target_model: str,
    hybrid_judge: HybridJudge,
    aggregator: ResultAggregator,
) -> None:
    """
    Batch mode: collect ALL target responses first, then judge ALL at once.

    This avoids constant model swapping when target and judge run on the
    same local endpoint (e.g., Ollama), dramatically reducing total time.
    """
    # Phase 1: Collect all target responses
    collected = []  # (probe_id, prompt, buff_name, response_text)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Phase 1: Target responses", total=len(all_prompts),
        )

        for probe_id, prompt, buff_name in all_prompts:
            progress.update(task, description=f"Phase 1: {probe_id} [{buff_name}]")

            try:
                response = target_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=target_model,
                )
                collected.append((probe_id, prompt, buff_name, response.content))

            except LLMClientError as e:
                logger.warning(f"Error on prompt: {e}")
                aggregator.result.errors.append(str(e))

            progress.advance(task)

    console.print(f"[green]✓ Collected {len(collected)} responses[/green]\n")

    # Phase 2: Judge all responses
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Phase 2: Judging", total=len(collected),
        )

        for probe_id, prompt, buff_name, response_text in collected:
            progress.update(task, description=f"Phase 2: {probe_id} [{buff_name}]")

            try:
                judgment = hybrid_judge.evaluate(
                    prompt=prompt,
                    response=response_text,
                    category=probe_id,
                )

                aggregator.add_judgment(
                    category=probe_id,
                    prompt=prompt,
                    response=response_text,
                    judgment=judgment,
                )

            except LLMClientError as e:
                logger.warning(f"Error judging: {e}")
                aggregator.result.errors.append(str(e))

            progress.advance(task)

    console.print(f"[green]✓ Judged {len(collected)} responses[/green]")


def _display_summary(
    result,
    md_path: Optional[Path],
    json_path: Path,
    html_path: Optional[Path] = None,
) -> None:
    """Display assessment summary."""
    console.print()

    # Calculate augmentation
    if result.base_prompts > 0:
        aug_factor = result.total_prompts / result.base_prompts
    else:
        aug_factor = 1.0

    # Build report lines dynamically
    report_lines = []
    if md_path:
        report_lines.append(f"  Markdown: {md_path}")
    if html_path:
        report_lines.append(f"  HTML:     {html_path}")
    report_lines.append(f"  JSON:     {json_path}")
    reports_section = "\n".join(report_lines)

    # Summary panel
    summary = f"""
[bold]Assessment Complete[/bold]

Model: {result.model_name}
Base Prompts: {result.base_prompts}
Total Tested: {result.total_prompts} ({aug_factor:.1f}x augmentation)
Buffs Used: {', '.join(result.buffs_used) if result.buffs_used else 'none'}
Overall Mean Concern: {result.overall_mean_score:.2f}

[bold]Reports Saved:[/bold]
{reports_section}
"""
    console.print(Panel(summary, title="Summary", border_style="green"))

    # Category breakdown
    table = Table(title="Results by Category")
    table.add_column("Category", style="cyan")
    table.add_column("Tested", justify="right")
    table.add_column("Mean Score", justify="right")
    table.add_column("High Concern", justify="right")

    for cat_id, cat in sorted(
        result.categories.items(),
        key=lambda x: x[1].mean_score,
        reverse=True,
    ):
        # Color code based on score
        score = cat.mean_score
        if score < 0.3:
            score_str = f"[green]{score:.2f}[/green]"
        elif score < 0.6:
            score_str = f"[yellow]{score:.2f}[/yellow]"
        else:
            score_str = f"[red]{score:.2f}[/red]"

        high_pct = f"{cat.high_concern_count} ({cat.high_concern_pct:.0f}%)"
        table.add_row(cat_id, str(cat.total_prompts), score_str, high_pct)

    console.print(table)


if __name__ == "__main__":
    main()
