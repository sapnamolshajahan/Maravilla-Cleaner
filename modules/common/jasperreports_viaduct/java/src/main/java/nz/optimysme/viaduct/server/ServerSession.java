package nz.optimysme.viaduct.server;

import java.io.File;

/**
 * A Report Session on the Server Side.
 */
public class ServerSession
{
	/*
	 * Instance.
	 */
	public final int id;
	public final File workDir;

	/**
	 * Default Contructor; build up locations and other useful stuff.
	 */
	public ServerSession (
		String workBase,
		ReportRequest request)
	{
		id = request.odooParams.session;
		workDir = new File (String.format ("%s/%s/%d", workBase, request.dbParams.db, request.odooParams.session));
	}

	@Override
	public String toString ()
	{
		return String.format ("{id=%d, workdir=%s}", id, workDir);
	}
}
