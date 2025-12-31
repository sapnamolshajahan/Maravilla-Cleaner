package nz.optimysme.viaduct.client;

import java.net.MalformedURLException;
import java.sql.Connection;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import nz.optimysme.viaduct.ViaductException;
import nz.optimysme.viaduct.server.ServerSession;

public class ClientSession
{
	private static final Logger _logger = LogManager.getLogger (ClientSession.class);

	/*
	 * Instance
	 */
	private final ServerSession _serverSession;
	private final ReportHelper _helper;
	private final JsonRpcClient _reportClient;
	private final Connection _conx;

	public ClientSession (
		String url,
		ServerSession serverSession,
		Connection conx)
		throws MalformedURLException
	{
		_serverSession = serverSession;
		_helper = new ReportHelper (_serverSession.id);
		_reportClient = new JsonRpcClient (url);
		_conx = conx;
	}

	public void connect ()
	{
	}

	public ReportHelperData getHelperData (
		String method,
		int id,
		Object... args)
		throws ViaductException
	{
		ReportHelperData data = _helper.getData (method, id, args);
		if (data != null)
			return data;
		_logger.debug (String.format ("client-call method=%s, id=%d", method, id));
		return _helper.addData (_reportClient.getData (_conx, _serverSession, method, id, args));
	}

	public String getLastRemoteError ()
	{
		return _reportClient.getLastRemoteError ();
	}

	@Override
	public String toString ()
	{
		return String.format ("{rpc=%s, server-session=%s}", _reportClient, _serverSession);
	}
}
