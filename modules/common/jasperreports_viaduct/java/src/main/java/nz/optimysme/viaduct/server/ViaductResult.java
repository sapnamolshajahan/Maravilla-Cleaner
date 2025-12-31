package nz.optimysme.viaduct.server;

import java.util.Base64;

public class ViaductResult
{
	public String status;
	public String output;

	public ViaductResult ()
	{
		status = null;
		output = null;
	}

	public ViaductResult setOutput (
		byte bytes[])
	{
		output = Base64.getEncoder ().encodeToString (bytes);
		return this;
	}
}
