from src.config import EXPORTS_DIR, ensure_project_dirs


def export_dataframe(dataframe, filename):
    """
    Export a pandas DataFrame to the data/exports folder.

    Parameters:
        dataframe: pandas DataFrame
            The result of an analysis query.

        filename: str
            The CSV file name to create inside data/exports.

    Returns:
        Path
            The full path of the exported file.
    """
    ensure_project_dirs()

    output_path = EXPORTS_DIR / filename

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    return output_path