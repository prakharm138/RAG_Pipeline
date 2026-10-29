from pathlib import Path

def load_documents():

    documents = {}

    # Resolve the bundled corpus independently of the launch directory.
    folder = Path(__file__).resolve().parent / "knowledge"
    if not folder.is_dir():
        raise FileNotFoundError(f"Knowledge directory not found: {folder}")

    for file in folder.glob("*.txt"):

        documents[file.name] = file.read_text(
            encoding="utf-8"
        )

    if not documents:
        raise ValueError(f"No .txt documents found in knowledge directory: {folder}")

    return documents