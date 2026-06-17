#!/usr/bin/env python3
"""Migrate Hanzo services onto the PaaS (platform.hanzo.ai) via its API. No GHA.

  X_API_KEY=<platform api key> python3 migrate.py services.yaml

The api key is minted per-user at platform.hanzo.ai -> Settings -> API Keys.
Idempotent-ish: failures per service are caught and reported; rerun is safe.
"""
import os, sys, json, urllib.request, urllib.error
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

API = os.environ.get("PLATFORM", "https://platform.hanzo.ai/api")
KEY = os.environ.get("X_API_KEY") or sys.exit("set X_API_KEY")

def call(proc, body=None):
    req = urllib.request.Request(f"{API}/{proc}", data=json.dumps(body or {}).encode(),
        headers={"x-api-key": KEY, "content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def main():
    inv = yaml.safe_load(open(sys.argv[1] if len(sys.argv) > 1 else "services.yaml"))
    gh = call("github.githubProviders")
    ghid = gh[0]["githubId"] if gh else None
    srv = call("server.all")
    serverId = srv[0]["serverId"] if srv else None
    print(f"github integration={ghid}  server={serverId or '<platform default>'}")
    ok = 0
    for s in inv["services"]:
        try:
            proj = call("project.create", {"name": s["project"], "description": f"{s['project']} ecosystem"})
            envid = proj["environments"][0]["environmentId"]
            aid = call("application.create", {"name": s["name"], "appName": s["name"],
                "environmentId": envid, **({"serverId": serverId} if serverId else {})})["applicationId"]
            if ghid:
                call("application.saveGithubProvider", {"applicationId": aid, "githubId": ghid,
                    "owner": s["owner"], "repository": s["repo"], "branch": s.get("branch", "main"),
                    "buildPath": "/", "enableSubmodules": False, "triggerType": "push"})
            else:
                call("application.saveGitProvider", {"applicationId": aid,
                    "customGitUrl": f"git@github.com:{s['owner']}/{s['repo']}.git",
                    "customGitBranch": s.get("branch", "main"), "customGitBuildPath": "/",
                    "enableSubmodules": False})
            call("application.saveBuildType", {"applicationId": aid, "buildType": s.get("build", "nixpacks"),
                "dockerContextPath": "/", "dockerBuildStage": ""})
            if s.get("env"):
                call("application.saveEnvironment", {"applicationId": aid, "env": s["env"], "createEnvFile": True})
            call("application.deploy", {"applicationId": aid, "title": "initial migrate"})
            print(f"  ✓ {s['name']:18} appId={aid}  ({s['owner']}/{s['repo']})")
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"  ✗ {s['name']:18} {e.code} {e.read()[:120].decode(errors='ignore')}")
        except Exception as e:
            print(f"  ✗ {s['name']:18} {e}")
    print(f"\n{ok}/{len(inv['services'])} services on platform.hanzo.ai — check the dashboard.")

if __name__ == "__main__":
    main()
