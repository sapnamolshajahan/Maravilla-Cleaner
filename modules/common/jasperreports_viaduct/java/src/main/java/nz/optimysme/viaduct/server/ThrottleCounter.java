package nz.optimysme.viaduct.server;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Simple counter for throttled dbnames.
 */
public class ThrottleCounter
{
	private static final Logger _logger = LogManager.getLogger (ThrottleCounter.class);

	public final String dbname;
	public final int limit;
	private int _active;

	public ThrottleCounter (
		String dbname,
		int limit)
	{
		this.dbname = dbname;
		this.limit = limit;
		this._active = 0;
	}

	public boolean atLimit ()
	{
		return limit > 0 && _active >= limit;
	}

	public ThrottleCounter inc ()
	{
		_active++;
		_logger.debug ("\u2191" + this);
		return this;
	}

	public ThrottleCounter dec ()
	{
		_active--;
		_logger.debug ("\u2193" + this);
		return this;
	}

	@Override
	public String toString ()
	{
		return String.format ("{dbname=%s, limit=%d, active=%d}", dbname, limit, _active);
	}
}
