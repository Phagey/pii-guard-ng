import shutil
import time
from pathlib import Path

import evaluate
import pii_guard

BENCH_FOLDER = Path("bench_data")
COPIES_FOR_MANY_FILES = 100
LARGE_FILE_SIZES_MB = [0.25, 0.5, 1.0, 2.0]


def scan_folder(folder):
    files = pii_guard.find_files(folder)
    total_bytes = 0
    total_items = 0

    start = time.perf_counter()
    for file_path in files:
        text = pii_guard.read_file(file_path)
        total_bytes += len(text.encode("utf-8"))
        emails, phones, ids, cards = pii_guard.analyze_text(text)
        total_items += len(emails) + len(phones) + len(ids) + len(cards)
    seconds = time.perf_counter() - start

    return len(files), total_bytes, total_items, seconds


def build_many_files():
    folder = BENCH_FOLDER / "many_files"
    folder.mkdir(parents=True)

    for copy in range(1, COPIES_FOR_MANY_FILES + 1):
        for source in evaluate.DATA_FOLDER.iterdir():
            target = folder / f"copy{copy:02d}_{source.name}"
            shutil.copyfile(source, target)

    return folder


def build_large_file(size_mb, base_text):
    folder = BENCH_FOLDER / f"large_{size_mb}mb"
    folder.mkdir(parents=True)

    target_size = int(size_mb * 1_000_000)
    repeats = target_size // len(base_text) + 1
    text = (base_text * repeats)[:target_size]
    text = text[:text.rfind("\n") + 1]

    (folder / "large.txt").write_text(text, encoding="utf-8")
    return folder


def print_result(name, files, total_bytes, items, seconds):
    megabytes = total_bytes / 1_000_000
    print(f"{name:<22}{files:>7}{megabytes:>9.2f}{items:>9}{seconds:>10.2f}{megabytes / seconds:>10.2f}")


def main():
    evaluate.build_dataset()

    if BENCH_FOLDER.exists():
        shutil.rmtree(BENCH_FOLDER)

    base_text = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted(evaluate.DATA_FOLDER.glob("*.txt"))
    )

    print(f"{'Test':<22}{'Files':>7}{'MB':>9}{'Items':>9}{'Seconds':>10}{'MB/sec':>10}")

    folder = build_many_files()
    print_result("Many small files", *scan_folder(folder))

    for size_mb in LARGE_FILE_SIZES_MB:
        folder = build_large_file(size_mb, base_text)
        print_result(f"One {size_mb} MB file", *scan_folder(folder))


if __name__ == "__main__":
    main()