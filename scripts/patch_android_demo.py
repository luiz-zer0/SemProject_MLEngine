"""Apply the local USB-phone configuration to Louis's Android checkout, without changing production settings."""
import argparse
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("android_root", type=Path)
    p.add_argument("--apply", action="store_true", help="Write the reviewed changes; default is dry run")
    args = p.parse_args()
    root = args.android_root.resolve()
    gradle = root / "app/build.gradle.kts"
    repo = root / "app/src/main/java/com/example/app_1/data/FirebaseRepository.kt"
    edits = [
        (gradle, 'val demoFirebase = providers.gradleProperty("demoFirebase").orNull == "true"',
         'val demoFirebase = providers.gradleProperty("demoFirebase").orNull == "true"\nval demoHost = providers.gradleProperty("demoHost").orElse("10.0.2.2").get()\nrequire(demoHost in setOf("10.0.2.2", "127.0.0.1")) { "Invalid local demo host" }'),
        (gradle, 'buildConfigField("String", "ML_API_BASE_URL", "\\"http://10.0.2.2:8000\\"")',
         'buildConfigField("String", "ML_API_BASE_URL", "\\"http://$demoHost:8000\\"")'),
        (repo, 'auth.useEmulator("10.0.2.2", 9099)\n            storage.useEmulator("10.0.2.2", 9199)',
         'val host = URL(BuildConfig.ML_API_BASE_URL).host\n            check(host in setOf("10.0.2.2", "127.0.0.1"))\n            auth.useEmulator(host, 9099)\n            storage.useEmulator(host, 9199)'),
    ]
    updated = {}
    for path, old, new in edits:
        text = updated.get(path, path.read_text(encoding="utf-8"))
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit(f"Unexpected source in {path}; inspect manually. No changes written.")
        updated[path] = text.replace(old, new, 1)
    for path, text in updated.items():
        print(("Updating " if args.apply else "Would update ") + str(path))
        if args.apply:
            path.write_text(text, encoding="utf-8")
    print("Review git diff in the Android checkout; build and test before presenting.")

if __name__ == "__main__":
    main()
