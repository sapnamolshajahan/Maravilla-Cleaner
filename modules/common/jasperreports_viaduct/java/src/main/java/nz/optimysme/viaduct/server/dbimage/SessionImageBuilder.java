package nz.optimysme.viaduct.server.dbimage;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import nz.optimysme.viaduct.ViaductException;

/**
 * Operate on ViaductSessionImage records as required.
 */
public class SessionImageBuilder
{
	private final Connection _conx;

	/**
	 * Constructor
	 */
	public SessionImageBuilder (
		Connection conx)
	{
		_conx = conx;
	}

	private ViaductSessionImage extract (
		ResultSet rs)
		throws SQLException
	{
		ViaductSessionImage result = new ViaductSessionImage ();
		result.id = rs.getInt ("id");
		result.name = rs.getString ("name");
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
	public ViaductSessionImage read (
		int imageId)
		throws SQLException, ViaductException
	{
		try (PreparedStatement st = _conx.prepareStatement ("""
			select id, name, content
			from viaduct_session_image
			where id = ?"""))
		{
			st.setInt (1, imageId);
			ResultSet rs = st.executeQuery ();
			while (rs.next ())
				return extract (rs);
		}
		throw new ViaductException (String.format ("Expected viaduct.session.image=%d not found", imageId));
	}
}
