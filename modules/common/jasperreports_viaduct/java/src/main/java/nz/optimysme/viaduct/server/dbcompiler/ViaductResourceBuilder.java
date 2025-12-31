package nz.optimysme.viaduct.server.dbcompiler;

import java.io.InputStream;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import nz.optimysme.viaduct.ViaductException;

/**
 * Operate on ViaductResource records as required.
 */
public class ViaductResourceBuilder
{
	private final Connection _conx;

	/**
	 * Constructor
	 */
	public ViaductResourceBuilder (
		Connection conx)
	{
		_conx = conx;
	}

	private ViaductResource extract (
		ResultSet rs)
		throws SQLException
	{
		ViaductResource result = new ViaductResource ();
		result.id = rs.getInt ("id");
		result.name = rs.getString ("name");
		result.directory = rs.getString ("directory");
		result.jrxml = rs.getString ("jrxml");
		result.content = rs.getBytes ("content");
		return result;
	}

	/**
	 * Read a single record from the supplied session id.
	 *
	 * @param sessionId
	 *        session id.
	 * @return populated record.
	 * @throws SQLException
	 * @throws ViaductException
	 */
	public ViaductResource read (
		int sessionId)
		throws SQLException, ViaductException
	{
		try (PreparedStatement st = _conx.prepareStatement ("""
			select viaduct_resource.id, name, directory, jrxml, content
			from viaduct_session, viaduct_resource
			where viaduct_session.id = ?
			and viaduct_resource.id = viaduct_report"""))
		{
			st.setInt (1, sessionId);
			ResultSet rs = st.executeQuery ();
			while (rs.next ())
				return extract (rs);
		}
		throw new ViaductException (String.format ("Expected viaduct.session=%d not found", sessionId));
	}

	/**
	 * @param directory
	 * @return list of ViaductReports with given directory.
	 */
	public List<ViaductResource> readDir (
		String directory)
		throws SQLException
	{
		ArrayList<ViaductResource> result = new ArrayList<> ();
		try (PreparedStatement st = _conx.prepareStatement ("""
			select id, name, directory, jrxml, content
			from viaduct_resource
			where directory = ?"""))
		{
			st.setString (1, directory);
			ResultSet rs = st.executeQuery ();
			while (rs.next ())
				result.add (extract (rs));
		}
		return result;
	}

	/**
	 * Store the compiled jasper report.
	 *
	 * @param id
	 * @param is
	 * @throws SQLException
	 */
	public void storeContent (
		int id,
		InputStream is)
		throws SQLException
	{
		try (PreparedStatement st = _conx.prepareStatement ("""
			update viaduct_resource set
			  content = ?
			where id = ?"""))
		{
			st.setBinaryStream (1, is);
			st.setInt (2, id);
			st.executeUpdate ();
		}
	}
}
