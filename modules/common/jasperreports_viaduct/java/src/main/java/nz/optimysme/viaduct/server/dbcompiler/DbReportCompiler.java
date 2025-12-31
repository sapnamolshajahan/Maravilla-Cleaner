package nz.optimysme.viaduct.server.dbcompiler;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.sql.Connection;
import java.sql.SQLException;

import org.apache.commons.io.FileUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import nz.optimysme.viaduct.ViaductException;
import nz.optimysme.viaduct.server.ServerSession;

import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.util.JRLoader;

/**
 * Compiles all reports, and possible sub-reports; using the database as source
 * and output repository.
 */
public class DbReportCompiler
	implements AutoCloseable
{
	private static final Logger _Logger = LogManager.getLogger (DbReportCompiler.class);

	/**
	 * Instance.
	 */
	private final ViaductResourceBuilder _builder;
	private final ViaductResource _target;
	private final File _jasperDir;

	/**
	 * Default Constructor.
	 *
	 * @throws ViaductException
	 */
	public DbReportCompiler (
		ServerSession session,
		Connection conx)
		throws SQLException, ViaductException
	{
		_builder = new ViaductResourceBuilder (conx);
		_target = _builder.read (session.id);
		_jasperDir = session.workDir;
		_jasperDir.mkdirs ();

		_Logger.info ("target=" + _target.name);
	}

	@Override
	public void close ()
		throws Exception
	{
		FileUtils.deleteDirectory (_jasperDir);
	}

	private static void writeFile (
		File file,
		byte content[])
		throws IOException
	{
		FileOutputStream output = new FileOutputStream (file);
		output.write (content);
		output.close ();
	}

	/**
	 * Extract the source and compiled results, if any.
	 *
	 * @param rec
	 * @throws IOException
	 * @throws JRException
	 * @throws SQLException
	 */
	private File compile (
		ViaductResource rec)
		throws IOException, JRException, SQLException
	{
		File jrxml = new File (_jasperDir, rec.name);
		writeFile (jrxml, rec.jrxml.getBytes ());

		String jasperName = rec.name.substring (0, rec.name.lastIndexOf ('.')) + ".jasper";
		File jasper = new File (_jasperDir, jasperName);
		if (rec.content != null)
		{
			writeFile (jasper, rec.content);
			_Logger.debug ("restored=" + jasper.getName ());

		} else
		{
			_Logger.info ("compile=" + jrxml.getName () + " => " + jasper.getName ());
			JasperCompileManager.compileReportToFile (jrxml.getAbsolutePath (), jasper.getAbsolutePath ());

			try (FileInputStream is = new FileInputStream (jasper))
			{
				_builder.storeContent (rec.id, is);
			}
		}
		return jasper;
	}

	public JasperReport compile ()
		throws JRException, IOException, SQLException
	{
		try
		{
			File targetOutput = null;
			for (ViaductResource rec : _builder.readDir (_target.directory))
			{
				if (rec.jrxml == null)
				{
					File resource = new File (_jasperDir, rec.name);
					writeFile (resource, rec.content);
					_Logger.debug ("resource=" + resource.getName ());

				} else
				{
					File output = compile (rec);
					if (_target.id == rec.id)
						targetOutput = output;
				}
			}
			return (JasperReport) JRLoader.loadObject (targetOutput);

		} catch (JRException | IOException | SQLException e)
		{
			_Logger.error ("compilation failed", e);
			throw e;
		}
	}
}
