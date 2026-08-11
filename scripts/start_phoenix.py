"""Launch Phoenix from Python for local learning; Docker Compose is preferred for persistence."""

from threading import Event

import phoenix as px


def main() -> None:
    session = px.launch_app()
    if session is None:
        raise RuntimeError("Phoenix did not return a local session")
    print(f"Phoenix is running at {session.url}")
    print("Press Ctrl+C to stop. Notebook-style launch is not intended for production persistence.")
    try:
        Event().wait()
    except KeyboardInterrupt:
        print("Stopping Phoenix.")


if __name__ == "__main__":
    main()
