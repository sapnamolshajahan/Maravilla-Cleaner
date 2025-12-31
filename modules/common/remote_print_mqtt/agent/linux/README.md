# Linux with systemd

`remote-print-agent.bash` is a wrapper script the will be invoked on startup.

Copy `remote-print.service` into /etc/systemd/system and modify the pathnames to suit. Log directories must be
created **prior** to startup.
