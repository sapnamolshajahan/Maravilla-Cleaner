package nz.optimysme.viaduct.server;

import java.util.HashMap;
import java.util.Map;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.stereotype.Service;
import org.springframework.web.context.ServletContextAware;

import jakarta.servlet.ServletContext;

/**
 * Manage limits on the number of active Viaduct Reports.
 */
@Service
public class Throttler
	implements ServletContextAware
{
	private static final Logger _logger = LogManager.getLogger (Throttler.class);

	//@formatter:off
	private static final String
		CtxMaxActive = "throttler.max.active",
		CtxDefaultLimit = "throttler.default.limit",
		CtxDbLimits = "throttler.db.limits";
	//@formatter:on

	/*
	 * Instance.
	 */
	private int _maxActive, _active, _defaultLimit;
	private Map<String, ThrottleCounter> _dbCounters;

	public Throttler ()
	{
		_maxActive = _active = _defaultLimit = 0;
		_dbCounters = new HashMap<> ();
	}

	@Override
	public void setServletContext (
		ServletContext context)
	{
		String maxActive = context.getInitParameter (CtxMaxActive);
		if (maxActive != null)
		{
			_maxActive = Integer.parseInt (maxActive);
			_logger.info (CtxMaxActive + "=" + _maxActive);

		} else
		{
			_logger.info ("no global limit specified");
		}

		String defaultLimit = context.getInitParameter (CtxDefaultLimit);
		if (defaultLimit != null)
		{
			_defaultLimit = Integer.parseInt (defaultLimit);
			_logger.info (CtxDefaultLimit + "=" + _defaultLimit);
		}

		String dbLimits = context.getInitParameter (CtxDbLimits);
		if (dbLimits != null && dbLimits.trim ().length () > 0)
		{
			/*
			 * Tokens are whitespace separated items of dbname:limit
			 */
			String tokens[] = dbLimits.trim ().split ("\\s+");
			for (String token : tokens)
			{
				String e[] = token.split (":");
				ThrottleCounter counter = new ThrottleCounter (e[0], Integer.parseInt (e[1]));
				_dbCounters.put (e[0], counter);
				_logger.info ("configured db-limit=" + counter);
			}
		}
	}

	public boolean allowRun (
		DbParams dbParams)
	{
		if (_maxActive > 0 && _active >= _maxActive)
		{
			_logger.warn ("hit global limit=" + _maxActive);
			return false;
		}

		ThrottleCounter counter = _dbCounters.get (dbParams.db);
		if (counter == null)
		{
			counter = new ThrottleCounter (dbParams.db, _defaultLimit);
			_dbCounters.put (dbParams.db, counter);
			_logger.info ("dynamic db-limit=" + counter);
		}
		if (counter.atLimit ())
		{
			_logger.info ("hit db-limit=" + counter);
			return false;
		}
		counter.inc ();

		_active++;
		_logger.debug ("active=" + _active);
		return true;
	}

	public void done (
		DbParams dbParams)
	{
		ThrottleCounter counter = _dbCounters.get (dbParams.db);
		counter.dec ();

		_active--;
		_logger.debug ("active=" + _active);
	}
}
