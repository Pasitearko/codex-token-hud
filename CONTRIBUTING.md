# Contributing / 参与贡献

Contributions are welcome. This is a Windows desktop project; UI changes should be checked in an active Windows desktop session.

欢迎提交问题和改进。此项目仅在 Windows 上运行；界面改动请在可交互的 Windows 桌面会话中检查。

1. Open an issue for larger changes, or fork the repository and create a focused branch.
2. Keep token aggregation, chat matching, and HUD presentation changes separate where practical.
3. Run `python -m py_compile token_strip.py smooth_capsule.py` before opening a pull request. For UI changes, run the relevant `hud_*_probe.py` scripts in an unlocked Windows desktop session and describe what you observed.
4. Update both `README.md` and `README.zh-CN.md` when changing user-facing behavior.
5. Open a pull request with a short summary, verification steps, and screenshots for visual changes.

Please never attach real Codex session JSONL files, chat text, database files, access tokens, or unredacted personal screenshots to public issues or pull requests.

请勿在公开 Issue 或 PR 中上传真实 Codex 会话 JSONL、聊天正文、数据库、访问令牌或未经遮盖的个人截图。
