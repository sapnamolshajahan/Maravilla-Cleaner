package nz.optimysme.viaduct;

import java.net.MalformedURLException;
import java.sql.Connection;

import nz.optimysme.viaduct.client.ClientSession;
import nz.optimysme.viaduct.client.ReportHelperData;
import nz.optimysme.viaduct.server.OdooParams;
import nz.optimysme.viaduct.server.ServerSession;

/**
 * Proxy object used within a Jasper Report to access the Odoo server.
 */
public class Viaduct
{
	/*
	 * Instance.
	 */
	private final ClientSession _clientSession;

	/**
	 * Sole Constructor.
	 *
	 * @throws MalformedURLException
	 */
	public Viaduct (
		ServerSession serverSession,
		OdooParams odooParams,
		Connection conx)
		throws MalformedURLException
	{
		_clientSession = new ClientSession (odooParams.url, serverSession, conx);
	}

	/**
	 * Connect to the Odoo server.
	 *
	 * @param conx
	 *        usable database connection to report source.
	 */
	public void connect ()
	{
		_clientSession.connect ();
	}

	/**
	 * Get a value from the remote Jasperreport helper.
	 *
	 * @throws ViaductException
	 */
	public ReportHelperData helper (
		String method,
		int id,
		Object... args)
		throws ViaductException
	{
		return _clientSession.getHelperData (method, id, args);
	}

	public String getLastRemoteError ()
	{
		return _clientSession.getLastRemoteError ();
	}

	@Override
	public String toString ()
	{
		return String.format ("{client-session=%s}", _clientSession);
	}
}
