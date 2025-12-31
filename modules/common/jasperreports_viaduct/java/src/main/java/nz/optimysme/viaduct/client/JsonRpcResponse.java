package nz.optimysme.viaduct.client;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.Serializable;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import nz.optimysme.viaduct.ViaductException;
import nz.optimysme.viaduct.server.ServerSession;
import nz.optimysme.viaduct.server.dbimage.SessionImageBuilder;
import nz.optimysme.viaduct.server.dbimage.ViaductSessionImage;

/**
 * JSON-RPC Request 2.0, customised for Odoo.
 */
public class JsonRpcResponse
	implements Serializable
{
	private static final Logger _logger = LogManager.getLogger (JsonRpcResponse.class);

	//@formatter:off
	private static final String
		DateMarker = "date",
		DatetimeMarker = "datetime",
		ImageMarker = "image";
	//@formatter:on

	/*
	 * Instance.
	 */
	private final ZoneId _zone;

	public String jsonrpc;
	public String id;
	public JsonError error;
	public Map<String, ReportHelperValue> result;

	public JsonRpcResponse ()
	{
		_zone = ZoneId.systemDefault ();
	}

	/**
	 * Inspect the result and re-convert values to expected types if required.
	 *
	 * @return map of final results with expected types.
	 */
	public Map<String, ReportHelperValue> normalise (
		ServerSession session,
		Connection conx)
	{
		HashMap<String, ReportHelperValue> converted = new HashMap<> ();
		if (result == null)
			return converted;

		for (Map.Entry<String, ReportHelperValue> entry : result.entrySet ())
		{
			String type = entry.getValue ().type;

			if (type.equals (DateMarker))
			{
				converted.put (entry.getKey (), parseDate (entry.getValue ()));

			} else if (type.equals (DatetimeMarker))
			{
				converted.put (entry.getKey (), parseDatetime (entry.getValue ()));

			} else if (type.equals (ImageMarker))
			{
				converted.put (entry.getKey (), storeImageFile (session.workDir, conx, entry.getValue ()));

			} else
			{
				converted.put (entry.getKey (), entry.getValue ());
			}
		}
		return converted;
	}

	private ReportHelperValue parseDate (
		ReportHelperValue raw)
	{
		ReportHelperValue result = new ReportHelperValue ();
		result.type = raw.type;

		String dateStr = raw.value.toString ();
		try
		{
			result.value = new SimpleDateFormat ("yyyy-MM-dd").parse (dateStr);

		} catch (ParseException e)
		{
			_logger.error ("Bad date=" + dateStr.toString (), e);
			result.value = new Date ();
		}
		return result;
	}

	/**
	 * <p>
	 * DateTime values are serialised using seconds since Epoch. These need to
	 * adjusted to Viaduct's local timezone so that they are displayed correctly
	 * in reports.
	 * </p>
	 * <p>
	 * Timestamp values are of the form ${epochMilli}:${tz}.
	 * </p>
	 *
	 * @param raw
	 *        original value.
	 * @return millis since Epoch.
	 */
	private ReportHelperValue parseDatetime (
		ReportHelperValue raw)
	{
		ReportHelperValue result = new ReportHelperValue ();
		result.type = raw.type;

		String segs[] = raw.value.toString ().split (":");
		long epochMilli = Long.parseLong (segs[0]) * 1000;
		if (segs.length == 1)
		{
			result.value = new Timestamp (epochMilli);
			return result;
		}
		ZoneId zone = ZoneId.of (segs[1]);
		if (zone.equals (_zone))
		{
			result.value = new Timestamp (epochMilli);
			return result;
		}

		Instant instant = Instant.ofEpochMilli (epochMilli);
		ZonedDateTime zonedTime = ZonedDateTime.ofInstant (instant, _zone);
		int zoneOffset = zonedTime.getOffset ().getTotalSeconds ();

		ZonedDateTime local = ZonedDateTime.ofInstant (instant, zone);
		int offset = local.getOffset ().getTotalSeconds () - zoneOffset;

		result.value = new Timestamp (epochMilli + offset * 1000);
		return result;
	}

	private ReportHelperValue storeImageFile (
		File workDir,
		Connection conx,
		ReportHelperValue raw)
	{
		ReportHelperValue result = new ReportHelperValue ();
		result.type = raw.type;

		try
		{
			SessionImageBuilder builder = new SessionImageBuilder (conx);
			ViaductSessionImage sessionImage = builder.read ((int) raw.value);

			File image = new File (workDir, sessionImage.name);
			if (!image.exists ())
			{
				writeFile (image, sessionImage.content);
				_logger.debug ("created helper-image=" + image.getName ());
			}
			result.value = image.getAbsolutePath ();

		} catch (IOException | SQLException | ViaductException e)
		{
			_logger.error (e.getMessage (), e);
		}
		return result;
	}

	private static void writeFile (
		File file,
		byte content[])
		throws IOException
	{
		FileOutputStream output = new FileOutputStream (file);
		if (content != null)
			output.write (content);
		output.close ();
	}

	public static class JsonError
	{
		public int code;
		public String message;
		public Map<String, Object> data;

		@Override
		public String toString ()
		{
			return String.format ("%s\n%s", message, data.get ("debug"));
		}
	}
}
