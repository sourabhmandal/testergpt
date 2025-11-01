
from github.types import CodeFileDetailsList, GithubPRChanged, CodeFileDetails
from unidiff import PatchSet
import requests

def extract_diff_from_pr(pr_diff_url: str) -> CodeFileDetails:
    response = requests.get(pr_diff_url)
    response.raise_for_status()

    patch = PatchSet(response.text)
    pr_diff_obj: CodeFileDetailsList = CodeFileDetailsList(root=[])

    for patched_file in patch:
        pr_line_data += f"File: {patched_file.path}\n"
        pr_diff_obj.root.append(
            CodeFileDetails(
                file_path=patched_file.path,
                additions=[line.value.strip() for hunk in patched_file for line in hunk if line.line_type == "+"],
                deletions=[line.value.strip() for hunk in patched_file for line in hunk if line.line_type == "-"],
            )
        )
        for hunk in patched_file:
            for line in hunk:
                pr_line_data += f"{line.line_type}: {line.value.strip()}\n"
    return pr_diff_obj


def _get_diff_line_mapping(payload: GithubPRChanged) -> Dict[str, Dict[int, int]]:
    """
    Get mapping of file line numbers to diff positions.
    Returns: {file_path: {line_number: diff_position}}
    """
    try:
        diff_url = payload.pull_request.diff_url
        response = requests.get(diff_url)
        response.raise_for_status()

        patch = PatchSet(response.text)
        line_mapping = {}

        for patched_file in patch:
            file_path = patched_file.path
            if file_path.startswith("b/"):
                file_path = file_path[2:]  # Remove 'b/' prefix

            line_mapping[file_path] = {}
            position = 0

            for hunk in patched_file:
                for line in hunk:
                    position += 1
                    # Only map lines that are additions or context (not deletions)
                    if line.line_type in ["+", " "]:
                        if line.target_line_no:
                            line_mapping[file_path][line.target_line_no] = position

        return line_mapping
    except Exception as e:
        print(f"Error parsing diff for line mapping: {e}")
        return {}
