"""
Bazan AI Document Pipeline
Entry point — orchestrates: detect → extract → assess → chunk → upload → index
"""

import sys
import time
import shutil
from pathlib import Path

from config import settings
from index_db import init_db, is_already_processed, save_result, get_review_files, get_stats
from extractor import extract
from assessor import assess
from chunker import chunk_document, create_summary_document
from uploader import WebUIUploader


SUMMARY_PROMPT = """Tóm tắt tài liệu cà phê sau thành 200-300 từ tiếng Việt.
Tập trung vào: thông tin thực hành, số liệu quan trọng, khuyến nghị chính.
Không dùng bullet points, viết thành đoạn văn.

{text}"""


def create_summary(text: str) -> str:
    import ollama

    response = ollama.chat(
        model=settings.assess_model,
        messages=[{"role": "user", "content": SUMMARY_PROMPT.format(text=text[:6000])}],
        options={"num_ctx": settings.assess_context, "temperature": 0.3},
    )
    return response["message"]["content"].strip()


def get_all_files() -> list[Path]:
    files = []
    for suffix in ["*.pdf", "*.PDF"]:
        files.extend(settings.raw_pdf_dir.glob(suffix))
    for suffix in ["*.md", "*.markdown"]:
        files.extend(settings.raw_md_dir.glob(suffix))
    return sorted(files)


def process_file(path: Path, uploader: WebUIUploader, dry_run: bool = False) -> dict:
    result = {"status": "error", "error_message": None}
    print(f"\n{'[DRY]' if dry_run else ''} Processing: {path.name}")

    # Extract
    try:
        doc = extract(path)
        if not doc.text.strip():
            result["error_message"] = "Empty text after extraction"
            result["status"] = "error"
            return result
        print(f"  Extracted: {len(doc.text)} chars via {doc.extraction_method}")
    except Exception as e:
        result["error_message"] = f"Extract failed: {e}"
        return result

    # Assess
    assessment = assess(doc.text)
    result.update(assessment)
    score = assessment["quality_score"]
    print(f"  Quality: {score}/10 | Topic: {assessment['topic']} | {assessment['reason']}")

    if dry_run:
        result["status"] = "dry_run"
        return result

    # Route theo score
    if score <= settings.quality_threshold_review - 1:
        dest = settings.rejected_dir / path.name
        shutil.copy2(path, dest)
        result["status"] = "rejected"
        print(f"  → Rejected (score {score})")
        return result

    if score < settings.quality_threshold_upload:
        dest = settings.review_dir / path.name
        shutil.copy2(path, dest)
        result["status"] = "review"
        print(f"  → Needs review (score {score})")
        return result

    # Score >= threshold → process và upload
    print(f"  → Uploading to KB (score {score})")

    # Tạo summary
    summary_text = create_summary(doc.text)
    summary_doc = create_summary_document(summary_text, path.name, assessment)

    # Upload summary vào bazan_summary
    if settings.kb_summary_id:
        summary_filename = f"summary_{path.stem}.txt"
        file_id = uploader.upload_to_kb(summary_doc, summary_filename, settings.kb_summary_id)
        if file_id:
            print(f"  ✓ Summary uploaded: {summary_filename}")
        time.sleep(settings.upload_delay_seconds)

    # Tạo chunks và upload vào bazan_detail
    if settings.kb_detail_id:
        chunks = chunk_document(doc, path.name, settings.chunk_size, settings.chunk_overlap)
        print(f"  Chunks: {len(chunks)}")

        # Gộp chunks thành 1 file với separator (WebUI sẽ re-chunk)
        combined = "\n\n---\n\n".join(c.content for c in chunks)
        detail_filename = f"detail_{path.stem}.txt"
        file_id = uploader.upload_to_kb(combined, detail_filename, settings.kb_detail_id)
        if file_id:
            result["webui_file_id"] = file_id
            print(f"  ✓ Detail chunks uploaded: {detail_filename}")

    result["status"] = "uploaded"
    return result


def run(dry_run: bool = False, force: bool = False):
    init_db()
    uploader = WebUIUploader()
    files = get_all_files()

    print(f"\n{'=' * 50}")
    print(f"Bazan AI Document Pipeline {'(DRY RUN)' if dry_run else ''}")
    print(f"Found {len(files)} files in raw directories")
    print(f"{'=' * 50}")

    skipped = processed = 0

    for path in files:
        if not force and is_already_processed(path):
            skipped += 1
            continue

        result = process_file(path, uploader, dry_run=dry_run)

        if not dry_run:
            save_result(path, result)
        processed += 1

    print(f"\n{'=' * 50}")
    print(f"Done: {processed} processed, {skipped} skipped")
    if not dry_run:
        stats = get_stats()
        print(f"DB stats: {stats}")
    print(f"{'=' * 50}\n")


def show_review():
    init_db()
    files = get_review_files()
    if not files:
        print("Không có file nào cần review.")
        return
    print(f"\n{'=' * 50}")
    print(f"Files cần review ({len(files)}):")
    print(f"{'=' * 50}")
    for f in files:
        print(f"  [{f['quality_score']}/10] {f['file_path']}")
        print(f"         Lý do: {f.get('reason', 'N/A')}")
    print()


if __name__ == "__main__":
    if "--review" in sys.argv:
        show_review()
    elif "--dry" in sys.argv:
        run(dry_run=True)
    elif "--force" in sys.argv:
        run(force=True)
    else:
        run()
