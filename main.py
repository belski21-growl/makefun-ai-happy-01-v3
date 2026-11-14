# Deliver the bundled picture to the grader.
#
# The repo ships exactly one picture, entry.png (JPEG data, named .png
# because the competition wants that filename). This script copies it
# into MAKEFUN_OUTPUT_DIR (or /output when the variable is unset) and
# proves the copy is faithful: it streams the file in blocks, hashes
# as it goes, and then streams the destination back and compares the
# two digests. If anything is off — missing file, wrong size, bad
# JPEG markers, a hash that does not match — it stops and says so
# instead of handing over a broken entry.
#
# The script never draws, downloads, or invents anything. The bytes
# that come out are the bytes that were packed in the repo. Running it
# twice gives the same file twice.
#
# Usage: python3 main.py

import hashlib
import os
import sys

PICTURE = "entry.png"
LIMIT = 1048576
BLOCK = 32768
MAGIC_OPEN = b"\xff\xd8"
MAGIC_CLOSE = b"\xff\xd9"


def fail(message):
    sys.stderr.write("ship-picture: " + message + "\n")
    sys.exit(1)


def bundle_dir():
    return os.path.dirname(os.path.abspath(__file__))


def target_dir():
    wanted = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if wanted:
        return wanted
    return "/output"


def sha256_hex(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            piece = stream.read(BLOCK)
            if not piece:
                break
            digest.update(piece)
    return digest.hexdigest()


def jpeg_ok(path):
    with open(path, "rb") as stream:
        head = stream.read(2)
        stream.seek(-2, os.SEEK_END)
        tail = stream.read(2)
    return head == MAGIC_OPEN and tail == MAGIC_CLOSE


def ship():
    home = bundle_dir()
    origin = os.path.join(home, PICTURE)
    dest_folder = target_dir()
    dest = os.path.join(dest_folder, PICTURE)

    if os.path.realpath(origin) == os.path.realpath(dest):
        fail("output would overwrite the bundled picture: " + dest)

    if not os.path.isfile(origin):
        fail("bundled picture missing: " + origin)

    size = os.path.getsize(origin)
    if size == 0:
        fail("bundled picture is empty: " + origin)
    if size > LIMIT:
        fail("bundled picture is %d bytes, over the 1 MiB limit" % size)
    if not jpeg_ok(origin):
        fail("bundled picture lacks JPEG start/end markers: " + origin)

    before = sha256_hex(origin)

    if not os.path.isdir(dest_folder):
        try:
            os.makedirs(dest_folder, exist_ok=True)
        except OSError as problem:
            fail("cannot make output folder " + dest_folder + ": " + str(problem))

    with open(origin, "rb") as reader, open(dest, "wb") as writer:
        while True:
            piece = reader.read(BLOCK)
            if not piece:
                break
            writer.write(piece)
        writer.flush()
        os.fsync(writer.fileno())

    if os.path.getsize(dest) != size:
        fail("destination size differs from the bundled picture")
    if sha256_hex(dest) != before:
        fail("destination hash differs from the bundled picture")
    if not jpeg_ok(dest):
        fail("destination lacks JPEG start/end markers: " + dest)

    sys.stdout.write(
        "entry.png: %d bytes, sha256 %s -> %s\n" % (size, before, dest)
    )


def main():
    ship()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
