@echo off
:loop
"C:\Program Files (x86)\WinSCP\winscp.com" /script=full_remote_to_local_synchronization.txt
timeout /t 2
goto loop
