#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.dataset import BENCHMARK_CASES
from evaluation.runner import (
    CaseResult,
    EvalStatus,
    run_evaluation,
    save_report_to_json,
)

# Terminal colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def status_badge(status: EvalStatus) -> str:
    if status == EvalStatus.PASSED:
        return f"{GREEN}[PASS]{RESET}"
    if status == EvalStatus.RESULT_MISMATCH:
        return f"{YELLOW}[MISMATCH]{RESET}"
    if status == EvalStatus.EXECUTION_ERROR:
        return f"{RED}[EXEC_ERR]{RESET}"
    if status == EvalStatus.VALIDATION_ERROR:
        return f"{RED}[VALID_ERR]{RESET}"
    return f"{RED}[CRASH]{RESET}"


def print_case_result(res: CaseResult, verbose: bool = False):
    badge = status_badge(res.status)
    time_str = f"{res.duration_ms:.0f}ms"
    diff_tag = f"[{res.difficulty.upper()}]"
    print(f" {badge} {diff_tag:<8} {res.case_id}: {res.question} ({time_str})")

    if verbose or res.status != EvalStatus.PASSED:
        if res.generated_sql:
            sql_preview = res.generated_sql.strip().replace("\n", " ")
            print(f"        {CYAN}Generated SQL:{RESET} {sql_preview}")
        if res.ground_truth_sql:
            gt_preview = res.ground_truth_sql.strip().replace("\n", " ")
            print(f"        {CYAN}Expected SQL: {RESET} {gt_preview}")

        if res.comparison_reason:
            print(f"        {YELLOW}Details:      {RESET} {res.comparison_reason}")
        if res.error_message:
            print(f"        {RED}Error:        {RESET} {res.error_message}")
        if verbose and res.actual_rows:
            print(f"        Actual Rows:   {res.actual_rows[:2]}")
        if verbose and res.expected_rows:
            print(f"        Expected Rows: {res.expected_rows[:2]}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark text-to-sql agent with execution accuracy (EX) against precomputed ground truth."
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard", "challenge", "all"],
        default="all",
        help="Filter benchmark cases by difficulty level",
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run a specific test case by ID (e.g. EASY-01)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed generated SQL and output for all cases",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval_report.json",
        help="Path to save JSON evaluation report (default: eval_report.json)",
    )
    args = parser.parse_args()

    selected_cases = BENCHMARK_CASES
    if args.case:
        selected_cases = [c for c in selected_cases if c.id.upper() == args.case.upper()]
        if not selected_cases:
            print(f"{RED}Error: Test case '{args.case}' not found.{RESET}")
            sys.exit(1)
    elif args.difficulty != "all":
        selected_cases = [c for c in selected_cases if c.difficulty == args.difficulty]

    print(f"\n{BOLD}{'=' * 75}{RESET}")
    print(f"{BOLD}  TEXT-TO-SQL EXECUTION ACCURACY EVALUATION BENCHMARK{RESET}")
    print(f"{BOLD}{'=' * 75}{RESET}")
    print(f"Running {len(selected_cases)} test cases against live agent...\n")

    summary = run_evaluation(
        cases=selected_cases,
        on_case_done=lambda res: print_case_result(res, verbose=args.verbose),
    )

    # Print summary statistics
    print(f"\n{BOLD}{'=' * 75}{RESET}")
    print(f"{BOLD}  BENCHMARK SUMMARY & DIAGNOSTICS{RESET}")
    print(f"{BOLD}{'=' * 75}{RESET}")
    print(f" Total Queries Evaluated: {summary.total_queries}")
    print(f" Passed (Exact Match):    {GREEN}{summary.passed}{RESET} ({summary.accuracy_percentage}%)")
    print(f" Result Mismatches:       {YELLOW}{summary.result_mismatches}{RESET}")
    print(f" Execution Errors:        {RED}{summary.execution_errors}{RESET}")
    print(f" Validation Errors:       {RED}{summary.validation_errors}{RESET}")
    print(f" Agent Crashes:           {RED}{summary.agent_crashes}{RESET}")

    print(f"\n{BOLD} Breakdown by Difficulty:{RESET}")
    for diff, stats in summary.by_difficulty.items():
        print(
            f"   • {diff.capitalize():<8}: {stats['passed']}/{stats['total']} passed ({stats['accuracy']}%)"
        )

    if summary.execution_errors > 0:
        print(f"\n{YELLOW}{BOLD}[!] DIAGNOSTIC INSIGHT:{RESET}")
        print(
            f"{YELLOW}   {summary.execution_errors} query(s) encountered runtime SQLite errors. "
            f"Because the agent currently lacks a 'diagnose_exec_error' node after execute_sql, "
            f"these queries could not be diagnosed or repaired at runtime.{RESET}"
        )

    save_report_to_json(summary, args.output)
    print(f"\n{CYAN}Detailed report saved to: {args.output}{RESET}\n")


if __name__ == "__main__":
    main()
