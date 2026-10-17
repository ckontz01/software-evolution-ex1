# Fresh-clone verification record

The published study at commit `badbd34b76b79df97226656ec954deee7cbe4936` was cloned into a separate directory and verified independently of the original working tree.

- All 32 archives / 1,829 members restored with matching checksums.
- All 90 Maven artifacts verified offline; both endpoint Git/source-JAR comparisons passed.
- All 42 focused tests passed.
- The complete result audit passed 3,362,762 checks with zero failures.
- AI input hashes, assignment coverage and matching-graph evaluation passed.
- A new extraction and A1–A4 analysis of 33.7.2 reproduced all 26 compared graph, removal, partition and metric files byte for byte. Runtime/path metadata was deliberately excluded from byte comparisons.
- The published 29-page PDF matched its recorded SHA256.

`receipt.json` preserves the exact commands, environment, checked commit and log hashes. `01.log` through `09.log` are local copies of the logs named by their original absolute paths in that receipt. `latest_reproduction.json` lists every compared output. `remote_byte_verification.json` records the separate Git-object comparison of all 198 then-published files with local original bytes.

`verification_driver.py` is the environment-specific driver preserved as execution evidence; its absolute paths identify the actual isolated verification run. Use the portable commands in the repository README for normal reproduction. The commit adding this record changes only verification evidence and does not change the verified implementation, data, figures or report.
