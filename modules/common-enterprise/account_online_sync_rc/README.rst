Online Bank Synchronization Controls
====================================

Enable or disable Online Bank Statement Synchronization using
the configuration file.

The following section must be included in the configuration
in order for a successful sync::

	[account_online_sync_rc]

	enable_fetch = True
	enable_fetch_wait = True

