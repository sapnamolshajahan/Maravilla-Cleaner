package nz.optimysme.viaduct.server;

import java.util.Map;

/**
 * Incoming report request data.
 */
public class ReportRequest
{
	public String format;
	public DbParams dbParams;
	public OdooParams odooParams;
	public Map<String, Object> reportParams;

	@Override
	public String toString ()
	{
		return String.format ("{session=%d, format=%s}", odooParams.session, format);
	}
}
