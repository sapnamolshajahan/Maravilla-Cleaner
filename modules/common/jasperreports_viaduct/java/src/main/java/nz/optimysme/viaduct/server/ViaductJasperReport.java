package nz.optimysme.viaduct.server;

import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.lang.management.ManagementFactory;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Map;
import java.util.Properties;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.context.ServletContextAware;

import nz.optimysme.viaduct.Viaduct;
import nz.optimysme.viaduct.server.dbcompiler.DbReportCompiler;

import jakarta.servlet.ServletContext;
import net.sf.jasperreports.engine.JRException;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.export.JRCsvExporter;
import net.sf.jasperreports.engine.export.oasis.JROdtExporter;
import net.sf.jasperreports.engine.export.ooxml.JRDocxExporter;
import net.sf.jasperreports.export.SimpleDocxReportConfiguration;
import net.sf.jasperreports.export.SimpleExporterInput;
import net.sf.jasperreports.export.SimpleOdtReportConfiguration;
import net.sf.jasperreports.export.SimpleOutputStreamExporterOutput;
import net.sf.jasperreports.export.SimpleWriterExporterOutput;

/**
 * Report engine.
 */
@Service
public class ViaductJasperReport
	implements ServletContextAware
{
	private static final Logger _logger = LogManager.getLogger (ViaductJasperReport.class);

	//@formatter:off
	private static final String
		FormatCsv = "csv",
		FormatDocX = "docx",
		FormatOdt = "odt",
		FormatPdf = "pdf";
	//@formatter:on

	static
	{
		try
		{
			Class.forName ("org.postgresql.Driver");

		} catch (ClassNotFoundException e)
		{
			_logger.fatal ("failed to load PostgreSQL", e);
		}
	}

	//@formatter:off
	private static final String
		PViaduct = "viaduct",
		PViaductDirectory = "viaduct-directory",

		/* JasperReports Internal Parameters */
		JIgnorePagination = "IS_IGNORE_PAGINATION";
	//@formatter:on

	/*
	 * Instance
	 */
	private String _workBase;
	@Autowired
	private Throttler _throttler;

	/**
	 * Sole Constructor.
	 */
	public ViaductJasperReport ()
	{
		_workBase = "/tmp/viaduct";
	}

	@Override
	public void setServletContext (
		ServletContext context)
	{
		_workBase = String.format ("/tmp%s-%s", context.getContextPath (),
			ManagementFactory.getRuntimeMXBean ().getName ());
		_logger.debug ("workbase=" + _workBase);
	}

	/**
	 * Generate the report, subject to throttling restrictions.
	 *
	 * @param request
	 *        request parameters.
	 * @return report in desired output format.
	 */
	public ViaductResult generate (
		ReportRequest request)
	{
		synchronized (_throttler)
		{
			try
			{
				while (!_throttler.allowRun (request.dbParams))
				{
					_logger.debug ("throttled wait");
					_throttler.wait ();
					_logger.debug ("throttled revived");
				}
			} catch (InterruptedException e)
			{
				ViaductResult error = new ViaductResult ();
				error.status = e.getMessage ();
				return error;
			}
		}

		ViaductResult result = generateActual (request);

		synchronized (_throttler)
		{
			_throttler.done (request.dbParams);
			_throttler.notify ();
		}

		return result;
	}

	private ViaductResult generateActual (
		ReportRequest request)
	{
		_logger.debug ("request=" + request);

		ServerSession session = new ServerSession (_workBase, request);
		Viaduct viaduct = null;
		ViaductResult result = new ViaductResult ();
		result.status = "incomplete";
		try
		{

			JasperPrint jasperPrint;
			try (Connection conx = connect (request.dbParams);
				DbReportCompiler compiler = new DbReportCompiler (session, conx))
			{
				viaduct = new Viaduct (session, request.odooParams, conx);
				JasperReport report = compiler.compile ();

				request.reportParams.put (PViaduct, viaduct);
				request.reportParams.put (PViaductDirectory, session.workDir.getAbsolutePath ());
				logParameters (request.reportParams);

				viaduct.connect ();
				jasperPrint = JasperFillManager.fillReport (report, request.reportParams, conx);
			}

			ByteArrayOutputStream output = new ByteArrayOutputStream ();
			switch (request.format)
			{
			case FormatCsv:
				_logger.debug ("generating csv output");
				exportToCsv (jasperPrint, output);
				break;

			case FormatDocX:
				_logger.debug ("generating docx output");
				exportToDocX (jasperPrint, output);
				break;

			case FormatOdt:
				_logger.debug ("generating odt output");
				exportToOdt (jasperPrint, output);
				break;

			default:
				_logger.warn ("Unknown output-format=" + request.format + ", using pdf");

			case FormatPdf:
				_logger.debug ("generating pdf output");
				JasperExportManager.exportReportToPdfStream (jasperPrint, output);
				break;
			}

			result.status = "completed";
			result.setOutput (output.toByteArray ());

		} catch (Exception e)
		{
			_logger.error (e.getMessage (), e);
			result.status = e.getMessage ();

			if (viaduct != null)
			{
				String remoteError = viaduct.getLastRemoteError ();
				if (remoteError != null)
					result.status += "\n" + remoteError;
			}
		}
		return result;
	}

	private void logParameters (
		Map<String, Object> parameters)
	{
		if (!_logger.isDebugEnabled ())
			return;

		for (String key : parameters.keySet ())
		{
			Object value = parameters.get (key);
			if (value instanceof Object[])
			{
				StringBuffer debug = new StringBuffer ("parameter: " + key + "=[");
				boolean first = true;
				for (Object o : (Object[]) value)
				{
					if (first)
						first = false;
					else
						debug.append (", ");
					debug.append (o);
				}
				debug.append ("]");
				_logger.debug (debug);

			} else
			{
				_logger.debug ("parameter: " + key + "=" + parameters.get (key));
			}
		}
	}

	private static void exportToCsv (
		JasperPrint jasperPrint,
		OutputStream os)
		throws JRException
	{
		JRCsvExporter exporter = new JRCsvExporter ();
		exporter.setExporterInput (new SimpleExporterInput (jasperPrint));
		exporter.setExporterOutput (new SimpleWriterExporterOutput (os));
		exporter.exportReport ();
	}

	private static void exportToDocX (
		JasperPrint jasperPrint,
		OutputStream os)
		throws JRException
	{
		SimpleDocxReportConfiguration configuration = new SimpleDocxReportConfiguration ();
		configuration.setIgnoreHyperlink (true);

		JRDocxExporter exporter = new JRDocxExporter ();
		exporter.setExporterInput (new SimpleExporterInput (jasperPrint));
		exporter.setExporterOutput (new SimpleOutputStreamExporterOutput (os));
		exporter.setConfiguration (configuration);
		exporter.exportReport ();
	}

	private static void exportToOdt (
		JasperPrint jasperPrint,
		OutputStream os)
		throws JRException
	{
		SimpleOdtReportConfiguration configuration = new SimpleOdtReportConfiguration ();
		configuration.setIgnoreHyperlink (true);

		JROdtExporter exporter = new JROdtExporter ();
		exporter.setExporterInput (new SimpleExporterInput (jasperPrint));
		exporter.setExporterOutput (new SimpleOutputStreamExporterOutput (os));
		exporter.setConfiguration (configuration);
		exporter.exportReport ();
	}

	private Connection connect (
		DbParams dbParams)
		throws SQLException
	{
		String url = String.format ("jdbc:postgresql://%s:%s/%s", dbParams.host, dbParams.port, dbParams.db);

		Properties props = new Properties ();
		props.setProperty ("user", dbParams.login);
		props.setProperty ("password", dbParams.password);
		_logger.info (String.format ("database user=%s, url=%s", dbParams.login, url));
		return DriverManager.getConnection (url, props);
	}
}
