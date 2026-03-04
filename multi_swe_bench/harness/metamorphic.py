from multi_swe_bench.harness.pull_request import PullRequest
from multi_swe_bench.harness.image import File

class Metamorphic:
    @staticmethod
    def apply_metamorphic_patch_cmd(pr: PullRequest, commit_message: str = "Apply metamorphic transformation") -> str:
        """
        Returns git command for **applying and committing** `metamorphic_base_patch`,
        if it's not None in the `pr.base`. Otherwise, returns an empty string (i.e., no-op behavior).
        """
        patch = pr.base.metamorphic_base_patch
        if (patch is not None) and (patch != ""):
            return Metamorphic._produce_apply_patch_commands(patch, commit_message)
        return ""

    @staticmethod
    def _produce_apply_patch_commands(patch: str, commit_message: str):
        """
        Returns git command for **applying and committing** `patch` with a given `commit_message`.
        """
        return (
            f"git apply - <<'__EOF_METAMORPHIC_PATCH__'\n"
            f"{patch}\n"
            f"__EOF_METAMORPHIC_PATCH__\n"
            f"git add -A && git commit -m '{commit_message}'"
        )


    @staticmethod
    def base_patch(pr: PullRequest) -> File:
        return File(
            "",
            "metamorphic_base.patch",
            f"{pr.metamorphic_base_patch}",
        )

    @staticmethod
    def fix_patch(pr: PullRequest) -> File:
        return File(
            "",
            "metamorphic_fix.patch",
            f"{pr.metamorphic_fix_patch}",
        )

    @staticmethod
    def base_run(pr: PullRequest) -> File:
        """Produces `File` that applies the metamorphic_base.patch on the base commit and runs tests"""
        return File(
            "",
            "metamorphic-run.sh",
            """#!/bin/bash
set -e

cd /home/{pr.repo}
git apply /home/metamorphic_base.patch
./gradlew test

""".format(pr=pr))

    @staticmethod
    def fix_run(pr: PullRequest) -> File:
        """Produces `File` that applies the test.patch + fix.patch + metamorphic_fix.patch and runs tests"""
        return File(
            "",
            "metamorphic-fix-run.sh",
            """#!/bin/bash
set -e

cd /home/{pr.repo}

git apply /home/test.patch /home/fix.patch /home/metamorphic_fix.patch
./gradlew test

""".format(pr=pr))
