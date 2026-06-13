# Job Hunter Pro — Canonical Context Index

Project root:
`/data/data/com.termux/files/home/Workspaces/Agents/Job_Hunter_Platform/job-hunter-pro`

Global machine AGENTS:
`/data/data/com.termux/files/home/AGENTS.md`

Project-local canonical master:
`docs/agent_context/canonical/JOB_HUNTER_PRO_CANONICAL_MASTER_CONTEXT.md`

Raw source drop:
`docs/agent_context/source_drop/job_hunter_pro_canonical_master/JOB_HUNTER_PRO_CANONICAL_MASTER_SOURCE.txt`

Repository:
`https://github.com/mjmichaelware/job-hunter-pro`

Production URL:
`https://job-hunter-pro-5t3wttw2ua-uc.a.run.app`

Read order for agents:
1. `/data/data/com.termux/files/home/AGENTS.md`
2. project `AGENTS.md` if present
3. this index
4. `docs/agent_context/canonical/JOB_HUNTER_PRO_CANONICAL_MASTER_CONTEXT.md`
5. current code/config/schema
6. deployment/build files
7. current git status

Rules:
- Do not modify global `~/AGENTS.md`.
- Do not fake deployment status.
- Verify production URL with curl before claiming production works.
- Do not expose secrets.
- Do not use destructive commands without explicit approval.
