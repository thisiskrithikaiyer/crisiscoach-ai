"""Evaluates whether the orchestrator routed messages to the correct agent."""
from crisiscoach.orchestrator.router import classify_intent
from crisiscoach.orchestrator.state import CrisisCoachState
from langchain_core.messages import HumanMessage


def score_routing(test_cases: list[dict]) -> dict:
    """
    test_cases: [{"input": "...", "expected_intent": "..."}]
    Returns accuracy metrics.
    """
    correct = 0
    results = []
    for case in test_cases:
        state: CrisisCoachState = {
            "messages": [HumanMessage(content=case["input"])],
            "user_id": "eval",
            "intent": "", "agent": "",
            "days_since_layoff": None, "visa_deadline_days": None,
            "runway_weeks": None, "mood_score": None, "energy_score": None,
            "open_tasks": None, "response": "", "sources": [],
        }
        predicted = classify_intent(state)
        expected = case["expected_intent"]
        is_correct = predicted == expected
        correct += int(is_correct)
        results.append({
            "input": case["input"],
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
        })

    accuracy = correct / len(test_cases) if test_cases else 0
    return {"accuracy": round(accuracy, 3), "correct": correct, "total": len(test_cases), "results": results}
