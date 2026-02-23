from multi_swe_bench.harness.pull_request import PullRequest
from multi_swe_bench.harness.image import File

class Metamorphic:
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
