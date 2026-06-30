from __future__ import annotations

from src.evidence.models import EvidenceGraph, EvidenceNode, STRONG, MODERATE


def _node_line(label: str, node: EvidenceNode) -> str:
    icon = "✓" if node.satisfied else "✗"
    bar = _bar(node.strength)
    return f"  {icon} {label:<22} {bar}  {node.confidence:<8}  {node.notes}"


def _bar(strength: float, width: int = 10) -> str:
    filled = int(round(strength * width))
    return "[" + "█" * filled + "·" * (width - filled) + f"] {strength:.2f}"


def print_evidence_graph(graph: EvidenceGraph) -> None:
    print(f"\n{'='*72}")
    print(f"  EVIDENCE GRAPH — {graph.candidate_name} ({graph.candidate_id})")
    print(f"  Role: {graph.job_title}")
    print(f"{'='*72}")

    print("\n  [TECHNICAL]")
    print(_node_line("Python",        graph.python))
    print(_node_line("Retrieval",     graph.retrieval))
    print(_node_line("Evaluation",    graph.evaluation))
    print(_node_line("MLOps",         graph.mlops))
    print(_node_line("Cloud",         graph.cloud))
    print(_node_line("Production AI", graph.production_ai))
    print(_node_line("Vector DB",     graph.vector_db))
    print(_node_line("Ranking",       graph.ranking))

    print("\n  [CAREER]")
    print(_node_line("Experience Yrs", graph.experience_years))
    print(_node_line("Seniority",      graph.seniority))
    print(_node_line("Career Growth",  graph.career_growth))
    print(_node_line("AI Experience",  graph.ai_experience))

    print("\n  [EDUCATION]")
    print(_node_line("Education",      graph.education))

    print("\n  [BEHAVIOR]")
    print(_node_line("GitHub",         graph.github_presence))
    print(_node_line("Certifications", graph.certifications))
    print(_node_line("Availability",   graph.availability))
    print(_node_line("Profile Quality",graph.profile_quality))

    print("\n  [RISK]")
    print(_node_line("Risk Flags",     graph.risk_flags))
    print()
