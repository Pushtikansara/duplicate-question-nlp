import argparse
import sys

from ares import ARES


def main() -> None:
    parser = argparse.ArgumentParser(description="ARES — Advanced Reasoning Engine for Semantics")
    parser.add_argument("question1", type=str, help="First question")
    parser.add_argument("question2", type=str, help="Second question")
    parser.add_argument("--model", "-m", type=str, default=None, help="Model name")
    parser.add_argument("--threshold", "-t", type=float, default=None, help="Decision threshold")
    parser.add_argument("--reflect", action="store_true", help="Enable reflection/trust scoring")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    engine = ARES()
    if args.model:
        engine.with_model(args.model)
    if args.threshold is not None:
        engine.with_threshold(args.threshold)
    if args.reflect:
        engine.with_reflection(True)

    result = engine.predict(args.question1, args.question2)

    if args.json:
        import json

        json.dump(result.to_dict(), sys.stdout, indent=2)
        print()
    else:
        print(f"Prediction: {result.prediction}")
        print(f"Confidence: {result.confidence:.4f}")
        print(f"Label: {result.predicted_label}")
        print(f"Model: {result.model_name}")
        print(f"Latency: {result.latency_ms:.2f}ms")
        if result.trust_score is not None:
            print(f"Trust: {result.trust_score:.1f} ({result.trust_level})")
            print(f"Risk: {result.risk_level}")


if __name__ == "__main__":
    main()
