import re

def analyze_requirement(requirement):
    """
    Analyze a software requirement for clarity, ambiguity, and consistency.
    """
    # Rule-based checks
    ambiguous_words = ["may", "might", "could", "possibly", "approximately"]
    contradictions = ["not possible", "never", "cannot", "no way"]

    analysis = {
        "is_ambiguous": False,
        "is_inconsistent": False,
        "suggestions": []
    }

    # Check for ambiguous words
    for word in ambiguous_words:
        if word in requirement.lower():
            analysis["is_ambiguous"] = True
            analysis["suggestions"].append(f"Consider avoiding ambiguous word: '{word}'")

    # Check for contradictions
    for phrase in contradictions:
        if phrase in requirement.lower():
            analysis["is_inconsistent"] = True
            analysis["suggestions"].append(f"Potential contradiction found: '{phrase}'")

    # Final recommendation
    if not analysis["is_ambiguous"] and not analysis["is_inconsistent"]:
        analysis["suggestions"].append("The requirement appears clear and consistent.")

    return analysis
