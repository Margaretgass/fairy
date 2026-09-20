import re
from pathlib import Path
from urllib.parse import unquote

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = REPOSITORY_ROOT / "docs" / "build"
CURRICULUM_ROOT = BUILD_ROOT / "curriculum"

STAGE_FOLDERS = (
    "stage-01-local-app",
    "stage-02-desktop-fairy",
    "stage-03-tasks",
    "stage-04-daily-planning",
    "stage-05-focus",
    "stage-06-ai-tools",
    "stage-07-connectors",
    "stage-08-charms-and-pilot",
)

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def test_curriculum_keeps_each_stage_and_its_recovery_files_together() -> None:
    assert (CURRICULUM_ROOT / "README.md").is_file()

    for folder_name in STAGE_FOLDERS:
        assert (CURRICULUM_ROOT / folder_name / "README.md").is_file()

    for stage_number, session_count in ((1, 3), (2, 4)):
        stage_folder = CURRICULUM_ROOT / STAGE_FOLDERS[stage_number - 1]
        checkpoints = stage_folder / "checkpoints"

        for session_number in range(1, session_count + 1):
            assert (checkpoints / f"session-{session_number:02}.md").is_file()

        assert (checkpoints / "final" / "README.md").is_file()
        assert (checkpoints / "final" / "complete-code").is_dir()

    assert not (BUILD_ROOT / "checkpoints").exists()
    assert not list(BUILD_ROOT.glob("stage-*.md"))


def test_curriculum_local_links_resolve_after_files_move() -> None:
    broken_links: list[str] = []

    for markdown_file in BUILD_ROOT.rglob("*.md"):
        in_fence = False

        for line_number, line in enumerate(markdown_file.read_text().splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            for raw_target in MARKDOWN_LINK.findall(line):
                target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
                if target.startswith(("#", "http://", "https://", "mailto:")):
                    continue

                relative_path = unquote(target.split("#", maxsplit=1)[0])
                if not relative_path:
                    continue

                resolved = (markdown_file.parent / relative_path).resolve()
                if not resolved.exists():
                    source = markdown_file.relative_to(REPOSITORY_ROOT)
                    broken_links.append(f"{source}:{line_number} -> {target}")

    assert not broken_links, "Broken local links:\n" + "\n".join(broken_links)
