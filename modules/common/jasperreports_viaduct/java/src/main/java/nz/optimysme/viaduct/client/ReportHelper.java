package nz.optimysme.viaduct.client;

import java.util.ArrayDeque;
import java.util.HashMap;

/**
 * Essential features of the remote JasperHelper.
 */
public class ReportHelper
{
	private static final int MaxCacheSize = 10;

	/*
	 * Instance.
	 */
	private final HashMap<String, ArrayDeque<ReportHelperData>> _dataCache;
	public final int name;

	public ReportHelper (
		int name)
	{
		this.name = name;
		_dataCache = new HashMap<> ();
	}

	/**
	 * See if we've cached a data-entry.
	 *
	 * @param id
	 * @return
	 */
	public ReportHelperData getData (
		String method,
		int id,
		Object args[])
	{
		ArrayDeque<ReportHelperData> bucket = _dataCache.get (method);
		if (bucket != null)
		{
			for (ReportHelperData data : bucket)
			{
				if (data.key.equals (id, args))
					return data;
			}
		}
		return null;
	}

	public ReportHelperData addData (
		ReportHelperData data)
	{
		ArrayDeque<ReportHelperData> bucket = _dataCache.get (data.method);
		if (bucket == null)
		{
			bucket = new ArrayDeque<> ();
			_dataCache.put (data.method, bucket);
		}
		bucket.addFirst (data);
		while (bucket.size () > MaxCacheSize)
			bucket.removeLast ();
		return data;
	}
}
