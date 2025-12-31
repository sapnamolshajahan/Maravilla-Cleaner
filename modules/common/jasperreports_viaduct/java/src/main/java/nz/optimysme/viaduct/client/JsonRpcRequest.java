package nz.optimysme.viaduct.client;

import java.io.Serializable;
import java.util.Map;

/**
 * JSON-RPC Request 2.0
 */
public class JsonRpcRequest
	implements Serializable
{
	public final String jsonrpc;
	public String method, id;
	public Map<String, Object> params;

	public JsonRpcRequest ()
	{
		jsonrpc = "2.0";
	}
}
