# SOP Compliance Report

## Overview

- Project: `Automation of Manual testing`
- Task: Automate the manual testing by developing a tool which crawls through the site and do all testing.
- Human Owner: SHIVAM MORE
- Agent: Codex CLI
- Date: 12-01-2026

## Summary of Outcome

- The tool crawls through all the modules and tests each interactive element.
- Remaining issue encountered: The tool is still not testing each module completely likely due to routing issue.

## SOP Compliance by Step

### Step 1: Task Definition (Human)

- Goal: Automate the manual testing of the Petyosa application.
- Scope: Includes all modules in the app; excludes any external elements.
- Risk Areas: false positive, performance.
- Acceptance Criteria: python main.py completes and produces a complete report with minimal mistake.


### Step 2: Plan First (Agent -> Human)

- Evidence: List the files/modules that will be touched. Build an agent doing the testing and providing the comprehensive report. List the tests intended to run. Plan is approved by human owner.

### Step 3: Execute With Evidence (Agent)

- Evidence :
  - `python main.py`, `pip install playwright`.
  - Check proof artifacts for logs and sceenshots.

### Step 4: Audit Loop (Required)

- Security / tenancy / RBAC: No changes intended; none validated.
- Data integrity & migrations: No data migrations in scope.
- Regression risks: No regression risk identified.
- Rollback plan: Revert to last commit using `git revert`.

### Step 5: Human Understanding (Mandatory in PR)

- What changed and why: The testing is automated using playright to make it faster, efficient and reliable.
- One real risk: May give false positive and ignore testing important features.
- One thing personally verified: The tool is crawling each and every element of every module.
- One thing uncertain / watching: The depth of the testing through automation.

### Step 6: PR Submission Requirements

- Task: Automate the manual testing by developing an agent who crawls through the site and do all testing.
- Summary of changes: Tool developed which automatically crawls the website and test each functionality.
- Audit output attached: none.
- Proof artifacts: none.
- Human Understanding: refer Step 5.
- Rollback note: revert to last working version via `git revert`.
Step 6: PR Submission Requirements

## Proof Artifacts (console output/Logs)
```
shiva@Asus MINGW64 /c/christ/petyosa/testing (main)
$ python main.py
00:12:25] Output folder: test_results\run_20260113_001225
[00:12:25] Target website: https://devapp.petyosa.com/
[00:12:26] 
>> Launching browser...
[00:12:27] 
============================================================
[00:12:27] MANUAL LOGIN REQUIRED
[00:12:27] ============================================================

[00:12:27] Opening login page: https://devapp.petyosa.com/
[00:12:29] 
[WAIT] Please complete the login process (OTP) in the browser.       
[00:12:29] [WAIT] You have 30 seconds to complete login.
[00:12:29] [WAIT] The test will continue automatically after you log in.

[00:12:38] [WAIT] 20 seconds remaining...
[00:12:48] [WAIT] 10 seconds remaining...
[00:13:00] [!] Login timeout reached. Continuing anyway...
[00:13:00] 
============================================================
[00:13:00] STARTING AUTOMATED TESTS
[00:13:00] ============================================================

[00:13:00]
[1/100] Testing: https://devapp.petyosa.com/community
[00:13:03]   Found 3 interactive elements
[00:13:08]   Status: WARNING
[00:13:08]   Load time: 1478ms
[00:13:08]   Network errors: 1
[00:13:08]   Console errors: 3
[00:13:08]   Elements tested: 3 (Failed: 0)
[00:13:08]   Discovered 0 new links (depth: 0)
....
....
....
[00:15:10]   Status: WARNING
[00:15:10]   Load time: 1427ms
[00:15:10]   Network errors: 1
[00:15:10]   Console errors: 15
[00:15:10]   Elements tested: 9 (Failed: 0)
[00:15:10]   Discovered 0 new links (depth: 0)
[00:15:11] 
============================================================
[00:15:11] GENERATING REPORT
[00:15:11] ============================================================

[00:15:11] 
## TEST SUMMARY
[00:15:11]   Total pages tested: 19
[00:15:11]   Pages with errors: 17
[00:15:11]   Total network errors: 65
[00:15:11]   Total console errors: 163
[00:15:11]   Total elements tested: 179
[00:15:11]   Element failures: 0
[00:15:11]   Duration: 165.6 seconds
[00:15:11]
[FILE] Report saved to: test_results\run_20260113_001225\test_report.html
[00:15:11] [FILE] Data saved to: test_results\run_20260113_001225\test_data.json
[00:15:11]
>> Opening report in browser...
```
!

## Issues Known

- The tool isn't fully capable of crawling all the endpoints of the website yet.
- The report isn't providing the proper explaination of the error (only the error code and its meaning)

## Improvements for Next Time

1. **Starting with proper task definition** 
2. **Plan things first before building**.
3. **Maintain documents as proof artifacts**
4. **Make a Human Understanding section before PR submission**.
5. **Be active and check everything precisely whatever is done by AI**