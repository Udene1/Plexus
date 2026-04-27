"""
Physics Verifier Agent — Grounded in first-principles via sandbox execution.
Validates hypotheses against conservation laws, causality, and thermodynamics.
"""
import uuid
import time
import math
from typing import Dict, Any
import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

from textplexus.schemas import CampaignState, PhysicsCheckResult, Evidence
from textplexus.config import Config, get_llm

llm = get_llm(temperature=0.0)


class PhysicsSandbox:
    """Safe sandbox for executing physics code — grounded in first principles."""

    ALLOWED_GLOBALS = {
        "np": np,
        "sp": sp,
        "solve_ivp": solve_ivp,
        "math": math,
        "pi": math.pi,
        "e": math.e,
        # Fundamental constants
        "G": 6.67430e-11,       # Gravitational constant (m³ kg⁻¹ s⁻²)
        "c": 299792458,         # Speed of light (m/s)
        "h": 6.62607015e-34,    # Planck's constant (J·s)
        "k_B": 1.380649e-23,    # Boltzmann constant (J/K)
        "eps_0": 8.854187817e-12,  # Vacuum permittivity (F/m)
        "mu_0": 1.25663706212e-6,  # Vacuum permeability (H/m)
        "e_charge": 1.602176634e-19,  # Elementary charge (C)
    }

    @staticmethod
    def run_code(code: str, timeout: int = 5) -> Dict[str, Any]:
        """Execute physics code safely and return result + violation score."""
        start_time = time.time()

        # Pre-built first-principles checkers
        def check_momentum_conservation(initial_p, final_p, tolerance=1e-6):
            diff = abs(np.array(initial_p) - np.array(final_p)).max()
            return diff < tolerance, float(diff)

        def check_energy_conservation(initial_e, final_e, tolerance=1e-6):
            diff = abs(initial_e - final_e)
            return diff < tolerance, float(diff)

        def trajectory_under_gravity(initial_pos, initial_vel, time_span, mass=1.0):
            """Simple 2D projectile under gravity — first principles."""
            def ode(t, y):
                return [y[2], y[3], 0, -9.81]
            sol = solve_ivp(
                ode, time_span, initial_pos + initial_vel,
                t_eval=np.linspace(0, time_span[1], 100)
            )
            return sol.y

        locals_dict = {"__builtins__": {}}  # Very restricted
        locals_dict.update(PhysicsSandbox.ALLOWED_GLOBALS)
        locals_dict.update({
            "check_momentum": check_momentum_conservation,
            "check_energy": check_energy_conservation,
            "trajectory_gravity": trajectory_under_gravity,
        })

        try:
            exec(code, locals_dict)

            execution_time = time.time() - start_time
            if execution_time > timeout:
                return {"error": "Timeout exceeded", "valid": False, "score": 1.0}

            return {
                "success": True,
                "result": locals_dict.get("result", "No explicit 'result' variable returned"),
                "valid": True,
                "score": 0.0,
                "time": execution_time,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "valid": False,
                "score": 0.8,  # High violation — code couldn't even run
            }


async def physics_verifier_node(state: CampaignState):
    """
    Physics Verifier with real code execution.
    Grounds answers in first principles via sandbox.
    """
    focus_id = state.current_focus_id
    if not focus_id or focus_id not in state.hypotheses:
        return state

    hypothesis = state.hypotheses[focus_id]

    prompt = f"""You are a rigorous Physics Verifier. Use first-principles reasoning only.
Check this hypothesis for violations of:
- Conservation of energy / momentum
- Causality and entropy increase (2nd law of thermodynamics)
- Speed of light, quantum limits, scaling laws

Hypothesis: {hypothesis.content}

If quantitative, generate Python code using numpy (as np), sympy (as sp), or scipy's solve_ivp.
You may use these pre-built helpers:
  check_energy(initial_e, final_e, tolerance=1e-6) -> (bool, diff)
  check_momentum(initial_p, final_p, tolerance=1e-6) -> (bool, diff)
  trajectory_gravity(initial_pos, initial_vel, time_span) -> solution array

Available constants: G, c, h, k_B, eps_0, mu_0, e_charge, pi, e

Always assign a final variable called 'result' (dict with 'valid': bool, 'explanation': str).
Put the generated code in the 'suggested_code' field.

Return structured output with: valid, violated_law, quantitative_constraint, suggested_code, suggested_adjustment, reasoning.
"""

    result: PhysicsCheckResult = await llm.with_structured_output(PhysicsCheckResult).ainvoke(prompt)

    # Execute sandbox if code was generated
    sandbox_result = None
    if result.suggested_code:
        sandbox_result = PhysicsSandbox.run_code(result.suggested_code)

    # Compute violation score
    if sandbox_result:
        violation_score = sandbox_result["score"]
        # If sandbox ran but returned an invalid result, trust sandbox over LLM
        if not sandbox_result["valid"]:
            result.valid = False
    else:
        violation_score = 0.0 if result.valid else 0.9

    # Build evidence
    e_id = str(uuid.uuid4())[:8]
    is_valid = result.valid and (not sandbox_result or sandbox_result["valid"])

    evidence_content = (
        f"Physics Check: {'VALID' if is_valid else 'VIOLATION'}\n"
        f"Violated Law: {result.violated_law or 'None'}\n"
        f"Reasoning: {result.reasoning}"
    )
    if sandbox_result:
        evidence_content += (
            f"\nSandbox Execution: {'Success' if sandbox_result['success'] else 'Failed'}\n"
            f"Result: {sandbox_result.get('result', sandbox_result.get('error'))}\n"
            f"Violation Score: {violation_score:.3f} (0=perfect, 1=impossible)"
        )

    evidence = Evidence(
        id=e_id,
        hypothesis_id=focus_id,
        source="Physics Verifier (Sandbox)",
        content=evidence_content.strip(),
        metadata={
            "violation_score": violation_score,
            "first_principles": True,
            "executed": bool(sandbox_result),
        },
    )
    state.evidence.append(evidence)

    # Tag hypothesis for penalty if violation detected
    if violation_score > 0.3:
        hypothesis.metadata["physics_violation"] = violation_score

    return state
