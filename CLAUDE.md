# MSWE-Agent

## Overview

MSWE-agent is an AI agent that generates patches to fix software bugs by interacting with codebases in Docker containers. It shares image-building infrastructure with multi-swe-bench for evaluation.

---

## Agent Execution Workflow

### Entry Points

- `multirun.py` - Run agent on multiple instances in parallel
- `run.py` - Run agent on a single instance

### Execution Flow

```
multirun.py / run.py
    ↓
get_instances() → prepare_datas() → build_images()  [if prebuild=True]
    ↓
Main(args, instance_id).main()
    ↓
SWEEnv.reset(instance_id)  [creates container, sets up repo]
    ↓
Agent.run()  [agent interacts with container]
    ↓
Submit patch → save to all_preds.jsonl
```

---

## Image Building Process

### Phase 1: Base Image
- Ubuntu with language-specific tooling (Java JDK, Maven, Gradle, etc.)
- Repository cloned to `/home/{repo}/`

### Phase 2: Instance Image (PR-specific)
- Built on top of base image
- Contains:
  - `/home/fix.patch` - Golden fix patch (from dataset)
  - `/home/test.patch` - Test patch that exposes the bug
  - `/home/metamorphic_base.patch` - Metamorphic transformation (if present)
  - `/home/prepare.sh` - Setup script
  - `/home/fix-run.sh`, `/home/test-run.sh`, `/home/run.sh` - Execution scripts

### prepare.sh Execution (During Image Build)
```bash
cd /home/{repo}
git checkout {pr.base.sha}

# Apply metamorphic patch if present (saved to /home/metamorphic_base.patch)
{Metamorphic.apply_metamorphic_patch_cmd(pr)}

# Pre-build to warm cache
./gradlew build || mvn clean test || ...
```

---

## Runtime: SWEEnv.reset()

When the agent starts working on an instance (`sweagent/environment/swe_env.py`):

1. **Create container** from pre-built image
2. **Clean repository** to base state:
   ```python
   for cmd in [
       f"cd {self._repo_name}",
       "git restore .",
       f"git reset --hard {self.base_commit}",
       "git clean -fdxq",
   ]:
       self.communicate_with_handling(cmd, ...)
   ```

3. **Re-apply metamorphic patch** (if exists):
   ```python
   self.communicate_with_handling(
       "if [ -f /home/metamorphic_base.patch ]; then "
       "git apply /home/metamorphic_base.patch && "
       "git add -A && "
       "git commit -m 'Re-apply metamorphic_base_patch transformation'; "
       "fi",
       ...
   )
   ```

4. **Install dependencies** (jq, etc.)
5. **Set up environment variables**
6. Agent begins interacting with the repository

---

## Metamorphic Testing Integration

### What It Does
Metamorphic transformations modify the codebase semantically while preserving behavior:
- Rename classes/methods/files
- Refactor code structure

### How It Works

1. **Dataset contains** `pr.base.metamorphic_base_patch`
2. **Image build** applies and commits the patch, saves to `/home/metamorphic_base.patch`
3. **Runtime** re-applies the patch after `git reset --hard` (to ensure agent sees transformed code)

### metamorphic.py

```python
METAMORPHIC_PATCH_PATH = "/home/metamorphic_base.patch"

class Metamorphic:
    @staticmethod
    def apply_metamorphic_patch_cmd(pr, commit_message):
        patch = pr.base.metamorphic_base_patch
        if patch:
            return (
                f"cat > {METAMORPHIC_PATCH_PATH} << 'EOF'\n{patch}\nEOF\n"
                f"git apply {METAMORPHIC_PATCH_PATH}\n"
                f"git add -A && git commit -m '{commit_message}'\n"
            )
        return ""
```

---

## Critical Bug Fixed

### The Problem
`SWEEnv.reset()` was running `git reset --hard {base_commit}` which reset to the **original** commit, undoing the metamorphic transformation applied during image build.

### The Solution
After `git reset --hard`, re-apply `/home/metamorphic_base.patch` if it exists:
```bash
if [ -f /home/metamorphic_base.patch ]; then
    git apply /home/metamorphic_base.patch
    git add -A
    git commit -m 'Re-apply metamorphic_base_patch transformation'
fi
```

This ensures the agent always sees the metamorphic-transformed codebase.

---

## Key Files

| File | Purpose |
|------|---------|
| `multirun.py` | Entry point for running agent on multiple instances |
| `run.py` | Entry point for running agent on single instance |
| `sweagent/environment/swe_env.py` | Environment managing Docker container interaction |
| `sweagent/environment/utils.py` | Utilities including `get_instances()`, container helpers |
| `sweagent/agent/agents.py` | Agent logic |
| `multi_swe_bench/harness/build_dataset.py` | Image building logic |
| `multi_swe_bench/harness/metamorphic.py` | Metamorphic patch application |
| `multi_swe_bench/harness/repos/{lang}/{org}/{repo}.py` | Instance implementations |

---

## Running the Agent

### Single Instance
```bash
python run.py \
    --model_name gpt4 \
    --data_path path/to/dataset.jsonl \
    --config_file config/default.yaml
```

### Multiple Instances
```bash
python multirun.py \
    --model_name gpt4 \
    --pr_file path/to/dataset.jsonl \
    --pre_build_all_images True
```

### Key Arguments
- `--pre_build_all_images`: Build all images before running (recommended for metamorphic)
- `--model_name`: Model to use (gpt4, claude, etc.)
- `--per_instance_cost_limit`: Max cost per instance

---

## Verification

To verify metamorphic setup is working:

1. **Build image**:
   ```bash
   python multirun.py --pr_file dataset.jsonl --pre_build_all_images True
   ```

2. **Check image contents**:
   ```bash
   docker run -it mockito/mockito:pr-3129 bash
   ls -la /home/  # Should see metamorphic_base.patch
   cd /home/mockito && git log --oneline -3
   # Should see "Apply metamorphic_base_patch transformation" commit
   ```

3. **Check at runtime**: Add logging to `SWEEnv.reset()` to verify patch is re-applied

---

## Important Notes

### Docker Image Rebuild Required
After modifying `metamorphic.py` or instance implementations, you must rebuild Docker images:
- Delete old images: `docker rmi mockito/mockito:pr-3129`
- Run with `--pre_build_all_images True`

### Shared Code with multi-swe-bench
The `multi_swe_bench/` directory is shared between MSWE-agent and multi-swe-bench repos. Changes to:
- `metamorphic.py`
- Instance implementations (`repos/{lang}/{org}/{repo}.py`)
- `build_dataset.py`

...should be synchronized between both repos.
