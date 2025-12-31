package nz.optimysme.viaduct.client;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.sql.Connection;
import java.util.HashMap;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.fasterxml.jackson.databind.ObjectMapper;

import nz.optimysme.viaduct.ViaductException;
import nz.optimysme.viaduct.server.ServerSession;

/**
 * Home grown JSON-RPC client.
 */
public class JsonRpcClient
{
	private static final Logger _Logger = LogManager.getLogger (JsonRpcClient.class);

	private final URL _url;
	private final ObjectMapper _mapper;
	private String _lastRemoteError;

	public JsonRpcClient (
		String url)
		throws MalformedURLException
	{
		_url = new URL (url);
		_mapper = new ObjectMapper ();
		_lastRemoteError = null;
	}

	public ReportHelperData getData (
		Connection conx,
		ServerSession session,
		String method,
		int id,
		Object[] args)
		throws ViaductException
	{
		try
		{
			HashMap<String, Object> params = new HashMap<> ();
			params.put ("session", session.id);
			params.put ("method", method);
			params.put ("identifier", id);
			params.put ("arguments", args);

			JsonRpcRequest request = new JsonRpcRequest ();
			request.id = Integer.toString (session.id);
			request.method = method; // unused by Odoo
			request.params = params;

			HttpURLConnection connect = (HttpURLConnection) _url.openConnection ();
			connect.addRequestProperty ("Content-Type", "application/json");
			connect.setRequestMethod ("POST");
			connect.setDoOutput (true);
			OutputStream os = connect.getOutputStream ();
			_mapper.writeValue (os, request);
			os.close ();

			JsonRpcResponse response = _mapper.readValue (connect.getInputStream (), JsonRpcResponse.class);
			if (response.error == null)
			{
				ReportHelperData data = new ReportHelperData (method, new ReportHelperDataKey (id, args));
				data.populate (response.normalise (session, conx));
				return data;
			}
			_lastRemoteError = response.error.toString ();

			_Logger.error ("json-error=" + response.error);
			throw new ViaductException ("Server internal error");

		} catch (ViaductException e)
		{
			throw e;

		} catch (Exception e)
		{
			throw new ViaductException ("unknown server error, check server logs", e);
		}
	}

	public String getLastRemoteError ()
	{
		return _lastRemoteError;
	}

	@Override
	public String toString ()
	{
		return String.format ("{url=%s}", _url);
	}
}
