"""
CV Generator CLI - Master/Derivative PDF system.

Usage:
    python generate.py                              # List available profiles
    python generate.py maria_gonzalez               # List derivatives for Maria
    python generate.py maria_gonzalez retail        # Generate PDF
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from engine.loader import list_profiles, list_derivatives, load_profile
from engine.pdf_builder import generate_pdf, register_fonts


def main():
    args = sys.argv[1:]

    if len(args) == 0:
        print("CV Generator")
        print("=" * 40)
        print("\nAvailable profiles:")
        for p in list_profiles():
            master = load_profile(p)
            nombre = master["persona"].get("nombre_completo", p)
            derivatives = list_derivatives(p)
            print(f"  {p}: {nombre}")
            if derivatives:
                print(f"    Derivatives: {', '.join(derivatives)}")
            else:
                print("    No derivatives")
        print(f"\nUsage: python generate.py <profile_id> <derivative_id>")
        return

    persona_id = args[0]

    if len(args) == 1:
        derivatives = list_derivatives(persona_id)
        if not derivatives:
            print(f"No derivatives for '{persona_id}'. Create one in derivatives/{persona_id}/")
            return
        master = load_profile(persona_id)
        nombre = master["persona"].get("nombre_completo", persona_id)
        print(f"Derivatives for {nombre}:")
        for d in derivatives:
            from engine.loader import load_derivative
            deriv = load_derivative(persona_id, d)
            config = deriv.get("config", {})
            print(f"  {d}: {config.get('objetivo_laboral', 'no objective')}")
        print(f"\nGenerate: python generate.py {persona_id} <derivative_id>")
        return

    derivado_id = args[1]
    print(f"Generating CV: {persona_id}/{derivado_id}...")

    try:
        register_fonts()
        path = generate_pdf(persona_id, derivado_id)
        print(f"PDF generated: {path}")
        print(f"Size: {path.stat().st_size / 1024:.1f} KB")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error generating PDF: {e}")


if __name__ == "__main__":
    main()
