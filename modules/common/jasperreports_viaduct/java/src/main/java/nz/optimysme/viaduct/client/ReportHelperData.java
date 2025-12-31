package nz.optimysme.viaduct.client;

import java.util.HashMap;
import java.util.Map;

/**
 * Wrapped Container for result of a call to the remote ViaductHelper.
 */
public class ReportHelperData
{
	public final String method;
	public final ReportHelperDataKey key;
	private final HashMap<String, ReportHelperValue> _values;

	public ReportHelperData (
		String method,
		ReportHelperDataKey key)
	{
		this.method = method;
		this.key = key;
		_values = new HashMap<> ();
	}

	public void populate (
		Map<String, ReportHelperValue> source)
	{
		_values.putAll (source);
	}

	public Object get (
		String name)
	{
		return _values.get (name).value;
	}
}
